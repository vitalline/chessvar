import math
import random
from itertools import product, zip_longest
from typing import Type

from cocos import scene
from cocos.batch import BatchNode
from cocos.director import director
from cocos.layer import ColorLayer
from cocos.sprite import Sprite
from cocos.text import Label

from pyglet.window import key, mouse

from chess.movement import movement
from chess.movement.move import Move
from chess.movement.util import Position, add
from chess.pieces import pieces as abc
from chess.pieces.groups import classic as fide, colorbound as cb, forward as fw
from chess.pieces.groups import knights as kn, pizza as pz, rookies as rk, util
from chess.pieces.groups.amazon import Amazon
from chess.pieces.pieces import Side

board_width = 8
board_height = 8

piece_groups = {
    1: [fide.Rook, fide.Knight, fide.Bishop, fide.Queen, fide.King, fide.Bishop, fide.Knight, fide.Rook],
    2: [cb.Bede, cb.Waffle, cb.FAD, cb.Cardinal, cb.King, cb.FAD, cb.Waffle, cb.Bede],
    3: [rk.ShortRook, rk.WoodyRook, rk.HalfDuck, rk.Chancellor, fide.King, rk.HalfDuck, rk.WoodyRook, rk.ShortRook],
    4: [kn.ChargeRook, kn.Fibnif, kn.ChargeKnight, kn.Colonel, fide.King, kn.ChargeKnight, kn.Fibnif, kn.ChargeRook],
    5: [kn.ChargeRook, fw.Knishop, fw.Bishight, fw.Forequeen, fide.King, fw.Bishight, fw.Knishop, kn.ChargeRook],
    6: [kn.ChargeRook, cb.Waffle, fide.Bishop, rk.Chancellor, fide.King, fide.Bishop, cb.Waffle, kn.ChargeRook],
    7: [rk.ShortRook, fide.Knight, fide.Bishop, Amazon, fide.King, fide.Bishop, fide.Knight, rk.ShortRook],
    8: [pz.Pepperoni, pz.Mushroom, pz.Sausage, pz.Meatball, fide.King, pz.Sausage, pz.Mushroom, pz.Pepperoni],
}

piece_group_names = {
    1: "Fabulous FIDEs",
    2: "Colorbound Clobberers",
    3: "Remarkable Rookies",
    4: "Nutty Knights",
    5: "Forward FIDEs",
    6: "All-Around Allstars",
    7: "Amazon Army",
    8: "Pizza Kings",
}


pawn_row = [fide.Pawn] * board_width
empty_row = [util.NoPiece] * board_width

white_row = [Side.WHITE] * board_width
black_row = [Side.BLACK] * board_width
neutral_row = [Side.NONE] * board_width

types = [white_row, pawn_row] + [empty_row] * (board_height - 4) + [pawn_row, black_row]
sides = [white_row, white_row] + [neutral_row] * (board_height - 4) + [black_row, black_row]

white_promotion_tiles = {(board_height - 1, i) for i in range(board_width)}
black_promotion_tiles = {(0, i) for i in range(board_width)}
promotion_tiles = {Side.WHITE: white_promotion_tiles, Side.BLACK: black_promotion_tiles}

