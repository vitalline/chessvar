from copy import copy
from itertools import product, zip_longest
from math import ceil, sqrt
from random import choice, randrange
from typing import Type

from PIL.ImageColor import getrgb
from arcade import key, MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT, Text
from arcade import Sprite, SpriteList, Window
from arcade import start_render

from chess.color import colors, trickster_colors
from chess.color import average, darken, desaturate, lighten, saturate
from chess.movement import movement
from chess.movement.move import Move
from chess.movement.util import Position, add
from chess.pieces import pieces as abc
from chess.pieces.groups import classic as fide
from chess.pieces.groups import avian as av, bent as bt, colorbound as cb
from chess.pieces.groups import cylindrical as cy, dragon as dr, fizzies as fi
from chess.pieces.groups import forward as fw, knights as kn, mash as ms
from chess.pieces.groups import pizza as pz, rookies as rk, slide as sl
from chess.pieces.groups import switch as sw
from chess.pieces.groups.amazon import Amazon
from chess.pieces.groups.util import NoPiece
from chess.pieces.pieces import Side

piece_groups = {
    1: [fide.Rook, fide.Knight, fide.Bishop, fide.Queen, fide.King, fide.Bishop, fide.Knight, fide.Rook],
    2: [cb.Bede, cb.Waffle, cb.FAD, cb.Cardinal, cb.King, cb.FAD, cb.Waffle, cb.Bede],
    3: [rk.ShortRook, rk.WoodyRook, rk.HalfDuck, rk.Chancellor, fide.King, rk.HalfDuck, rk.WoodyRook, rk.ShortRook],
    4: [kn.ChargeRook, kn.Fibnif, kn.ChargeKnight, kn.Colonel, fide.King, kn.ChargeKnight, kn.Fibnif, kn.ChargeRook],
    5: [kn.ChargeRook, fw.Knishop, fw.Bishight, fw.Forequeen, fide.King, fw.Bishight, fw.Knishop, kn.ChargeRook],
    6: [kn.ChargeRook, cb.Waffle, fide.Bishop, rk.Chancellor, fide.King, fide.Bishop, cb.Waffle, kn.ChargeRook],
    7: [kn.ChargeRook, kn.Fibnif, fw.Bishight, rk.Chancellor, fide.King, fw.Bishight, kn.Fibnif, kn.ChargeRook],
    8: [cb.Bede, cb.FAD, cb.Waffle, cb.Cardinal, cb.King, cb.Waffle, cb.FAD, cb.Bede],
    9: [rk.ShortRook, fide.Knight, fide.Bishop, Amazon, fide.King, fide.Bishop, fide.Knight, rk.ShortRook],
    10: [cy.CyWaffle, cy.CyKnight, cy.CyBishop, cy.CyChancellor, fide.King, cy.CyBishop, cy.CyKnight, cy.CyWaffle],
    11: [fi.LRhino, fi.Gnohmon, fi.Crabinal, fi.EagleScout, fide.King, fi.Crabinal, fi.Gnohmon, fi.RRhino],
    12: [av.Wader, av.Darter, av.Faalcon, av.Kingfisher, fide.King, av.Faalcon, av.Darter, av.Wader],
    13: [pz.Pepperoni, pz.Mushroom, pz.Sausage, pz.Meatball, fide.King, pz.Sausage, pz.Mushroom, pz.Pepperoni],
    14: [ms.Forfer, kn.Fibnif, ms.B4nD, ms.N2R4, fide.King, ms.B4nD, kn.Fibnif, ms.Forfer],
    15: [dr.DragonHorse, dr.Dragonfly, dr.Dragoon, dr.Wyvern, fide.King, dr.Dragoon, dr.Dragonfly, dr.DragonHorse],
    16: [sw.Panda, sw.Marquis, sw.Unicorn, sw.ErlQueen, fide.King, sw.Unicorn, sw.Marquis, sw.Panda],
    17: [bt.LGriffon, bt.LAanca, bt.LSastik, bt.Griffon, fide.King, bt.RSastik, bt.RAanca, bt.RGriffon],
    18: [sl.LameDuck, sl.Diamond, sl.Onyx, sl.Squire, fide.King, sl.Onyx, sl.Diamond, sl.LameDuck],
}

piece_group_names = {
    1: "Fabulous FIDEs",
    2: "Colorbound Clobberers",
    3: "Remarkable Rookies",
    4: "Nutty Knights",
    5: "Forward FIDEs",
    6: "All-Around Allstars",
    7: "All-Around Allstars 2",
    8: "Colorbound Clobberers 2",
    9: "Amazon Army",
    10: "Cylindrical Cinders",
    11: "Fighting Fizzies",
    12: "Avian Airforce",
    13: "Pizza Kings",
    14: "Meticulous Mashers",
    15: "Daring Dragons",
    16: "Seeping Switchers",
    17: "Bent Bozos",
    18: "Silly Sliders",
}

board_width = 8
board_height = 8

pawn_row = [fide.Pawn] * board_width
empty_row = [NoPiece] * board_width

white_row = [Side.WHITE] * board_width
black_row = [Side.BLACK] * board_width
neutral_row = [Side.NONE] * board_width

types = [white_row, pawn_row] + [empty_row] * (board_height - 4) + [pawn_row, black_row]
sides = [white_row, white_row] + [neutral_row] * (board_height - 4) + [black_row, black_row]

white_promotion_squares = {(board_height - 1, i) for i in range(board_width)}
black_promotion_squares = {(0, i) for i in range(board_width)}
promotion_squares = {Side.WHITE: white_promotion_squares, Side.BLACK: black_promotion_squares}

default_size = 50
min_size = 25
max_size = 100
size_step = 5
highlight_alpha = 64
selection_alpha = 128

movements = []


