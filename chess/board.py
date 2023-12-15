from copy import copy
from itertools import product, zip_longest
from math import ceil, sqrt
from random import choice
from typing import Type

from cocos.batch import BatchNode
from cocos.director import director
from cocos.layer import ColorLayer
from cocos.scene import Scene
from cocos.sprite import Sprite
from cocos.text import Label

from pyglet.window import key, mouse

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
background_color = 192, 192, 192
highlight_color = 255, 255, 204
highlight_opacity = 25
selection_opacity = 50
win_shade = 225
loss_shade = 125
draw_shade = 175

movements = []


def get_cell_color(pos: Position) -> tuple[int, int, int]:
    if (pos[0] + pos[1]) % 2:
        return 255, 204, 153
    else:
        return 187, 119, 51


def get_royal_color(side: Side) -> tuple[int, int, int]:
    if side == Side.WHITE:
        return 255, 255, 204
    else:
        return 255, 153, 153


class Board(ColorLayer):

    def __init__(self):
        self.board_width, self.board_height = board_width, board_height
        self.size = default_size

        self.is_event_handler = True
        director.init(
            width=(self.board_width + 2) * self.size,
            height=(self.board_height + 2) * self.size,
            caption='Chess',
            autoscale=True,
        )
        super().__init__(192, 168, 142, 1000)
        # remove default key combinations to not clash with our custom ones
        director.window.remove_handlers(director._default_event_handler)

        # super boring initialization stuff (bluh bluh)
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
        self.game_over = False  # act 6 act 6 intermission 3 (game over)
        self.edit_mode = False  # allows to edit the board position if set to True
        self.pieces = []  # list of pieces on the board
        self.piece_sets = {Side.WHITE: 1, Side.BLACK: 1}  # piece sets to use for each side
        self.promotions = {Side.WHITE: [], Side.BLACK: []}  # types of pieces each side promote to
        self.edit_promotions = {Side.WHITE: [], Side.BLACK: []}  # types of pieces each side can promote to in edit mode
        self.movable_pieces = {Side.WHITE: [], Side.BLACK: []}  # pieces that can be moved by each side
        self.royal_pieces = {Side.WHITE: [], Side.BLACK: []}  # these have to stay on the board and should be protected
        self.quasi_royal_pieces = {Side.WHITE: [], Side.BLACK: []}  # at least one of these has to stay on the board
        self.board_sprites = []  # sprites for the board squares
        self.row_labels = []  # labels for the rows
        self.col_labels = []  # labels for the columns
        self.moves = {}  # dictionary of valid moves from any square that has a movable piece on it
        self.theoretical_moves = {}  # dictionary of theoretical moves from any square that has an opposing piece on it
        self.anchor = 0, 0  # used to have the board scale from the origin instead of the center
        self.board = BatchNode()  # node for the board sprites
        self.highlight = Sprite("assets/util/selection.png", color=highlight_color, opacity=0)  # highlight sprite
        self.highlight.scale = self.size / self.highlight.width  # scale it to the size of a square
        self.selection = Sprite("assets/util/selection.png", opacity=0)  # sprite for the selection marker
        self.selection.scale = self.size / self.selection.width  # scale it to the size of a square
        self.move_node = BatchNode()  # node for the move markers
        self.piece_node = BatchNode()  # node for the piece sprites
        self.active_piece_node = BatchNode()  # node for the selected piece
        self.promotion_area_node = BatchNode()  # node for the promotion area background tiles
        self.promotion_piece_node = BatchNode()  # node for the possible promotion pieces

        # let's add it all together shall we
        self.add(self.board, z=1)
        self.add(self.highlight, z=2)
        self.add(self.selection, z=3)
        self.add(self.move_node, z=4)
        self.add(self.piece_node, z=5)
        self.add(self.active_piece_node, z=6)
        self.add(self.promotion_area_node, z=7)
        self.add(self.promotion_piece_node, z=8)

        # initialize row/column labels
        label_kwargs = {
            'font_name': 'Courier New',
            'font_size': default_size * 0.5,
            'bold': True,
            'color': (0, 0, 0, 1000)
        }

        for row in range(self.board_height):
            self.row_labels += [
                Label(str(row + 1), self.get_screen_position((row, -0.9)),
                      anchor_x='center', anchor_y='center', **label_kwargs),
                Label(str(row + 1), self.get_screen_position((row, board_width - 0.1)),
                      anchor_x='center', anchor_y='center', **label_kwargs),
            ]

        for col in range(self.board_width):
            self.col_labels += [
                Label(chr(col + ord('a')), self.get_screen_position((-0.9, col)),
                      anchor_x='center', anchor_y='center', **label_kwargs),
                Label(chr(col + ord('a')), self.get_screen_position((board_height - 0.1, col)),
                      anchor_x='center', anchor_y='center', **label_kwargs),
            ]

        for label in self.row_labels + self.col_labels:
            label.scale = 0.8
            self.add(label, z=1)

        # initialize board sprites
        self.board_sprites = [[] for _ in range(self.board_height)]

        for row, col in product(range(self.board_height), range(self.board_width)):

            self.board_sprites[row].append(Sprite("assets/util/cell.png"))
            self.board_sprites[row][col].position = self.get_screen_position((row, col))
            self.board_sprites[row][col].color = get_cell_color((row, col))
            self.board_sprites[row][col].scale = default_size / self.board_sprites[row][col].width
            self.board.add(self.board_sprites[row][col])

        # set up pieces on the board
        self.reset_board(update=True)

        # it's showtime
        director.run(Scene(self))

    def resize(self, new_cell_size: int) -> None:
        self.size = new_cell_size
        dimensions = (self.board_width + 2) * self.size, (self.board_height + 2) * self.size
        director.window.set_size(*dimensions)
        # self.scale = self.size / self.board_sprites[0][0].width

    def reset_board(self, shuffle: bool = False, update: bool = False) -> None:
        self.deselect_piece()  # you know, just in case
        self.turn_side = Side.WHITE
        self.game_over = False
        self.edit_mode = False

        for sprite in self.piece_node.get_children():
            self.piece_node.remove(sprite)

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
            self.pieces[row][col].color = (255, 255, 255)
            self.pieces[row][col].scale = default_size / self.pieces[row][col].width
            self.piece_node.add(self.pieces[row][col])

        self.load_all_moves()
        self.show_moves()

    def get_board_position(self, x: float, y: float) -> Position:
        window_width, window_height = director.get_window_size()
        x, y = director.get_virtual_coordinates(x, y)
        col = round((x - window_width / 2) / default_size + (self.board_width - 1) / 2)
        row = round((y - window_height / 2) / default_size + (self.board_height - 1) / 2)
        return row, col

    def get_screen_position(self, pos: tuple[float, float]) -> tuple[float, float]:
        window_width = (self.board_width + 2) * default_size
        window_height = (self.board_height + 2) * default_size
        row, col = pos
        x = (col - (self.board_width - 1) / 2) * default_size + window_width / 2
        y = (row - (self.board_height - 1) / 2) * default_size + window_height / 2
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
        self.selection.opacity = selection_opacity
        self.selection.position = self.get_screen_position(pos)

        # move the piece to active piece node (to be displayed on top of everything else)
        piece = self.get_piece(self.selected_square)
        self.piece_node.remove(piece)
        self.active_piece_node.add(piece)

        self.show_moves()

    def show_moves(self) -> None:
        self.hide_moves()
        if self.selected_square is None and self.not_on_board(self.hovered_square):
            if not self.move_history:
                return
            move = self.move_history[-1]
            if move is None or move.is_edit:
                return
            if move.pos_from is not None:
                move_sprite = Sprite(
                    f"assets/util/{'move' if self.not_a_piece(move.pos_from) else 'capture'}.png",
                    position=self.get_screen_position(move.pos_from),
                    opacity=selection_opacity
                )
                move_sprite.scale = default_size / move_sprite.width
                self.move_node.add(move_sprite)
            if move.pos_to is not None and move.pos_from != move.pos_to:
                move_sprite = Sprite(
                    f"assets/util/{'move' if self.not_a_piece(move.pos_to) else 'capture'}.png",
                    position=self.get_screen_position(move.pos_to),
                    opacity=selection_opacity
                )
                move_sprite.scale = default_size / move_sprite.width
                self.move_node.add(move_sprite)
        else:
            pos = self.selected_square or self.hovered_square
            if self.not_on_board(pos):
                return
            theoretical = self.get_side(pos) == self.turn_side.opponent()
            move_dict = self.theoretical_moves if theoretical else self.moves
            move_positions = set()
            for move in move_dict.get(pos, ()):
                if move.pos_to in move_positions:
                    continue
                move_positions.add(move.pos_to)
                move_sprite = Sprite(
                    f"assets/util/{'move' if self.not_a_piece(move.pos_to) else 'capture'}.png",
                    position=self.get_screen_position(move.pos_to),
                    opacity=selection_opacity if self.selected_square else highlight_opacity
                )
                move_sprite.scale = default_size / move_sprite.width
                self.move_node.add(move_sprite)

    def deselect_piece(self) -> None:
        self.selection.opacity = 0
        self.square_was_clicked = False

        if self.nothing_selected():
            return

        # move the piece to general piece node
        piece = self.get_piece(self.selected_square)
        self.reset_position(piece)
        self.active_piece_node.remove(piece)
        self.piece_node.add(piece)

        self.selected_square = None
        self.show_moves()

    def hide_moves(self) -> None:
        for child in list(self.move_node.get_children()):
            self.move_node.remove(child)

    def on_mouse_press(self, x, y, buttons, modifiers) -> None:
        if buttons & mouse.LEFT:
            self.held_buttons = mouse.LEFT
            if self.game_over and not self.edit_mode:
                return
            pos = self.get_board_position(x, y)
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
            self.clicked_square = pos  # we need this in order to discern what are we dragging
            if self.not_a_piece(pos):
                return
            if self.turn_side != self.get_side(pos) and not self.edit_mode:
                return
            if self.selected_square is not None:
                if self.selected_square == pos:
                    self.deselect_piece()
                    return
                if self.edit_mode:
                    return
            self.deselect_piece()  # just in case we had something previously selected
            self.select_piece(pos)
        if buttons & mouse.RIGHT:
            self.held_buttons = mouse.RIGHT
            if self.promotion_piece:
                self.undo_last_finished_move()
                return
            if self.edit_mode:
                pos = self.get_board_position(x, y)
                if self.not_on_board(pos):
                    return
                self.clicked_square = pos  # we need this in order to discern what are we dragging
                self.deselect_piece()  # just in case we had something previously selected

    def on_mouse_motion(self, x, y, dx, dy) -> None:
        pos = self.get_board_position(x + dx, y + dy)
        if self.clicked_square != pos:
            self.square_was_clicked = False
            self.clicked_square = None
        if self.not_on_board(pos):
            self.highlight.opacity = 0
            self.hovered_square = None
            if (self.selected_square is None and not self.move_history) or self.promotion_piece:
                self.hide_moves()
            else:
                self.show_moves()
        else:
            self.highlight.opacity = highlight_opacity
            self.highlight.position = self.get_screen_position(pos)
            if self.hovered_square != pos:
                self.hovered_square = pos
                if self.selected_square is None and not self.promotion_piece:
                    self.show_moves()
                elif self.promotion_piece:
                    self.hide_moves()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers) -> None:
        self.on_mouse_motion(x, y, dx, dy)  # move the highlight as well!
        if buttons & self.held_buttons & mouse.LEFT and self.selected_square is not None:
            if self.edit_mode and modifiers & key.MOD_ACCEL:
                self.reset_position(self.get_piece(self.selected_square))
            else:
                sprite = self.get_piece(self.selected_square)
                x, y = director.get_virtual_coordinates(x, y)
                sprite.x = x
                sprite.y = y

    def on_mouse_release(self, x, y, buttons, modifiers) -> None:
        held_buttons = buttons & self.held_buttons
        self.held_buttons = 0
        if self.edit_mode:
            if self.promotion_piece:
                return
            pos = self.get_board_position(x, y)
            if self.not_on_board(pos):
                return
            move = Move(is_edit=True)
            if held_buttons & mouse.LEFT:
                if self.nothing_selected():
                    return
                if self.not_a_piece(pos):
                    if self.square_was_clicked:
                        self.deselect_piece()
                        return
                if pos == self.selected_square:
                    if self.square_was_clicked:
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
            elif held_buttons & mouse.RIGHT:
                if self.clicked_square != pos:
                    self.clicked_square = None
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
            selection = self.selected_square
            self.square_was_clicked = self.clicked_square == pos
            square_was_clicked = self.square_was_clicked  # we need this because self.square_was_clicked will be reset
            self.clicked_square = None
            move.piece.move(move)
            self.move_history.append(move)
            if not self.promotion_piece:
                print(f"[{len(self.move_history)}] Edit: {self.move_history[-1]}")
            self.advance_turn()
            if (
                    held_buttons & mouse.LEFT
                    and modifiers & key.MOD_ACCEL
                    and square_was_clicked
            ):
                self.select_piece(selection)
            return
        if held_buttons & mouse.RIGHT:
            self.deselect_piece()
            return
        if held_buttons & mouse.LEFT:
            if self.game_over:
                self.deselect_piece()
                return
            if self.promotion_piece:
                return
            if self.nothing_selected():
                return
            selected = self.selected_square
            pos = self.get_board_position(x, y)
            self.square_was_clicked = self.clicked_square == pos
            self.clicked_square = None
            if self.not_on_board(pos):
                if self.square_was_clicked:
                    self.deselect_piece()
                    return
            if pos == self.selected_square:
                self.reset_position(self.get_piece(pos))
                if not self.square_was_clicked:
                    self.deselect_piece()
            else:
                move = self.find_move(selected, pos)
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

    def update_move(self, move: Move) -> None:
        move.set(piece=self.get_piece(move.pos_from))
        if move.pos_from != move.pos_to:
            captured_piece = self.get_piece(move.pos_to)
            if captured_piece.side != Side.NONE:
                move.set(captured_piece=(self.en_passant_target if captured_piece.is_empty() else captured_piece))

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
            self.piece_node.remove(move.piece)
        if move.pos_to is not None and move.pos_from != move.pos_to:
            self.piece_node.remove(self.pieces[move.pos_to[0]][move.pos_to[1]])
            self.pieces[move.pos_to[0]][move.pos_to[1]] = move.piece
        if move.pos_from is not None and move.pos_from != move.pos_to:
            self.pieces[move.pos_from[0]][move.pos_from[1]] = (
                NoPiece(self, move.pos_from) if move.swapped_piece is None else move.swapped_piece
            )
            self.piece_node.add(self.pieces[move.pos_from[0]][move.pos_from[1]])
        if move.piece is not None and move.pos_from is None:
            self.piece_node.add(move.piece)
        if not move.is_edit or (move.pos_from == move.pos_to and move.promotion is None):
            (move.piece or move).movement.update(move, move.piece.side or self.turn_side)

    def update(self, move: Move) -> None:
        if self.en_passant_target is not None and move.piece.side == self.en_passant_target.side.opponent():
            if move.pos_to in self.en_passant_markers and isinstance(move.movement, movement.EnPassantMovement):
                self.capture_en_passant()
            else:
                self.clear_en_passant()

    def undo(self, move: Move) -> None:
        if move.pos_from != move.pos_to or move.promotion is not None:
            if move.pos_from is not None:
                self.set_position(move.piece, move.pos_from)
                self.piece_node.remove(self.pieces[move.pos_from[0]][move.pos_from[1]])
            if move.pos_to is not None and move.pos_from != move.pos_to:
                self.piece_node.remove(self.pieces[move.pos_to[0]][move.pos_to[1]])
            if move.pos_from is not None:
                self.pieces[move.pos_from[0]][move.pos_from[1]] = move.piece
                self.piece_node.add(move.piece)
        if move.captured_piece is not None:
            if move.captured_piece.board_pos != move.pos_to:
                self.piece_node.remove(self.pieces[move.captured_piece.board_pos[0]][move.captured_piece.board_pos[1]])
            self.reset_position(move.captured_piece)
            self.pieces[move.captured_piece.board_pos[0]][move.captured_piece.board_pos[1]] = move.captured_piece
            self.piece_node.add(move.captured_piece)
        if move.pos_to is not None and move.pos_from != move.pos_to:
            if move.captured_piece is None or move.captured_piece.board_pos != move.pos_to:
                self.pieces[move.pos_to[0]][move.pos_to[1]] = NoPiece(self, move.pos_to)
                self.piece_node.add(self.pieces[move.pos_to[0]][move.pos_to[1]])
            if move.swapped_piece is not None:
                self.set_position(move.swapped_piece, move.pos_to)
                self.piece_node.add(move.swapped_piece)
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
            print(f'[{len(self.move_history)}] Undo: {
                f"{'Edit' if self.move_history[-1].is_edit else 'Move'}: " + str(self.move_history[-1])
                if self.move_history[-1] is not None else f"Pass: {self.turn_side.name()}'s turn"
            }')
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
        if last_move.is_edit and not self.edit_mode:
            self.turn_side = self.turn_side.opponent()
        if self.promotion_piece is None:
            print(f'[{len(self.move_history)}] Redo: {
                f"{'Edit' if self.move_history[-1].is_edit else 'Move'}: " + str(self.move_history[-1])
                if self.move_history[-1] is not None else f"Pass: {self.turn_side.opponent().name()}'s turn"
            }')
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
            background_sprite = Sprite(
                "assets/util/cell.png", position=self.get_screen_position(pos), color=background_color
            )
            background_sprite.scale = default_size / background_sprite.width
            self.promotion_area_node.add(background_sprite)
            if promotion is None:
                continue
            promotion_piece = promotion(self, pos, piece.side)
            promotion_piece.scale = default_size / promotion_piece.width
            self.promotion_piece_node.add(promotion_piece)
            self.promotion_area[pos] = promotion

    def end_promotion(self) -> None:
        self.promotion_piece = None
        self.promotion_area = {}
        for node in (self.promotion_area_node, self.promotion_piece_node):
            for sprite in node.get_children():
                node.remove(sprite)

    def replace(self, piece: abc.Piece, new_type: Type[abc.Piece], new_side: Side | None = None) -> None:
        if new_side is None:
            new_side = piece.side
        pos = piece.board_pos
        self.piece_node.remove(piece)
        self.pieces[pos[0]][pos[1]] = new_type(
            self, pos, new_side,
            promotions=self.promotions[new_side],
            promotion_squares=promotion_squares[new_side],
        ) if issubclass(new_type, abc.PromotablePiece) else new_type(self, pos, new_side)
        self.pieces[pos[0]][pos[1]].scale = default_size / self.pieces[pos[0]][pos[1]].width
        self.piece_node.add(self.pieces[pos[0]][pos[1]])
        self.pieces[pos[0]][pos[1]].board_pos = pos
        if pos in self.en_passant_markers and not self.not_a_piece(pos):
            self.en_passant_markers.remove(pos)

    def color_pieces(self, side: Side = Side.ANY, color: tuple[int, int, int] | None = None, shade: int = 255) -> None:
        for piece in self.movable_pieces.get(side, sum(self.movable_pieces.values(), [])):
            piece.color = color or (shade, ) * 3

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
            self.color_pieces(shade=255)  # reverting the piece colors to normal in case they were previously changed
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
        if self.game_over:
            # the game has ended. let's find out who won and show it by changing piece colors... unless edit mode is on!
            if pass_check_side != Side.NONE:
                # the last player was in check and passed the turn, the game ends and the current player wins
                self.color_pieces(pass_check_side, shade=loss_shade)
                self.color_pieces(pass_check_side.opponent(), shade=win_shade)
                print(f"[{len(self.move_history)}] Game over! {pass_check_side.opponent().name()} wins.")
            elif self.check_side != Side.NONE:
                # the current player was checkmated, the game ends and the opponent wins
                self.color_pieces(self.check_side, shade=loss_shade)
                self.color_pieces(self.check_side.opponent(), shade=win_shade)
                print(f"[{len(self.move_history)}] Checkmate! {self.check_side.opponent().name()} wins.")
            else:
                # the current player was stalemated, the game ends in a draw
                self.color_pieces(shade=draw_shade)
                print(f"[{len(self.move_history)}] Stalemate! It's a draw.")
        else:
            # the game is still going, so let's revert the piece colors to normal in case they were changed
            self.color_pieces(shade=255)
            if self.check_side != Side.NONE:
                print(f"[{len(self.move_history)}] {self.check_side.name()} is in check!")

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
                add(royal.board_pos, offset) for mov in castle_movements for offset in mov.gap + [mov.direction]
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
            if self.held_buttons & mouse.LEFT and self.selected_square is not None:
                self.reset_position(self.get_piece(self.selected_square))
        if self.held_buttons:
            return
        if symbol == key.R:
            if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:
                self.piece_sets = {Side.WHITE: 1, Side.BLACK: 1}
                self.reset_board(update=True)
            elif modifiers & key.MOD_SHIFT:
                self.reset_board(shuffle=True)
            elif modifiers & key.MOD_ACCEL:
                self.reset_board()
        if symbol == key.MINUS and modifiers & key.MOD_ACCEL:
            if self.size == min_size:
                return
            self.resize(
                min_size if modifiers & key.MOD_SHIFT else max(min_size, self.size - size_step)
            )
        if symbol == key.EQUAL and modifiers & key.MOD_ACCEL:
            if self.size == max_size:
                return
            self.resize(
                max_size if modifiers & key.MOD_SHIFT else min(max_size, self.size + size_step)
            )
        if symbol == key._0 and modifiers & key.MOD_ACCEL:
            if self.size == default_size:
                return
            self.resize(default_size)
        if symbol == key.E and modifiers & key.MOD_ACCEL:
            self.edit_mode = not self.edit_mode
            print(f"[{len(self.move_history)}] Mode: {'EDIT' if self.edit_mode else 'PLAY'}")
            self.deselect_piece()
            self.hide_moves()
            if self.edit_mode:
                self.advance_turn()
                self.moves = {}
                self.theoretical_moves = {}
            else:
                self.turn_side = self.turn_side.opponent()
                self.advance_turn()
                self.show_moves()
        if symbol == key.W:
            if modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:
                if self.turn_side != Side.WHITE:
                    self.move_history.append(None)
                    print(f"[{len(self.move_history)}] Pass: {Side.WHITE.name()}'s turn")
                    self.clear_en_passant()
                    self.advance_turn()
            else:
                direction = -1 if modifiers & key.MOD_ACCEL else 1
                self.piece_sets[Side.WHITE] = (self.piece_sets[Side.WHITE] + direction - 1) % len(piece_groups) + 1
                self.reset_board(update=True)
        if symbol == key.B:
            if modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:
                if self.turn_side != Side.BLACK:
                    self.move_history.append(None)
                    print(f"[{len(self.move_history)}] Pass: {Side.BLACK.name()}'s turn")
                    self.clear_en_passant()
                    self.advance_turn()
            else:
                direction = -1 if modifiers & key.MOD_ACCEL else 1
                self.piece_sets[Side.BLACK] = (self.piece_sets[Side.BLACK] + direction - 1) % len(piece_groups) + 1
                self.reset_board(update=True)
        if symbol == key.Z and modifiers & key.MOD_ACCEL:
            if modifiers & key.MOD_SHIFT:
                self.redo_last_finished_move()
            else:
                self.undo_last_finished_move()
        if symbol == key.Y and modifiers & key.MOD_ACCEL:
            self.redo_last_finished_move()
        if symbol == key.SLASH:
            if modifiers & key.MOD_SHIFT:
                self.deselect_piece()
                if self.moves:
                    self.select_piece(choice(list(self.moves.keys())))
            if modifiers & key.MOD_ACCEL:
                choices = (
                    self.moves.get(self.selected_square, [])
                    if self.selected_square
                    else sum(self.moves.values(), [])
                )
                if choices:
                    random_move = choice(choices)
                    self.update_move(random_move)
                    random_move.piece.move(random_move)
                    self.move_history.append(random_move)
                    print(f"[{len(self.move_history)}] Move: {self.move_history[-1]}")
                    self.advance_turn()

    def on_deactivate(self):
        self.hovered_square = None
        self.clicked_square = None
        self.held_buttons = 0
        self.highlight.opacity = 0
        self.deselect_piece()
        self.show_moves()

    def run(self):
        pass