cell_size = 50
background_color = 192, 192, 192
highlight_color = 255, 255, 204
highlight_opacity = 25
selection_opacity = 50
marker_opacity = 50


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
        self.is_event_handler = True
        director.init(
            width=(board_width+2)*cell_size,
            height=(board_height+2)*cell_size,
            caption='Chess',
            autoscale=False,

        )
        super().__init__(192, 168, 142, 1000)
        director.window.remove_handlers(director._default_event_handler)

        # super boring initialization stuff (bluh bluh)
        self.board_width, self.board_height = board_width, board_height
        self.clicked_piece = None
        self.selected_piece = None
        self.piece_was_clicked = False  # used to discern two-click moving from dragging
        self.en_passant_target = None
        self.en_passant_markers = set()
        self.promotion_piece = None
        self.promotion_area = {}
        self.move_history = []
        self.turn_side = Side.WHITE
        self.check_side = Side.NONE
        self.game_over = False
        self.pieces = []
        self.piece_sets = {Side.WHITE: 0, Side.BLACK: 0}
        self.promotion_types = {Side.WHITE: [], Side.BLACK: []}
        self.movable_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.royal_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.quasi_royal_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.board_sprites = []
        self.row_labels = []
        self.col_labels = []
        self.moves = {}
        self.no_moves = movement.RiderMovement(self, [])
        self.board = BatchNode()
        self.highlight = Sprite("assets/util/highlight.png", color=highlight_color, opacity=0)
        self.highlight.scale = cell_size / self.highlight.width
        self.selection = Sprite("assets/util/selection.png", opacity=0)
        self.selection.scale = cell_size / self.selection.width
        self.piece_node = BatchNode()
        self.move_node = BatchNode()
        self.active_piece_node = BatchNode()
        self.promotion_area_node = BatchNode()
        self.promotion_piece_node = BatchNode()
        self.add(self.board, z=1)
        self.add(self.highlight, z=2)
        self.add(self.selection, z=2)
        self.add(self.piece_node, z=3)
        self.add(self.move_node, z=3)
        self.add(self.active_piece_node, z=4)
        self.add(self.promotion_area_node, z=5)
        self.add(self.promotion_piece_node, z=6)

        label_kwargs = {
            'font_name': 'Courier New',
            'font_size': cell_size * 0.4,
            'bold': True,
            'color': (0, 0, 0, 1000)
        }

        for row in range(self.board_height):
            self.board_sprites += [[]]
            self.row_labels += [
                Label(str(row + 1), self.get_screen_position((row, -0.9)),
                      anchor_x='center', anchor_y='center', **label_kwargs),
                Label(str(row + 1), self.get_screen_position((row, board_width - 0.1)),
                      anchor_x='center', anchor_y='center', **label_kwargs),
            ]

        for col in range(self.board_width):
            self.row_labels += [
                Label(chr(col + ord('a')), self.get_screen_position((-0.9, col)),
                      anchor_x='center', anchor_y='center', **label_kwargs),
                Label(chr(col + ord('a')), self.get_screen_position((board_height - 0.1, col)),
                      anchor_x='center', anchor_y='center', **label_kwargs),
            ]

        for row, col in product(range(self.board_height), range(self.board_width)):

            self.board_sprites[row].append(Sprite("assets/util/cell.png"))
            self.board_sprites[row][col].position = self.get_screen_position((row, col))
            self.board_sprites[row][col].color = get_cell_color((row, col))
            self.board_sprites[row][col].scale = cell_size / self.board_sprites[row][col].width
            self.board.add(self.board_sprites[row][col])

        for label in self.row_labels + self.col_labels:
            self.add(label, z=1)

        self.reset_board(shuffle=True)

        director.run(scene.Scene(self))

    def reset_board(self, new_piece_sets: dict[Side, int] | None = None, shuffle: bool = False):
        self.deselect_piece()  # you know, just in case
        self.turn_side = Side.WHITE

        for sprite in self.piece_node.get_children():
            self.piece_node.remove(sprite)

        if new_piece_sets is not None:
            self.piece_sets = new_piece_sets
        elif shuffle:
            self.piece_sets = {side: random.choice(list(piece_groups.keys())) for side in self.piece_sets}

        self.move_history = []

        print(
            f"[{len(self.move_history)}] Starting new game: "
            f"{piece_group_names[self.piece_sets[Side.WHITE]]} vs "
            f"{piece_group_names[self.piece_sets[Side.BLACK]]}"
        )

        piece_sets = {side: piece_groups[self.piece_sets[side]] for side in self.piece_sets}

        if new_piece_sets is not None or shuffle:
            self.promotion_types = {side: [] for side in self.promotion_types}
            for side in self.promotion_types:
                used_piece_set = set()
                for pieces in (piece_sets[side], piece_sets[side.opponent()]):
                    promotion_types = []
                    for piece in pieces:
                        if piece not in used_piece_set and not issubclass(piece, abc.RoyalPiece):
                            used_piece_set.add(piece)
                            promotion_types.append(piece)
                    self.promotion_types[side].extend(promotion_types[::-1])

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
                    promotions=self.promotion_types[piece_side],
                    promotion_tiles=promotion_tiles[piece_side],
                )
                if issubclass(piece_type, abc.PromotablePiece) else
                piece_type(
                    self, (row, col), piece_side
                )
            )
            self.pieces[row][col].color = (255, 255, 255)
            self.pieces[row][col].scale = cell_size / self.pieces[row][col].width
            self.piece_node.add(self.pieces[row][col])

        self.load_all_moves()

    def get_board_position(self, x: float, y: float) -> Position:
        window_width, window_height = director.get_window_size()
        x, y = director.get_virtual_coordinates(x, y)
        col = round((x - window_width / 2) / cell_size + (self.board_width - 1) / 2)
        row = round((y - window_height / 2) / cell_size + (self.board_height - 1) / 2)
        return row, col

    def get_screen_position(self, pos: tuple[float, float]) -> tuple[float, float]:
        window_width, window_height = director.get_window_size()
        row, col = pos
        x = (col - (self.board_width - 1) / 2) * cell_size + window_width / 2
        y = (row - (self.board_height - 1) / 2) * cell_size + window_height / 2
        return x, y

    # From now on we shall unanimously assume that the first coordinate corresponds to row number (AKA vertical axis).
    def get_cell(self, pos: Position) -> Sprite:
        return self.board_sprites[pos[0]][pos[1]]

    def get_piece(self, pos: Position) -> abc.Piece:
        return self.pieces[pos[0]][pos[1]]

    def get_side(self, pos: Position) -> Side:
        return self.get_piece(pos).side

    def not_on_board(self, pos: Position) -> bool:
        return pos[0] < 0 or pos[0] >= self.board_height or pos[1] < 0 or pos[1] >= self.board_width

    def not_a_piece(self, pos: Position | None) -> bool:
        return pos is None or self.not_on_board(pos) or self.get_piece(pos).is_empty()

    def nothing_selected(self) -> bool:
        return self.not_a_piece(self.selected_piece)

    def not_movable(self, pos: Position | None) -> bool:
        return self.not_a_piece(pos) or self.turn_side not in (self.get_piece(pos).side, Side.ANY)

    def find_move(self, pos_from: Position, pos_to: Position) -> Move | None:
        for move in self.moves.get(pos_from, ()):
            if pos_to == move.pos_to:
                return move
        return None

    def select_piece(self, pos: Position) -> None:
        if self.not_on_board(pos):
            return  # there's nothing to select off the board
        if pos == self.selected_piece:
            return  # piece already selected, nothing else to do

        # set selection properties for the selected cell
        self.selected_piece = pos
        self.selection.opacity = selection_opacity
        self.selection.position = self.get_screen_position(pos)

        # move the piece to active piece node (to be displayed on top of everything else)
        piece = self.get_piece(self.selected_piece)
        self.piece_node.remove(piece)
        self.active_piece_node.add(piece)

        for move in self.moves.get(pos, ()):
            move_sprite = Sprite(
                f"assets/util/{'move' if self.not_a_piece(move.pos_to) else 'capture'}.png",
                position=self.get_screen_position(move.pos_to),
                opacity=marker_opacity
            )
            move_sprite.scale = cell_size / move_sprite.width
            self.move_node.add(move_sprite)

    def deselect_piece(self) -> None:
        self.selection.opacity = 0
        self.piece_was_clicked = False

        if self.nothing_selected():
            return

        # move the piece to general piece node
        piece = self.get_piece(self.selected_piece)
        self.active_piece_node.remove(piece)
        self.piece_node.add(piece)

        self.selected_piece = None
        for child in list(self.move_node.get_children()):
            self.move_node.remove(child)

    def on_mouse_press(self, x, y, buttons, modifiers) -> None:
        if buttons & mouse.LEFT:
            if self.game_over:
                return
            pos = self.get_board_position(x, y)
            if self.promotion_piece:
                if pos in self.promotion_area:
                    self.move_history[-1].set(promotion=self.promotion_area[pos])
                    self.replace(self.promotion_piece, self.promotion_area[pos])
                    self.promotion_piece = None
                    self.promotion_area = {}
                    for node in (self.promotion_area_node, self.promotion_piece_node):
                        for sprite in node.get_children():
                            node.remove(sprite)
                    if self.move_history:
                        print(f"[{len(self.move_history)}] {self.move_history[-1]}")
                    self.advance_turn()
                    return
                return
            self.clicked_piece = pos  # we need this in order to discern what are we dragging
            if self.not_movable(pos):
                return
            self.deselect_piece()  # just in case we had something previously selected
            self.select_piece(pos)

    def on_mouse_motion(self, x, y, dx, dy) -> None:
        pos = self.get_board_position(x + dx, y + dy)
        if self.not_on_board(pos):
            self.highlight.opacity = 0
        else:
            self.highlight.opacity = highlight_opacity
            self.highlight.position = self.get_screen_position(pos)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers) -> None:
        self.on_mouse_motion(x, y, dx, dy)  # move the highlight as well!
        if buttons & mouse.LEFT and self.selected_piece is not None and self.clicked_piece == self.selected_piece:
            sprite = self.get_piece(self.selected_piece)
            sprite.x = x
            sprite.y = y

    def on_mouse_release(self, x, y, buttons, modifiers) -> None:
        if buttons & mouse.LEFT:
            if self.game_over:
                self.deselect_piece()
                return
            if self.promotion_piece:
                return
            if self.nothing_selected():
                return
            selected = self.selected_piece
            pos = self.get_board_position(x, y)
            if self.not_on_board(pos):
                if self.piece_was_clicked:
                    self.deselect_piece()
                    return
                pos = selected  # to avoid dragging a piece off the board, place it back on its cell
            move = self.find_move(selected, pos)
            if move is None:
                if self.piece_was_clicked:
                    self.deselect_piece()
                    return
                pos = selected  # is an invalid move has been attempted, do the same
            self.piece_was_clicked = self.clicked_piece == pos
            self.clicked_piece = None
            if move is None:
                self.set_position(self.get_piece(selected), pos)
                return
            self.update_move(move)
            self.get_piece(selected).move(move)
            self.move_history.append(move)
            if not self.promotion_piece and self.move_history:
                print(f"[{len(self.move_history)}] {self.move_history[-1]}")
            self.advance_turn()

    def update_move(self, move: Move) -> None:
        move.set(piece=self.get_piece(move.pos_from))
        captured_piece = self.get_piece(move.pos_to)
        if captured_piece.side != Side.NONE:
            move.set(captured_piece=(self.en_passant_target if captured_piece.is_empty() else captured_piece))

    def set_position(self, piece: abc.Piece, pos: Position) -> None:
        piece.board_pos = pos
        piece.position = self.get_screen_position(pos)

    def move(self, move: Move) -> None:
        self.set_position(move.piece, move.pos_to)
        self.deselect_piece()
        self.piece_node.remove(self.pieces[move.pos_to[0]][move.pos_to[1]])
        self.pieces[move.pos_to[0]][move.pos_to[1]] = move.piece
        self.pieces[move.pos_from[0]][move.pos_from[1]] = util.NoPiece(self, move.pos_from)
        self.piece_node.add(self.pieces[move.pos_from[0]][move.pos_from[1]])
        (move.piece or move).movement.update(move)

    def update(self, move: Move) -> None:
        if self.en_passant_target is not None and move.piece.side == self.en_passant_target.side.opponent():
            if move.pos_to in self.en_passant_markers and isinstance(move.movement, movement.EnPassantMovement):
                self.capture_en_passant()
            else:
                self.clear_en_passant()

    def undo(self, move: Move) -> None:
        self.set_position(move.piece, move.pos_from)
        self.piece_node.remove(self.pieces[move.pos_from[0]][move.pos_from[1]])
        self.piece_node.remove(self.pieces[move.pos_to[0]][move.pos_to[1]])
        self.pieces[move.pos_from[0]][move.pos_from[1]] = move.piece
        self.piece_node.add(move.piece)
        if move.captured_piece is not None:
            if move.captured_piece.board_pos != move.pos_to:
                self.piece_node.remove(self.pieces[move.captured_piece.board_pos[0]][move.captured_piece.board_pos[1]])
            self.set_position(move.captured_piece, move.captured_piece.board_pos)
            self.pieces[move.captured_piece.board_pos[0]][move.captured_piece.board_pos[1]] = move.captured_piece
            self.piece_node.add(move.captured_piece)
        if move.captured_piece is None or move.captured_piece.board_pos != move.pos_to:
            self.pieces[move.pos_to[0]][move.pos_to[1]] = util.NoPiece(self, move.pos_to)
            self.piece_node.add(self.pieces[move.pos_to[0]][move.pos_to[1]])
        (move.piece or move).movement.undo(move)

    def undo_last_move(self) -> None:
        if self.promotion_piece:
            return  # can't undo a move while promoting because the move is not yet complete. please try again later /hj
        if not self.move_history:
            return
        print(f"[{len(self.move_history)}] Undoing last move.")
        last_move = self.move_history.pop()
        self.undo(last_move)
        if self.move_history:
            move = self.move_history[-1]
            (move.piece or move).movement.undo(move)
            (move.piece or move).movement.update(move)
        self.advance_turn()

    def start_promotion(self, piece: abc.Piece) -> None:
        if not isinstance(piece, abc.PromotablePiece) or not piece.promotions:
            return
        self.promotion_piece = piece
        piece_pos = piece.board_pos
        area = len(piece.promotions)
        area_height = max(4, math.ceil(math.sqrt(area)))
        area_width = math.ceil(area / area_height)
        area_origin = piece_pos
        while self.not_on_board((area_origin[0] + piece.side.direction(area_height - 1), area_origin[1])):
            area_origin = add(area_origin, piece.side.direction((-1, 0)))
        area_origin = add(area_origin, piece.side.direction((area_height - 1, 0)))
        area_cells = []
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
            area_cells.append((current_row, current_col))
        for promotion, pos in zip_longest(piece.promotions, area_cells):
            background_sprite = Sprite(
                "assets/util/cell.png", position=self.get_screen_position(pos), color=background_color
            )
            background_sprite.scale = cell_size / background_sprite.width
            self.promotion_area_node.add(background_sprite)
            if promotion is None:
                continue
            promotion_piece = promotion(self, pos, piece.side)
            promotion_piece.scale = cell_size / promotion_piece.width
            self.promotion_piece_node.add(promotion_piece)
            self.promotion_area[pos] = promotion

    def replace(self, piece: abc.Piece, new_type: Type[abc.Piece], new_side: Side | None = None) -> None:
        if new_side is None:
            new_side = piece.side
        pos = piece.board_pos
        self.piece_node.remove(piece)
        self.pieces[pos[0]][pos[1]] = new_type(self, pos, new_side)
        self.pieces[pos[0]][pos[1]].scale = cell_size / self.pieces[pos[0]][pos[1]].width
        self.piece_node.add(self.pieces[pos[0]][pos[1]])
        self.pieces[pos[0]][pos[1]].board_pos = pos

    def color_pieces(self, side: Side = Side.ANY, color: tuple[int, int, int] | None = None, shade: int = 255) -> None:
        for piece in self.movable_pieces.get(side, sum(self.movable_pieces.values(), [])):
            piece.color = color or (shade, ) * 3

    def advance_turn(self) -> None:
        if self.promotion_piece:
            return
        self.turn_side = self.turn_side.opponent()
        self.load_all_moves()
        if sum(self.moves.values(), []):
            self.color_pieces(shade=255)
            self.game_over = False
            if self.check_side != Side.NONE:
                print(f"{self.check_side.name()} is in check!")
        else:
            if self.check_side != Side.NONE:
                self.color_pieces(self.check_side, shade=125)
                self.color_pieces(self.check_side.opponent(), shade=225)
                print(f"Checkmate! {self.check_side.opponent().name()} wins.")
            else:
                self.color_pieces(shade=175)
                print("Stalemate! It's a draw.")
            self.game_over = True

    def load_all_moves(self) -> None:
        self.load_check()
        movable_pieces = {side: self.movable_pieces[side].copy() for side in self.movable_pieces}
        royal_pieces = {side: self.royal_pieces[side].copy() for side in self.royal_pieces}
        quasi_royal_pieces = {side: self.quasi_royal_pieces[side].copy() for side in self.quasi_royal_pieces}
        check_side = self.check_side
        en_passant_target = self.en_passant_target
        en_passant_markers = self.en_passant_markers.copy()
        self.moves = {}
        for piece in movable_pieces[self.turn_side]:
            for move in piece.moves(piece.board_pos):
                self.update_move(move)
                self.move(move)
                self.load_check()
                if self.check_side != self.turn_side:
                    self.moves.setdefault(move.pos_from, []).append(move)
                self.undo(move)
                if en_passant_target is not None:
                    self.en_passant_target = en_passant_target
                    self.en_passant_markers = en_passant_markers.copy()
                    for marker in self.en_passant_markers:
                        self.mark_en_passant(self.en_passant_target.board_pos, marker)
        self.movable_pieces = movable_pieces
        self.royal_pieces = royal_pieces
        self.quasi_royal_pieces = quasi_royal_pieces
        self.check_side = check_side

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
                if isinstance(piece, abc.QuasiRoyalPiece):
                    self.quasi_royal_pieces[piece.side].append(piece)
        for side in (Side.WHITE, Side.BLACK):
            if len(self.quasi_royal_pieces[side]) == 1:
                self.royal_pieces[side].append(self.quasi_royal_pieces[side].pop())

    def load_check(self):
        self.load_pieces()
        self.check_side = Side.NONE
        for royal in self.royal_pieces[self.turn_side]:
            for piece in self.movable_pieces[self.turn_side.opponent()]:
                for move in piece.moves(piece.board_pos):
                    if move.pos_to == royal.board_pos:
                        self.check_side = self.turn_side
                        break
                if self.check_side != Side.NONE:
                    break
            if self.check_side != Side.NONE:
                break

    def mark_en_passant(self, piece_pos: Position, marker_pos: Position) -> None:
        if self.en_passant_target is not None and self.en_passant_target.board_pos != piece_pos:
            return
        self.en_passant_target = self.get_piece(piece_pos)
        self.replace(self.get_piece(marker_pos), util.NoPiece, self.en_passant_target.side)
        self.en_passant_markers.add(marker_pos)

    def capture_en_passant(self) -> None:
        if self.en_passant_target is None:
            return
        self.replace(self.en_passant_target, util.NoPiece, Side.NONE)
        self.clear_en_passant()

    def clear_en_passant(self) -> None:
        self.en_passant_target = None
        for marker in self.en_passant_markers:
            if self.not_a_piece(marker):
                self.replace(self.get_piece(marker), util.NoPiece, Side.NONE)
        self.en_passant_markers = set()

    def on_key_press(self, symbol, modifiers):
        if symbol == key.R:
            if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:
                self.reset_board(new_piece_sets={Side.WHITE: 1, Side.BLACK: 1})
            elif modifiers & key.MOD_ACCEL:
                self.reset_board(shuffle=True)
            else:
                self.reset_board()
            return
        if symbol == key.T and modifiers & key.MOD_ACCEL:
            self.turn_side = Side.ANY
        if symbol == key.W:
            if modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:
                if self.turn_side != Side.WHITE:
                    self.turn_side = Side.WHITE
                    print(f"[{len(self.move_history) + 1}] Passed turn to {self.turn_side.name()}.")
                    self.load_all_moves()
            else:
                direction = -1 if modifiers & key.MOD_ACCEL else 1
                self.piece_sets[Side.WHITE] = (self.piece_sets[Side.WHITE] + direction - 1) % len(piece_groups) + 1
                self.reset_board(new_piece_sets=self.piece_sets)
                return
        if symbol == key.B:
            if modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:
                if self.turn_side != Side.BLACK:
                    self.turn_side = Side.BLACK
                    print(f"[{len(self.move_history) + 1}] Passed turn to {self.turn_side.name()}.")
                    self.load_all_moves()
            else:
                direction = -1 if modifiers & key.MOD_ACCEL else 1
                self.piece_sets[Side.BLACK] = (self.piece_sets[Side.BLACK] + direction - 1) % len(piece_groups) + 1
                self.reset_board(new_piece_sets=self.piece_sets)
                return
        if symbol == key.Z and modifiers & key.MOD_ACCEL:
            self.undo_last_move()
        if self.selected_piece is not None and self.turn_side not in (self.get_side(self.selected_piece), Side.ANY):
            self.deselect_piece()

    def run(self):
        pass