class Board(Window):

    def __init__(self):
        # super boring initialization stuff (bluh bluh)
        self.board_width, self.board_height = board_width, board_height
        self.square_size = default_size

        super().__init__(
            width=(self.board_width + 2) * self.square_size,
            height=(self.board_height + 2) * self.square_size,
            title='Chess',
            resizable=True,
            vsync=True,
            center_window=True,
        )

        self.origin = self.width / 2, self.height / 2
        self.set_minimum_size((self.board_width + 2) * min_size, (self.board_height + 2) * min_size)

        self.color_index = 0  # index of the current color scheme
        self.color_scheme = colors[self.color_index]  # current color scheme
        self.background_color = self.color_scheme["background_color"]  # background color
        self.hovered_square = None  # square we are currently hovering over
        self.clicked_square = None  # square we clicked on
        self.selected_square = None  # square selected for moving
        self.square_was_clicked = False  # used to discern two-click moving from dragging
        self.held_buttons = 0  # mouse button that was pressed
        self.en_passant_target = None  # piece that can be captured en passant
        self.en_passant_markers = set()  # squares where it can be captured
        self.promotion_piece = None  # piece that is currently being promoted
        self.promotion_area = {}  # squares to draw possible promotions on
        self.move_history = []  # list of moves made so far
        self.future_move_history = []  # list of moves that were undone, in reverse order
        self.turn_side = Side.WHITE  # side whose turn it is
        self.check_side = Side.NONE  # side that is currently in check
        self.castling_threats = set()  # squares that are attacked in a way that prevents castling
        self.flip_mode = False  # whether the board is flipped
        self.edit_mode = False  # allows to edit the board position if set to True
        self.game_over = False  # act 6 act 6 intermission 3 (game over)
        self.trickster_color_index = 0  # hey wouldn't it be funny if there was an easter egg here
        self.trickster_color_delta = 0  # but it's not like that's ever going to happen right
        self.trickster_angle_delta = 0  # this is just a normal chess game after all
        self.pieces = []  # list of pieces on the board
        self.piece_sets = {Side.WHITE: 1, Side.BLACK: 1}  # piece sets to use for each side
        self.promotions = {Side.WHITE: [], Side.BLACK: []}  # types of pieces each side promote to
        self.edit_promotions = {Side.WHITE: [], Side.BLACK: []}  # types of pieces each side can promote to in edit mode
        self.movable_pieces = {Side.WHITE: [], Side.BLACK: []}  # pieces that can be moved by each side
        self.royal_pieces = {Side.WHITE: [], Side.BLACK: []}  # these have to stay on the board and should be protected
        self.quasi_royal_pieces = {Side.WHITE: [], Side.BLACK: []}  # at least one of these has to stay on the board
        self.moves = {}  # dictionary of valid moves from any square that has a movable piece on it
        self.theoretical_moves = {}  # dictionary of theoretical moves from any square that has an opposing piece on it
        self.anchor = 0, 0  # used to have the board scale from the origin instead of the center
        self.highlight = Sprite("assets/util/selection.png")  # sprite for the highlight marker
        self.highlight.alpha = 0
        self.highlight.scale = self.square_size / self.highlight.texture.width  # scale it to the size of a square
        self.selection = Sprite("assets/util/selection.png")  # sprite for the selection marker
        self.selection.alpha = 0
        self.selection.scale = self.square_size / self.selection.texture.width  # scale it to the size of a square
        self.active_piece = None  # piece that is currently being moved
        self.label_list = []  # labels for the rows and columns
        self.board_sprite_list = SpriteList()  # sprites for the board squares
        self.move_sprite_list = SpriteList()  # sprites for the move markers
        self.piece_sprite_list = SpriteList()  # sprites for the piece sprites
        self.promotion_area_sprite_list = SpriteList()  # sprites for the promotion area background tiles
        self.promotion_piece_sprite_list = SpriteList()  # sprites for the possible promotion pieces

        # initialize row/column labels
        label_kwargs = {
            'anchor_x': 'center',
            'anchor_y': 'center',
            'font_name': 'Courier New',
            'font_size': self.square_size / 2,
            'width': self.square_size / 2,
            'bold': True,
            'align': 'center',
            'color': self.color_scheme["text_color"],
        }

        for row in range(self.board_height):
            self.label_list.extend([
                Text(str(row + 1), *self.get_screen_position((row, -1)), **label_kwargs),
                Text(str(row + 1), *self.get_screen_position((row, board_width)), **label_kwargs)
            ])

        for col in range(self.board_width):
            self.label_list.extend([
                Text(chr(col + ord('a')), *self.get_screen_position((-1, col)), **label_kwargs),
                Text(chr(col + ord('a')), *self.get_screen_position((board_height, col)), **label_kwargs),
            ])

        # initialize board sprites
        for row, col in product(range(self.board_height), range(self.board_width)):
            sprite = Sprite("assets/util/square.png")
            sprite.color = self.color_scheme["light_square_color" if (row + col) % 2 else "dark_square_color"]
            sprite.position = self.get_screen_position((row, col))
            sprite.scale = self.square_size / sprite.texture.width
            self.board_sprite_list.append(sprite)

        # set up pieces on the board
        self.reset_board(update=True)

    def on_draw(self):
        self.update_trickster_mode()
        start_render()
        for label in self.label_list:
            label.draw()
        self.board_sprite_list.draw()
        if not self.promotion_area:
            self.highlight.draw()
            self.selection.draw()
        self.move_sprite_list.draw()
        self.piece_sprite_list.draw()
        if self.active_piece:
            self.active_piece.draw()
        self.promotion_area_sprite_list.draw()
        self.promotion_piece_sprite_list.draw()
        if self.promotion_area:
            self.highlight.draw()

    def on_update(self, delta_time: float):
        if self.trickster_color_index:
            self.trickster_color_delta += delta_time
            self.trickster_angle_delta += delta_time

    def reset_board(self, shuffle: bool = False, update: bool = False) -> None:
        self.deselect_piece()  # you know, just in case
        self.turn_side = Side.WHITE
        self.game_over = False
        self.edit_mode = False

        self.piece_sprite_list.clear()

        for sprite in self.piece_sprite_list:
            self.piece_sprite_list.remove(sprite)

        if shuffle:
            self.piece_sets = {side: choice(list(piece_groups.keys())) for side in self.piece_sets}

        print(
            f"[0] Starting new game: "
            f"{piece_group_names[self.piece_sets[Side.WHITE]]} vs "
            f"{piece_group_names[self.piece_sets[Side.BLACK]]}"
        )

        piece_sets = {side: piece_groups[self.piece_sets[side]] for side in self.piece_sets}

        if update or shuffle:
            self.future_move_history = []
            self.promotions = {side: [] for side in self.promotions}
            for side in self.promotions:
                used_piece_set = set()
                for pieces in (
                        piece_sets[side][3::-1], piece_sets[side.opponent()][3::-1],
                        piece_sets[side][5:], piece_sets[side.opponent()][5:],
                ):
                    promotion_types = []
                    for piece in pieces:
                        if piece not in used_piece_set and not issubclass(piece, abc.RoyalPiece):
                            used_piece_set.add(piece)
                            promotion_types.append(piece)
                    self.promotions[side].extend(promotion_types[::-1])
            self.edit_promotions = {side: [] for side in self.edit_promotions}
            for side in self.edit_promotions:
                used_piece_set = set()
                for pieces in (
                    piece_sets[side][3::-1], piece_sets[side.opponent()][3::-1],
                    piece_sets[side][5:], piece_sets[side.opponent()][5:],
                    [
                        piece_groups[self.piece_sets[side.opponent()]][4],
                        fide.Pawn,
                        piece_groups[self.piece_sets[side]][4],
                    ]
                ):
                    promotion_types = []
                    for piece in pieces:
                        if piece not in used_piece_set:
                            used_piece_set.add(piece)
                            promotion_types.append(piece)
                    self.edit_promotions[side].extend(promotion_types[::-1])
        else:
            self.future_move_history += self.move_history[::-1]

        self.move_history = []

        self.pieces = []

        for row in range(self.board_height):
            self.pieces += [[]]

        for row, col in product(range(self.board_height), range(self.board_width)):
            piece_type = types[row][col]
            piece_side = sides[row][col]
            if isinstance(piece_type, abc.Side):
                piece_type = piece_sets[piece_side][col]
            self.pieces[row].append(
                piece_type(
                    self, (row, col), piece_side,
                    promotions=self.promotions[piece_side],
                    promotion_squares=promotion_squares[piece_side],
                )
                if issubclass(piece_type, abc.PromotablePiece) else
                piece_type(
                    self, (row, col), piece_side
                )
            )
            self.pieces[row][col].set_color(
                self.color_scheme.get(
                    f"{self.pieces[row][col].side.file_name()}piece_color",
                    self.color_scheme["piece_color"]
                ),
                self.color_scheme["colored_pieces"]
            )
            self.pieces[row][col].scale = self.square_size / self.pieces[row][col].texture.width
            self.piece_sprite_list.append(self.pieces[row][col])

        self.load_all_moves()
        self.show_moves()

    def get_board_position(
            self,
            pos: tuple[float, float],
            size: float = 0,
            origin: tuple[float, float] | None = None,
            flip: bool | None = None
    ) -> Position:
        x, y = pos
        size = size or self.square_size
        origin = origin or self.origin
        flip = flip if flip is not None else self.flip_mode
        if flip:
            col = round((origin[0] - x) / size + (self.board_width - 1) / 2)
            row = round((origin[1] - y) / size + (self.board_height - 1) / 2)
        else:
            col = round((x - origin[0]) / size + (self.board_width - 1) / 2)
            row = round((y - origin[1]) / size + (self.board_height - 1) / 2)
        return row, col

    def get_screen_position(
            self,
            pos: tuple[float, float],
            size: float = 0,
            origin: tuple[float, float] | None = None,
            flip: bool | None = None
    ) -> tuple[float, float]:
        row, col = pos
        size = size or self.square_size
        origin = origin or self.origin
        flip = flip if flip is not None else self.flip_mode
        if flip:
            x = origin[0] - (col - (self.board_width - 1) / 2) * size
            y = origin[1] - (row - (self.board_height - 1) / 2) * size
        else:
            x = (col - (self.board_width - 1) / 2) * size + origin[0]
            y = (row - (self.board_height - 1) / 2) * size + origin[1]
        return x, y

    # From now on we shall unanimously assume that the first coordinate corresponds to row number (AKA vertical axis).

    def get_piece(self, pos: Position | None) -> abc.Piece:
        return NoPiece(self, pos, Side.NONE) if self.not_on_board(pos) else self.pieces[pos[0]][pos[1]]

    def get_side(self, pos: Position | None) -> Side:
        return self.get_piece(pos).side

    def not_on_board(self, pos: Position | None) -> bool:
        return pos is None or pos[0] < 0 or pos[0] >= self.board_height or pos[1] < 0 or pos[1] >= self.board_width

    def not_a_piece(self, pos: Position | None) -> bool:
        return self.get_piece(pos).is_empty()

    def nothing_selected(self) -> bool:
        return self.not_a_piece(self.selected_square)

    def find_move(self, pos_from: Position, pos_to: Position) -> Move | None:
        for move in self.moves.get(pos_from, ()):
            if pos_to == move.pos_to:
                return move
        return None

    def select_piece(self, pos: Position) -> None:
        if self.not_on_board(pos):
            return  # there's nothing to select off the board
        if pos == self.selected_square:
            return  # piece already selected, nothing else to do

        # set selection properties for the selected square
        self.selected_square = pos
        self.selection.alpha = selection_alpha
        self.selection.position = self.get_screen_position(pos)

        # make the piece displayed on top of everything else
        piece = self.get_piece(self.selected_square)
        self.piece_sprite_list.remove(piece)
        self.active_piece = piece

        self.show_moves()

    def show_moves(self) -> None:
        self.hide_moves()
        move_sprites = dict()
        pos = self.selected_square or self.hovered_square
        if not self.not_on_board(pos):
            theoretical = self.get_side(pos) == self.turn_side.opponent()
            move_dict = self.theoretical_moves if theoretical else self.moves
            for move in move_dict.get(pos, ()):
                if move.pos_to in move_sprites:
                    continue
                move_sprite = Sprite(f"assets/util/{'move' if self.not_a_piece(move.pos_to) else 'capture'}.png")
                move_sprite.alpha = selection_alpha if self.selected_square else highlight_alpha
                move_sprite.position = self.get_screen_position(move.pos_to)
                move_sprite.scale = self.square_size / move_sprite.texture.width
                self.move_sprite_list.append(move_sprite)
                move_sprites[move.pos_to] = move_sprite
        if not self.selected_square and self.move_history and not self.edit_mode:
            move = self.move_history[-1]
            if move is not None and not move.is_edit:
                if move.pos_from is not None and move.pos_from != move.pos_to:
                    if move.pos_from in move_sprites and not self.not_a_piece(move.pos_from):
                        move_sprites[move.pos_from].alpha = selection_alpha
                    else:
                        move_sprite = Sprite("assets/util/capture.png")
                        move_sprite.alpha = selection_alpha
                        move_sprite.position = self.get_screen_position(move.pos_from)
                        move_sprite.scale = self.square_size / move_sprite.texture.width
                        self.move_sprite_list.append(move_sprite)
                if move.pos_to is not None and not self.not_a_piece(move.pos_to):
                    if move.pos_to in move_sprites:
                        move_sprites[move.pos_to].alpha = selection_alpha
                    else:
                        move_sprite = Sprite("assets/util/selection.png")
                        move_sprite.alpha = selection_alpha
                        move_sprite.position = self.get_screen_position(move.pos_to)
                        move_sprite.scale = self.square_size / move_sprite.texture.width
                        self.move_sprite_list.append(move_sprite)

    def deselect_piece(self) -> None:
        self.selection.alpha = 0
        self.square_was_clicked = False
        self.clicked_square = None

        if self.nothing_selected():
            return

        # move the piece to general piece node
        piece, self.active_piece = self.active_piece, None
        self.reset_position(piece)
        self.piece_sprite_list.append(piece)

        self.selected_square = None
        self.show_moves()

    def hide_moves(self) -> None:
        self.move_sprite_list.clear()

    def update_highlight(self, pos: Position) -> None:
        if self.clicked_square != pos:
            self.square_was_clicked = False
            self.clicked_square = None
        if self.not_on_board(pos):
            self.highlight.alpha = 0
            self.hovered_square = None
            if (self.selected_square is None and not self.move_history) or self.promotion_piece:
                self.hide_moves()
            else:
                self.show_moves()
        else:
            self.highlight.alpha = highlight_alpha
            self.highlight.position = self.get_screen_position(pos)
            if self.hovered_square != pos:
                self.hovered_square = pos
                if self.selected_square is None and not self.promotion_piece:
                    self.show_moves()
                elif self.promotion_piece:
                    self.hide_moves()

    def on_mouse_press(self, x, y, buttons, modifiers) -> None:
        if buttons & MOUSE_BUTTON_LEFT:
            self.held_buttons = MOUSE_BUTTON_LEFT
            if self.game_over and not self.edit_mode:
                return
            pos = self.get_board_position((x, y))
            if self.promotion_piece:
                if pos in self.promotion_area:
                    self.move_history[-1].set(promotion=self.promotion_area[pos])
                    self.replace(self.promotion_piece, self.promotion_area[pos])
                    self.end_promotion()
                    print(
                        f"[{len(self.move_history)}] "
                        f"{'Edit' if self.move_history[-1].is_edit else 'Move'}: "
                        f"{self.move_history[-1]}"
                    )
                    self.advance_turn()
                return
            if pos == self.selected_square:
                self.deselect_piece()
                return
            if self.selected_square is not None:
                if self.edit_mode:
                    self.square_was_clicked = True
                    self.clicked_square = pos
                    return
                if pos not in {move.pos_to for move in self.moves.get(self.selected_square, ())}:
                    self.deselect_piece()
            if not self.not_a_piece(pos) and (self.turn_side == self.get_side(pos) or self.edit_mode):
                self.deselect_piece()  # just in case we had something previously selected
                self.select_piece(pos)
            self.square_was_clicked = True
            self.clicked_square = pos
        if buttons & MOUSE_BUTTON_RIGHT:
            self.held_buttons = MOUSE_BUTTON_RIGHT
            self.deselect_piece()
            if self.promotion_piece:
                self.undo_last_finished_move()
                return
            if self.edit_mode:
                pos = self.get_board_position((x, y))
                if self.not_on_board(pos):
                    return
                self.square_was_clicked = True
                self.clicked_square = pos

    def on_mouse_motion(self, x, y, dx, dy) -> None:
        if not self.held_buttons:
            pos = self.get_board_position((x + dx, y + dy))
            self.update_highlight(pos)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers) -> None:
        pos = self.get_board_position((x + dx, y + dy))
        self.update_highlight(pos)
        if buttons & self.held_buttons & MOUSE_BUTTON_LEFT and self.selected_square is not None:
            if self.edit_mode and modifiers & key.MOD_ACCEL:
                self.reset_position(self.get_piece(self.selected_square))
            else:
                sprite = self.get_piece(self.selected_square)
                sprite.position = x, y

    def on_mouse_release(self, x, y, buttons, modifiers) -> None:
        held_buttons = buttons & self.held_buttons
        self.held_buttons = 0
        if self.edit_mode:
            if self.promotion_piece:
                return
            pos = self.get_board_position((x, y))
            if self.not_on_board(pos):
                return
            next_selected_square = None
            move = Move(is_edit=True)
            if held_buttons & MOUSE_BUTTON_LEFT:
                if not self.selected_square:
                    return
                if pos == self.selected_square:
                    if not self.square_was_clicked:
                        self.deselect_piece()
                    self.reset_position(self.get_piece(pos))
                    return
                if modifiers & key.MOD_ACCEL:
                    self.reset_position(self.get_piece(self.selected_square))
                    piece = copy(self.get_piece(self.selected_square))
                    piece.board_pos = None
                    move.set(pos_from=None, pos_to=pos, piece=piece)
                    if not self.not_a_piece(pos):
                        move.set(captured_piece=self.get_piece(pos))
                    if self.square_was_clicked:
                        next_selected_square = pos
                elif modifiers & key.MOD_SHIFT:
                    move.set(
                        pos_from=self.selected_square, pos_to=pos,
                        piece=self.get_piece(self.selected_square)
                    )
                    if not self.not_a_piece(pos):
                        move.set(swapped_piece=self.get_piece(pos))
                else:
                    move.set(
                        pos_from=self.selected_square, pos_to=pos,
                        piece=self.get_piece(self.selected_square)
                    )
                    if not self.not_a_piece(pos):
                        move.set(captured_piece=self.get_piece(pos))
            elif held_buttons & MOUSE_BUTTON_RIGHT:
                if self.clicked_square != pos:
                    self.deselect_piece()
                    return
                if modifiers & key.MOD_ACCEL:
                    if self.not_a_piece(pos):
                        self.deselect_piece()
                        return
                    move.set(pos_from=pos, pos_to=pos, piece=self.get_piece(pos))
                elif modifiers & key.MOD_SHIFT:
                    move.set(pos_from=pos, pos_to=pos, piece=self.get_piece(pos))
                    side = self.get_side(pos)
                    if side == Side.NONE:
                        side = Side.WHITE if pos[0] < self.board_height / 2 else Side.BLACK
                        move.piece.side = side
                    if len(self.edit_promotions[side]) == 1:
                        move.set(promotion=self.edit_promotions[side][0])
                    elif len(self.edit_promotions[side]) > 1:
                        move.set(promotion=move.piece.__class__)
                        move.piece.move(move)
                        self.move_history.append(move)
                        self.start_promotion(move.piece, self.edit_promotions[side])
                        return
                else:
                    if self.not_a_piece(pos):
                        self.deselect_piece()
                        return
                    move.set(pos_from=pos, pos_to=None, piece=self.get_piece(pos))
            else:
                return
            move.piece.move(move)
            self.move_history.append(move)
            if not self.promotion_piece:
                print(f"[{len(self.move_history)}] Edit: {self.move_history[-1]}")
            self.advance_turn()
            if next_selected_square:
                self.select_piece(next_selected_square)
            return
        if held_buttons & MOUSE_BUTTON_RIGHT:
            self.deselect_piece()
            return
        if held_buttons & MOUSE_BUTTON_LEFT:
            if self.game_over:
                self.deselect_piece()
                return
            if self.promotion_piece:
                return
            if self.nothing_selected():
                return
            pos = self.get_board_position((x, y))
            if self.selected_square and pos != self.selected_square:
                move = self.find_move(self.selected_square, pos)
                if move is None:
                    self.deselect_piece()
                    return
                self.update_move(move)
                move.promotion = None  # do not auto-promote because we are selecting promotion type manually
                move.piece.move(move)
                self.move_history.append(move)
                if not self.promotion_piece:
                    print(f"[{len(self.move_history)}] Move: {self.move_history[-1]}")
                self.advance_turn()
            else:
                self.reset_position(self.get_piece(self.selected_square))
                if not self.square_was_clicked:
                    self.deselect_piece()

    def update_move(self, move: Move) -> None:
        move.set(piece=self.get_piece(move.pos_from))
        if move.pos_from != move.pos_to:
            new_piece = self.get_piece(move.pos_to)
            if new_piece.side != Side.NONE:
                if move.swapped_piece is not None:
                    move.set(swapped_piece=new_piece)
                else:
                    move.set(captured_piece=(self.en_passant_target if new_piece.is_empty() else new_piece))

    def set_position(self, piece: abc.Piece, pos: Position) -> None:
        piece.board_pos = pos
        piece.position = self.get_screen_position(pos)

    def reset_position(self, piece: abc.Piece) -> None:
        self.set_position(piece, piece.board_pos)

    def move(self, move: Move) -> None:
        self.deselect_piece()
        if move.piece is not None and move.pos_to is not None:
            self.set_position(move.piece, move.pos_to)
        if move.swapped_piece is not None:
            self.set_position(move.swapped_piece, move.pos_from)
        if move.piece is not None and move.pos_to is None:
            self.piece_sprite_list.remove(move.piece)
        if move.pos_to is not None and move.pos_from != move.pos_to:
            self.piece_sprite_list.remove(self.pieces[move.pos_to[0]][move.pos_to[1]])
            self.pieces[move.pos_to[0]][move.pos_to[1]] = move.piece
        if move.pos_from is not None and move.pos_from != move.pos_to:
            self.pieces[move.pos_from[0]][move.pos_from[1]] = (
                NoPiece(self, move.pos_from) if move.swapped_piece is None else move.swapped_piece
            )
            self.piece_sprite_list.append(self.pieces[move.pos_from[0]][move.pos_from[1]])
        if move.piece is not None and move.pos_from is None:
            self.piece_sprite_list.append(move.piece)
        if not move.is_edit or (move.pos_from == move.pos_to and move.promotion is None):
            (move.piece or move).movement.update(move, move.piece.side or self.turn_side)

    def update_board(self, move: Move) -> None:
        if self.en_passant_target is not None and move.piece.side == self.en_passant_target.side.opponent():
            if move.pos_to in self.en_passant_markers and isinstance(move.movement, movement.EnPassantMovement):
                self.capture_en_passant()
            else:
                self.clear_en_passant()

    def undo(self, move: Move) -> None:
        if move.pos_from != move.pos_to or move.promotion is not None:
            if move.pos_from is not None:
                self.set_position(move.piece, move.pos_from)
                self.piece_sprite_list.remove(self.pieces[move.pos_from[0]][move.pos_from[1]])
            if move.pos_to is not None and move.pos_from != move.pos_to:
                self.piece_sprite_list.remove(self.pieces[move.pos_to[0]][move.pos_to[1]])
            if move.pos_from is not None:
                self.pieces[move.pos_from[0]][move.pos_from[1]] = move.piece
                self.piece_sprite_list.append(move.piece)
        if move.captured_piece is not None:
            if move.captured_piece.board_pos != move.pos_to:
                self.piece_sprite_list.remove(self.pieces[move.captured_piece.board_pos[0]][move.captured_piece.board_pos[1]])
            self.reset_position(move.captured_piece)
            self.pieces[move.captured_piece.board_pos[0]][move.captured_piece.board_pos[1]] = move.captured_piece
            self.piece_sprite_list.append(move.captured_piece)
        if move.pos_to is not None and move.pos_from != move.pos_to:
            if move.captured_piece is None or move.captured_piece.board_pos != move.pos_to:
                self.pieces[move.pos_to[0]][move.pos_to[1]] = NoPiece(self, move.pos_to)
                self.piece_sprite_list.append(self.pieces[move.pos_to[0]][move.pos_to[1]])
            if move.swapped_piece is not None:
                self.set_position(move.swapped_piece, move.pos_to)
                self.piece_sprite_list.append(move.swapped_piece)
                self.pieces[move.pos_to[0]][move.pos_to[1]] = move.swapped_piece
        if not move.is_edit or (move.pos_from == move.pos_to and move.promotion is None):
            (move.piece or move).movement.undo(move, move.piece.side or self.turn_side)

    def undo_last_move(self) -> None:
        if not self.move_history:
            return
        if self.promotion_piece is not None:
            if self.move_history and self.future_move_history:
                past, future = self.move_history[-1], self.future_move_history[-1]
                if (
                    past.pos_from == future.pos_from and past.pos_to == future.pos_to
                    and ((past.captured_piece is not None) != (future.swapped_piece is not None))
                    and ((past.swapped_piece is not None) != (future.captured_piece is not None))
                    and future.promotion is not None
                ):
                    past.promotion = future.promotion
            if self.promotion_piece.board_pos in self.en_passant_markers:
                self.mark_en_passant(self.en_passant_target, self.promotion_piece.board_pos)
            self.end_promotion()
            past = self.move_history[-1]
            if not past.is_edit:
                self.turn_side = self.turn_side.opponent()
        else:
            print(f'''[{len(self.move_history)}] Undo: {
                f"{'Edit' if self.move_history[-1].is_edit else 'Move'}: " + str(self.move_history[-1])
                if self.move_history[-1] is not None else f"Pass: {self.turn_side.name()}'s turn"
            }''')
        last_move = self.move_history.pop()
        if last_move is not None:
            self.undo(last_move)
            if last_move.is_edit:
                if not self.edit_mode:
                    self.turn_side = self.turn_side.opponent()
                if (
                        last_move.piece is not None
                        and last_move.piece.is_empty()
                        and last_move.piece.board_pos not in self.en_passant_markers
                ):
                    last_move.piece.side = Side.NONE
        if self.move_history:
            move = self.move_history[-1]
            if move is not None and (not move.is_edit or (move.pos_from == move.pos_to and move.promotion is None)):
                (move.piece or move).movement.reload(move, move.piece.side or self.turn_side)
        future_move_history = self.future_move_history.copy()
        self.advance_turn()
        self.future_move_history = future_move_history
        self.future_move_history.append(last_move)

    def redo_last_move(self) -> None:
        piece_was_moved = False
        if self.promotion_piece is not None:
            if self.move_history and self.future_move_history:
                past, future = self.move_history[-1], self.future_move_history[-1]
                if (
                    past.pos_from == future.pos_from and past.pos_to == future.pos_to
                    and ((past.captured_piece is not None) != (future.swapped_piece is not None))
                    and ((past.swapped_piece is not None) != (future.captured_piece is not None))
                    and future.promotion is not None
                ):
                    past.promotion = future.promotion
                    self.replace(self.promotion_piece, future.promotion)
                    self.end_promotion()
                else:
                    return
            else:
                return
            piece_was_moved = True
        if not self.future_move_history:
            return
        last_move = copy(self.future_move_history[-1])
        if last_move is None:
            self.clear_en_passant()
        elif not piece_was_moved:
            if last_move.pos_from is not None:
                self.update_move(last_move)
                self.update_move(self.future_move_history[-1])
                side = self.get_side(last_move.pos_from)
                if side == Side.NONE:
                    side = Side.WHITE if last_move.pos_from[0] < self.board_height / 2 else Side.BLACK
                    last_move.piece.side = side
            last_move.piece.move(last_move)
            if not isinstance(last_move.piece, abc.PromotablePiece) and last_move.promotion is not None:
                self.replace(last_move.piece, last_move.promotion)
        self.move_history.append(last_move)
        # do not pop move from future history because advance_turn() will do it for us
        if last_move is not None and last_move.is_edit and not self.edit_mode:
            self.turn_side = self.turn_side.opponent()
        if self.promotion_piece is None:
            print(f'''[{len(self.move_history)}] Redo: {
                f"{'Edit' if self.move_history[-1].is_edit else 'Move'}: " + str(self.move_history[-1])
                if self.move_history[-1] is not None else f"Pass: {self.turn_side.opponent().name()}'s turn"
            }''')
        self.advance_turn()

    def undo_last_finished_move(self) -> None:
        self.undo_last_move()
        while self.move_history and self.move_history[-1] is None:
            self.undo_last_move()

    def redo_last_finished_move(self) -> None:
        while self.future_move_history and self.future_move_history[-1] is None:
            self.redo_last_move()
        self.redo_last_move()

    def start_promotion(self, piece: abc.Piece, promotions: list[Type[abc.Piece]]) -> None:
        if not self.edit_mode and not (isinstance(piece, abc.PromotablePiece) and promotions):
            return
        self.hide_moves()
        self.promotion_piece = piece
        piece_pos = piece.board_pos
        area = len(promotions)
        area_height = max(4, ceil(sqrt(area)))
        area_width = ceil(area / area_height)
        area_origin = piece_pos
        while self.not_on_board((area_origin[0] + piece.side.direction(area_height - 1), area_origin[1])):
            area_origin = add(area_origin, piece.side.direction((-1, 0)))
        area_origin = add(area_origin, piece.side.direction((area_height - 1, 0)))
        area_squares = []
        col_increment = 0
        aim_left = area_origin[1] >= board_width / 2
        for col, row in product(range(area_width), range(area_height)):
            current_row = area_origin[0] + piece.side.direction(-row)
            new_col = col + col_increment
            current_col = area_origin[1] + ((new_col + 1) // 2 * ((aim_left + new_col) % 2 * 2 - 1))
            while self.not_on_board((current_row, current_col)):
                col_increment += 1
                new_col = col + col_increment
                current_col = area_origin[1] + ((new_col + 1) // 2 * ((aim_left + new_col) % 2 * 2 - 1))
            area_squares.append((current_row, current_col))
        for promotion, pos in zip_longest(promotions, area_squares):
            background_sprite = Sprite("assets/util/square.png")
            background_sprite.color = self.color_scheme["promotion_area_color"]
            background_sprite.position = self.get_screen_position(pos)
            background_sprite.scale = self.square_size / background_sprite.texture.width
            self.promotion_area_sprite_list.append(background_sprite)
            if promotion is None:
                continue
            promotion_piece = promotion(self, pos, piece.side)
            promotion_piece.scale = self.square_size / promotion_piece.texture.width
            self.promotion_piece_sprite_list.append(promotion_piece)
            self.promotion_area[pos] = promotion

    def end_promotion(self) -> None:
        self.promotion_piece = None
        self.promotion_area = {}
        self.promotion_area_sprite_list.clear()
        self.promotion_piece_sprite_list.clear()

    def replace(
            self, piece: abc.Piece, new_type: Type[abc.Piece | abc.PromotablePiece], new_side: Side | None = None
    ) -> None:
        if new_side is None:
            new_side = piece.side
        pos = piece.board_pos
        self.piece_sprite_list.remove(piece)
        self.pieces[pos[0]][pos[1]] = new_type(
            self, pos, new_side,
            promotions=self.promotions[new_side],
            promotion_squares=promotion_squares[new_side],
        ) if issubclass(new_type, abc.PromotablePiece) else new_type(self, pos, new_side)
        self.pieces[pos[0]][pos[1]].set_color(
            self.color_scheme.get(
                f"{new_side.file_name()}piece_color",
                self.color_scheme["piece_color"]
            ),
            self.color_scheme["colored_pieces"]
        )
        self.pieces[pos[0]][pos[1]].scale = self.square_size / self.pieces[pos[0]][pos[1]].texture.width
        self.piece_sprite_list.append(self.pieces[pos[0]][pos[1]])
        self.pieces[pos[0]][pos[1]].board_pos = pos
        if pos in self.en_passant_markers and not self.not_a_piece(pos):
            self.en_passant_markers.remove(pos)

    def color_pieces(self, side: Side = Side.ANY, color: tuple[int, int, int] | None = None) -> None:
        for piece in self.movable_pieces.get(side, sum(self.movable_pieces.values(), [])):
            piece.set_color(
                color if color is not None else
                self.color_scheme.get(
                    f"{piece.side.file_name()}piece_color",
                    self.color_scheme["piece_color"]
                ),
                self.color_scheme["colored_pieces"]
            )

    def advance_turn(self) -> None:
        self.deselect_piece()
        # if we're promoting, we can't advance the turn yet
        if self.promotion_piece:
            return
        # let's also check if the last move matches the first future move
        if self.future_move_history and self.move_history:  # if there are any moves to compare that is
            if (
                    (self.move_history[-1] is None) == (self.future_move_history[-1] is None)
                    and self.future_move_history[-1] == self.move_history[-1]
            ):
                self.future_move_history.pop()  # if it does, the other future moves are still makeable, so we keep them
            else:
                self.future_move_history = []  # otherwise, we can't redo the future moves anymore, so we clear them
        self.game_over = False
        if self.edit_mode:
            self.color_pieces()  # reverting the piece colors to normal in case they were changed
            return  # let's not advance the turn while editing the board to hopefully make things easier for everyone
        self.load_check()
        pass_check_side = Side.NONE
        if self.check_side == self.turn_side:  # if the player is in check and passes the turn, the game ends
            self.game_over = True
            pass_check_side = self.check_side
        self.turn_side = self.turn_side.opponent()
        self.load_all_moves()  # this updates the check status as well
        self.show_moves()
        if not sum(self.moves.values(), []):
            self.game_over = True
        if pass_check_side != Side.NONE:
            self.check_side = pass_check_side
        if self.game_over:
            # the game has ended. let's find out who won and show it by changing piece colors... unless edit mode is on!
            if pass_check_side != Side.NONE:
                # the last player was in check and passed the turn, the game ends and the current player wins
                print(f"[{len(self.move_history)}] Game over! {pass_check_side.opponent().name()} wins.")
            elif self.check_side != Side.NONE:
                # the current player was checkmated, the game ends and the opponent wins
                print(f"[{len(self.move_history)}] Checkmate! {self.check_side.opponent().name()} wins.")
            else:
                # the current player was stalemated, the game ends in a draw
                print(f"[{len(self.move_history)}] Stalemate! It's a draw.")
        else:
            if self.check_side != Side.NONE:
                # the game is still going, but the current player is in check
                print(f"[{len(self.move_history)}] {self.check_side.name()} is in check!")
            else:
                # the game is still going and there is no check
                pass
        self.color_all_pieces()

    def update_colors(self) -> None:
        self.color_scheme = colors[self.color_index]
        if self.trickster_color_index:
            self.color_scheme = copy(self.color_scheme)
            new_colors = (
                trickster_colors[self.trickster_color_index - 1],
                trickster_colors[self.trickster_color_index % len(trickster_colors)]
            )
            self.color_scheme["light_square_color"] = lighten(desaturate(new_colors[0], 0.11), 0.011)
            self.color_scheme["dark_square_color"] = lighten(desaturate(new_colors[1], 0.11), 0.011)
            self.color_scheme["background_color"] = darken(average(
                self.color_scheme["light_square_color"],
                self.color_scheme["dark_square_color"]
            ), 0.11 / 2)
            self.color_scheme["promotion_area_color"] = darken(self.color_scheme["background_color"], 0.11)
            self.color_scheme["text_color"] = darken(self.color_scheme["background_color"], 0.11 * 3)
            self.color_scheme["white_piece_color"] = saturate(darken(new_colors[0], 0.11), 0.11)
            self.color_scheme["black_piece_color"] = desaturate(darken(new_colors[1], 0.11), 0.11)
            self.color_scheme["white_check_color"] = desaturate(self.color_scheme["white_piece_color"], 0.11)
            self.color_scheme["black_check_color"] = desaturate(self.color_scheme["black_piece_color"], 0.11)
            self.color_scheme["white_win_color"] = darken(self.color_scheme["white_piece_color"], 0.11)
            self.color_scheme["black_win_color"] = darken(self.color_scheme["black_piece_color"], 0.11)
            self.color_scheme["white_draw_color"] = desaturate(self.color_scheme["white_piece_color"], 0.11 * 5)
            self.color_scheme["black_draw_color"] = desaturate(self.color_scheme["black_piece_color"], 0.11 * 5)
            self.color_scheme["loss_color"] = getrgb("#bbbbbb")
        self.background_color = self.color_scheme["background_color"]
        for sprite in self.label_list:
            sprite.color = self.color_scheme["text_color"]
        for sprite in self.board_sprite_list:
            color = sum(self.get_board_position(sprite.position)) % 2
            sprite.color = self.color_scheme["light_square_color" if color else "dark_square_color"]
        for sprite in self.promotion_area_sprite_list:
            sprite.color = self.color_scheme["promotion_area_color"]
        for sprite in self.promotion_piece_sprite_list:
            if isinstance(sprite, abc.Piece):
                sprite.set_color(
                    self.color_scheme.get(
                        f"{sprite.side.file_name()}piece_color",
                        self.color_scheme["piece_color"]
                    ),
                    self.color_scheme["colored_pieces"]
                )
        self.color_all_pieces()

    def color_all_pieces(self) -> None:
        if self.game_over:
            if self.check_side != Side.NONE:
                self.color_pieces(
                    self.check_side,
                    self.color_scheme.get(
                        f"{self.check_side.file_name()}loss_color",
                        self.color_scheme["loss_color"]
                    ),
                )
                self.color_pieces(
                    self.check_side.opponent(),
                    self.color_scheme.get(
                        f"{self.check_side.opponent().file_name()}win_color",
                        self.color_scheme["win_color"]
                    ),
                )
            else:
                self.color_pieces(
                    Side.WHITE,
                    self.color_scheme.get(
                        f"{Side.WHITE.file_name()}draw_color",
                        self.color_scheme["draw_color"]
                    ),
                )
                self.color_pieces(
                    Side.BLACK,
                    self.color_scheme.get(
                        f"{Side.BLACK.file_name()}draw_color",
                        self.color_scheme["draw_color"]
                    ),
                )
        else:
            if self.check_side != Side.NONE:
                self.color_pieces(
                    self.check_side,
                    self.color_scheme.get(
                        f"{self.check_side.file_name()}check_color",
                        self.color_scheme["check_color"]
                    ),
                )
                self.color_pieces(self.check_side.opponent())
            else:
                self.color_pieces()

    def update_trickster_mode(self) -> None:
        if not self.trickster_color_index:
            self.trickster_color_delta = 0
            return  # trickster mode is disabled
        if self.trickster_color_delta > 1 / 11:
            self.trickster_color_delta %= 1 / 11  # ah yes, modulo assignment. derpy stepbrother of the walrus operator
            self.trickster_color_index = self.trickster_color_index % len(trickster_colors) + 1
            self.update_colors()
        for sprite_list in (self.piece_sprite_list, self.promotion_piece_sprite_list, [self.active_piece]):
            for sprite in sprite_list:
                if (
                        isinstance(sprite, abc.Piece) and not sprite.is_empty()
                        and not (self.game_over and not self.edit_mode and sprite.side == self.check_side)
                ):
                    sprite.angle += self.trickster_angle_delta / 11 * 360 * (1 if sum(sprite.board_pos) % 2 else -1)
        self.trickster_angle_delta = 0

    def reset_trickster_mode(self) -> None:
        if self.trickster_color_index:
            return  # trickster mode is enabled
        self.update_colors()
        for sprite_list in (self.piece_sprite_list, self.promotion_piece_sprite_list):
            for sprite in sprite_list:
                if isinstance(sprite, abc.Piece) and not sprite.is_empty():
                    sprite.angle = 0

    def load_all_moves(self) -> None:
        self.load_check()
        movable_pieces = {side: self.movable_pieces[side].copy() for side in self.movable_pieces}
        royal_pieces = {side: self.royal_pieces[side].copy() for side in self.royal_pieces}
        quasi_royal_pieces = {side: self.quasi_royal_pieces[side].copy() for side in self.quasi_royal_pieces}
        check_side = self.check_side
        castling_threats = self.castling_threats.copy()
        en_passant_target = self.en_passant_target
        en_passant_markers = self.en_passant_markers.copy()
        self.moves = {}
        for piece in movable_pieces[self.turn_side]:
            for move in piece.moves():
                self.update_move(move)
                self.move(move)
                self.load_check()
                if self.check_side != self.turn_side:
                    self.moves.setdefault(move.pos_from, []).append(move)
                self.undo(move)
                self.check_side = check_side
                self.castling_threats = castling_threats.copy()
                if en_passant_target is not None:
                    self.en_passant_target = en_passant_target
                    self.en_passant_markers = en_passant_markers.copy()
                    for marker in self.en_passant_markers:
                        self.mark_en_passant(self.en_passant_target.board_pos, marker)
        self.theoretical_moves = {}
        for piece in movable_pieces[self.turn_side.opponent()]:
            for move in piece.moves(theoretical=True):
                self.theoretical_moves.setdefault(move.pos_from, []).append(move)
        self.movable_pieces = movable_pieces
        self.royal_pieces = royal_pieces
        self.quasi_royal_pieces = quasi_royal_pieces
        self.check_side = check_side
        self.castling_threats = castling_threats

    def load_pieces(self):
        self.movable_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.royal_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.quasi_royal_pieces = {Side.WHITE: [], Side.BLACK: []}
        for row, col in product(range(self.board_height), range(self.board_width)):
            piece = self.get_piece((row, col))
            if piece.side != Side.NONE:
                self.movable_pieces[piece.side].append(piece)
                if isinstance(piece, abc.RoyalPiece):
                    self.royal_pieces[piece.side].append(piece)
                elif isinstance(piece, abc.QuasiRoyalPiece):
                    self.quasi_royal_pieces[piece.side].append(piece)
        for side in (Side.WHITE, Side.BLACK):
            if len(self.quasi_royal_pieces[side]) == 1:
                self.royal_pieces[side].append(self.quasi_royal_pieces[side].pop())

    def load_check(self):
        self.load_pieces()
        self.check_side = Side.NONE
        self.castling_threats = set()
        for royal in self.royal_pieces[self.turn_side]:
            castle_moves = [
                move for move in royal.moves() if isinstance(move.movement, movement.CastlingMovement)
            ]
            castle_movements = set(move.movement for move in castle_moves)
            castle_squares = set(
                add(royal.board_pos, offset)
                for castling in castle_movements
                for offset in castling.gap + [castling.direction]
            )
            for piece in self.movable_pieces[self.turn_side.opponent()]:
                for move in piece.moves():
                    if move.pos_to == royal.board_pos:
                        self.check_side = self.turn_side
                        self.castling_threats = castle_squares
                        break
                    if move.pos_to in castle_squares:
                        self.castling_threats.add(move.pos_to)
                if self.check_side != Side.NONE:
                    break
            if self.check_side != Side.NONE:
                break

    def mark_en_passant(self, piece_pos: Position, marker_pos: Position) -> None:
        if self.en_passant_target is not None and self.en_passant_target.board_pos != piece_pos:
            return
        self.en_passant_target = self.get_piece(piece_pos)
        if self.not_a_piece(marker_pos):
            self.replace(self.get_piece(marker_pos), NoPiece, self.en_passant_target.side)
        self.en_passant_markers.add(marker_pos)

    def capture_en_passant(self) -> None:
        if self.en_passant_target is None:
            return
        self.replace(self.en_passant_target, NoPiece, Side.NONE)
        self.clear_en_passant()

    def clear_en_passant(self) -> None:
        self.en_passant_target = None
        for marker in self.en_passant_markers:
            if self.not_a_piece(marker):
                self.replace(self.get_piece(marker), NoPiece, Side.NONE)
        self.en_passant_markers = set()

    def on_key_press(self, symbol, modifiers):
        if self.edit_mode and modifiers & key.MOD_ACCEL:
            if self.held_buttons & MOUSE_BUTTON_LEFT and self.selected_square is not None:
                self.reset_position(self.get_piece(self.selected_square))
        if self.held_buttons:
            return
        if symbol == key.R:  # Restart
            if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:
                self.piece_sets = {Side.WHITE: 1, Side.BLACK: 1}
                self.reset_board(update=True)
            elif modifiers & key.MOD_SHIFT:
                self.reset_board(shuffle=True)
            elif modifiers & key.MOD_ACCEL:
                self.reset_board()
        if symbol == key.F11:  # Full screen (toggle)
            self.set_fullscreen(not self.fullscreen)
        if symbol == key.MINUS:  # (-) Decrease window size
            if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:
                self.set_size((self.board_width + 2) * min_size, (self.board_height + 2) * min_size)
            elif modifiers & key.MOD_ACCEL:
                width, height = self.get_size()
                self.set_size(
                    width - (self.board_width + 2) * size_step,
                    height - (self.board_height + 2) * size_step
                )
            elif modifiers & key.MOD_SHIFT:
                width, height = self.get_size()
                size = min(round(width / (self.board_width + 2)), round(height / (self.board_height + 2)))
                self.set_size((self.board_width + 2) * size, (self.board_height + 2) * size)
        if symbol == key.EQUAL:  # (+) Increase window size
            if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:
                self.set_size((self.board_width + 2) * max_size, (self.board_height + 2) * max_size)
            elif modifiers & key.MOD_ACCEL:
                width, height = self.get_size()
                self.set_size(
                    width + (self.board_width + 2) * size_step,
                    height + (self.board_height + 2) * size_step
                )
            elif modifiers & key.MOD_SHIFT:
                width, height = self.get_size()
                size = max(round(width / (self.board_width + 2)), round(height / (self.board_height + 2)))
                self.set_size((self.board_width + 2) * size, (self.board_height + 2) * size)
        if symbol == key.KEY_0 and modifiers & key.MOD_ACCEL:  # Reset window size
            self.set_size((self.board_width + 2) * self.square_size, (self.board_height + 2) * self.square_size)
        if symbol == key.E and modifiers & key.MOD_ACCEL:  # Edit mode (toggle)
            self.edit_mode = not self.edit_mode
            print(f"[{len(self.move_history)}] Mode: {'EDIT' if self.edit_mode else 'PLAY'}")
            self.deselect_piece()
            self.hide_moves()
            if self.edit_mode:
                self.advance_turn()
                self.moves = {}
                self.theoretical_moves = {}
                self.show_moves()
            else:
                self.turn_side = self.turn_side.opponent()
                self.advance_turn()
                self.show_moves()
        if symbol == key.W:  # White
            if modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:  # White is in control
                if self.turn_side != Side.WHITE:
                    self.move_history.append(None)
                    print(f"[{len(self.move_history)}] Pass: {Side.WHITE.name()}'s turn")
                    self.clear_en_passant()
                    self.advance_turn()
            elif modifiers & key.MOD_SHIFT:  # Shift white piece set
                d = -1 if modifiers & key.MOD_ACCEL else 1
                self.piece_sets[Side.WHITE] = (self.piece_sets[Side.WHITE] + d - 1) % len(piece_groups) + 1
                self.reset_board(update=True)
        if symbol == key.B:  # Black
            if modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:  # Black is in control
                if self.turn_side != Side.BLACK:
                    self.move_history.append(None)
                    print(f"[{len(self.move_history)}] Pass: {Side.BLACK.name()}'s turn")
                    self.clear_en_passant()
                    self.advance_turn()
            elif modifiers & key.MOD_SHIFT:  # Shift black piece set
                d = -1 if modifiers & key.MOD_ACCEL else 1
                self.piece_sets[Side.BLACK] = (self.piece_sets[Side.BLACK] + d - 1) % len(piece_groups) + 1
                self.reset_board(update=True)
        if symbol == key.N:  # Next
            if modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:  # Next player is in control
                self.move_history.append(None)
                print(f"[{len(self.move_history)}] Pass: {self.turn_side.opponent().name()}'s turn")
                self.clear_en_passant()
                self.advance_turn()
            elif modifiers & key.MOD_SHIFT:
                if self.piece_sets[Side.WHITE] == self.piece_sets[Side.BLACK]:  # Next piece set
                    d = -1 if modifiers & key.MOD_ACCEL else 1
                    self.piece_sets[Side.WHITE] = (self.piece_sets[Side.WHITE] + d - 1) % len(piece_groups) + 1
                    self.piece_sets[Side.BLACK] = (self.piece_sets[Side.BLACK] + d - 1) % len(piece_groups) + 1
                else:  # Next player goes first
                    piece_sets = self.piece_sets[Side.WHITE], self.piece_sets[Side.BLACK]
                    self.piece_sets[Side.BLACK], self.piece_sets[Side.WHITE] = piece_sets
                self.reset_board(update=True)
        if symbol == key.F and modifiers & key.MOD_ACCEL:  # Flip
            self.flip_board()
        if symbol == key.G:  # Graphics
            if modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:  # Graphics reset
                self.color_index = 0
            elif modifiers & key.MOD_SHIFT:  # Graphics shift
                self.color_index = (self.color_index + (-1 if modifiers & key.MOD_ACCEL else 1)) % len(colors)
            if self.color_scheme["scheme_type"] == "cherub" and self.trickster_color_index:
                self.trickster_color_index = 0
                self.reset_trickster_mode()
            else:
                self.update_colors()
        if symbol == key.T and modifiers & key.MOD_ACCEL:  # Trickster mode
            if self.color_scheme["scheme_type"] == "cherub":
                self.trickster_color_index = (
                    randrange(len(trickster_colors)) + 1 if not self.trickster_color_index else 0
                )
                self.reset_trickster_mode()
        if symbol == key.Z and modifiers & key.MOD_ACCEL:  # Undo
            if modifiers & key.MOD_SHIFT:  # Unless Ctrl+Shift+Z, then redo
                self.redo_last_finished_move()
            else:
                self.undo_last_finished_move()
        if symbol == key.Y and modifiers & key.MOD_ACCEL:  # Redo
            self.redo_last_finished_move()
        if symbol == key.SLASH:  # (?) Random
            if modifiers & key.MOD_SHIFT:  # Random piece
                self.deselect_piece()
                if self.moves:
                    self.select_piece(choice(list(self.moves.keys())))
            if modifiers & key.MOD_ACCEL:  # Random move
                if self.game_over and not self.edit_mode:
                    return
                choices = (
                    self.moves.get(self.selected_square, [])
                    if self.selected_square            # Pick from moves of selected piece
                    else sum(self.moves.values(), [])  # Pick from all possible moves
                )
                if choices:
                    random_move = choice(choices)
                    self.update_move(random_move)
                    random_move.piece.move(random_move)
                    self.move_history.append(random_move)
                    print(f"[{len(self.move_history)}] Move: {self.move_history[-1]}")
                    self.advance_turn()

    def update_sprite(
            self, sprite: Sprite, from_size: float, from_origin: tuple[float, float], from_flip_mode: bool
    ) -> None:
        old_position = sprite.position
        sprite.scale = self.square_size / sprite.texture.width
        sprite.position = self.get_screen_position(self.get_board_position(
            old_position, from_size, from_origin, from_flip_mode
        ))

    def update_sprites(self, width: float, height: float, flip_mode: bool) -> None:
        super().on_resize(width, height)
        old_size = self.square_size
        self.square_size = min(self.width / (self.board_width + 2), self.height / (self.board_height + 2))
        old_origin = self.origin
        self.origin = self.width / 2, self.height / 2
        old_flip_mode = self.flip_mode
        self.flip_mode = flip_mode
        old_selected_square = self.selected_square
        self.update_sprite(self.highlight, old_size, old_origin, old_flip_mode)
        self.update_sprite(self.selection, old_size, old_origin, old_flip_mode)
        if self.active_piece is not None:
            self.update_sprite(self.active_piece, old_size, old_origin, old_flip_mode)
        for sprite_list in (
            self.board_sprite_list,
            self.move_sprite_list,
            self.piece_sprite_list,
            self.promotion_area_sprite_list,
            self.promotion_piece_sprite_list,
        ):
            for sprite in sprite_list:
                self.update_sprite(sprite, old_size, old_origin, old_flip_mode)
        for label in self.label_list:
            old_position = label.position
            label.font_size = self.square_size / 2
            label.x, label.y = self.get_screen_position(
                self.get_board_position(old_position, old_size, old_origin, old_flip_mode)
            )
        self.select_piece(old_selected_square)
        self.update_highlight(self.get_board_position(self.highlight.position, old_size, old_origin, old_flip_mode))

    def flip_board(self) -> None:
        self.update_sprites(self.width, self.height, not self.flip_mode)

    def on_resize(self, width: float, height: float):
        self.update_sprites(width, height, self.flip_mode)

    def on_deactivate(self):
        self.hovered_square = None
        self.clicked_square = None
        self.held_buttons = 0
        self.highlight.alpha = 0
        self.show_moves()

    def run(self):
        pass
