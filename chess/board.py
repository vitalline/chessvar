from itertools import product
from typing import Type

from cocos import scene
from cocos.batch import BatchNode
from cocos.director import director
from cocos.layer import ColorLayer
from cocos.sprite import Sprite
from cocos.text import Label

from pyglet.window import key, mouse

from chess.movement.base import RiderMovement
from chess.movement.move import Move
from chess.movement.util import Position, add
from chess.pieces.piece import Piece, Side, PromotablePiece
from chess.pieces.groups.classic import Bishop, King, Knight, Pawn, Queen, Rook
from chess.pieces.util.none import NoPiece

board_width = 8
board_height = 8

piece_row = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
pawn_row = [Pawn] * board_width
empty_row = [NoPiece] * board_width

white_row = [Side.WHITE] * board_width
black_row = [Side.BLACK] * board_width
neutral_row = [Side.NONE] * board_width

types = [piece_row, pawn_row] + [empty_row] * (board_height - 4) + [pawn_row, piece_row]
sides = [white_row, white_row] + [neutral_row] * (board_height - 4) + [black_row, black_row]

promotions = [Rook, Knight, Bishop, Queen]
white_promotion_tiles = [(board_height - 1, i) for i in range(board_width)]
black_promotion_tiles = [(0, i) for i in range(board_width)]
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
        director.init(width=(board_width+2)*cell_size,
                      height=(board_height+2)*cell_size,
                      caption='Chess', autoscale=False)
        super().__init__(192, 168, 142, 1000)
        director.window.remove_handlers(director._default_event_handler)

        # super boring initialization stuff (bluh bluh)
        self.board_width, self.board_height = board_width, board_height
        self.clicked_piece = None
        self.selected_piece = None
        self.piece_was_clicked = False  # used to discern two-click moving from dragging
        self.promotion_piece = None
        self.promotion_area = {}
        self.turn_side = Side.WHITE
        self.pieces = list()
        self.board_sprites = list()
        self.row_labels = list()
        self.col_labels = list()
        self.move_sprites = list()
        self.no_moves = RiderMovement(self, [])
        self.board = BatchNode()
        self.highlight = Sprite("assets/util/highlight.png", color=highlight_color, opacity=0)
        self.selection = Sprite("assets/util/selection.png", opacity=0)
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
            'font_size': 20,
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

            self.board_sprites[row] += [Sprite("assets/util/cell.png")]
            self.board_sprites[row][col].position = self.get_screen_position((row, col))
            self.board_sprites[row][col].color = get_cell_color((row, col))
            self.board.add(self.board_sprites[row][col])

        for label in self.row_labels + self.col_labels:
            self.add(label, z=1)

        self.shuffle()
        self.set_board()

        director.run(scene.Scene(self))

    def shuffle(self):
        pass

    def reset_board(self):
        self.deselect_piece()  # you know, just in case
        self.turn_side = Side.WHITE

        for sprite in self.piece_node.get_children():
            self.piece_node.remove(sprite)

        self.set_board()

    def set_board(self):
        self.pieces = list()

        for row in range(self.board_height):
            self.pieces += [[]]

        for row, col in product(range(self.board_height), range(self.board_width)):
            self.pieces[row] += [
                types[row][col](self, (row, col), sides[row][col], promotions, promotion_tiles[sides[row][col]])
                if issubclass(types[row][col], PromotablePiece) else types[row][col](self, (row, col), sides[row][col])
            ]
            self.pieces[row][col].color = (255, 255, 255)
            self.piece_node.add(self.pieces[row][col])

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

    def get_piece(self, pos: Position) -> Piece:
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

    def find_move(self, pos: Position) -> Move | None:
        for move in self.move_sprites:
            if pos == move.pos_to:
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

        self.move_sprites = list()
        for move in piece.moves(pos):
            self.move_sprites.append(move)
            self.move_node.add(Sprite(f"assets/util/{'move' if self.not_a_piece(move.pos_to) else 'capture'}.png",
                                      position=self.get_screen_position(move.pos_to),
                                      opacity=marker_opacity))

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
        self.move_sprites = list()
        for child in list(self.move_node.get_children()):
            self.move_node.remove(child)

    def on_mouse_press(self, x, y, buttons, modifiers) -> None:
        if buttons & mouse.LEFT:
            pos = self.get_board_position(x, y)
            if self.promotion_piece:
                if pos in self.promotion_area:
                    self.promote_to(self.promotion_area[pos])
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
        if buttons & mouse.LEFT and self.clicked_piece == self.selected_piece:  # if we are dragging the selected piece:
            sprite = self.get_piece(self.selected_piece)
            sprite.x = x
            sprite.y = y

    def on_mouse_release(self, x, y, buttons, modifiers) -> None:
        if buttons & mouse.LEFT:
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
            move = self.find_move(pos)
            if move is None:
                if self.piece_was_clicked:
                    self.deselect_piece()
                    return
                pos = selected  # is an invalid move has been attempted, do the same
            self.piece_was_clicked = self.clicked_piece == pos
            self.clicked_piece = None

            if self.get_piece(selected).move(pos):
                self.advance_turn()

    def move(self, piece: Piece, pos_to: Position) -> bool:
        pos_from = piece.board_pos
        piece.board_pos = pos_to
        piece.position = self.get_screen_position(pos_to)
        if pos_from == pos_to:
            return False
        self.deselect_piece()
        self.piece_node.remove(self.pieces[pos_to[0]][pos_to[1]])         # remove the piece from the end position
        self.pieces[pos_to[0]][pos_to[1]] = piece                         # put the moved piece on the end position
        self.pieces[pos_from[0]][pos_from[1]] = NoPiece(self, pos_from)   # put an empty piece on the start position
        self.piece_node.add(self.pieces[pos_from[0]][pos_from[1]])        # and attach it to the piece rendering node
        return True

    def start_promotion(self, piece: Piece) -> None:
        if not isinstance(piece, PromotablePiece):
            return
        self.promotion_piece = piece
        piece_pos = piece.board_pos
        pos = piece_pos
        for promotion in piece.promotions:
            self.promotion_area_node.add(
                Sprite("assets/util/cell.png", position=self.get_screen_position(pos), color=background_color)
            )
            self.promotion_piece_node.add(promotion(self, pos, piece.side))
            self.promotion_area[pos] = promotion
            pos = add(pos, piece.side.direction((-1, 0)))
            if self.not_on_board(pos):
                pos = add(pos, piece.side.direction((-board_height, 0)))
                pos = add(pos, piece.side.direction((-1, 0))[::-1])
                if self.not_on_board(pos):
                    pos = add(pos, piece.side.direction((-board_width, 0))[::-1])

    def promote_to(self, promotion: Type[Piece]) -> None:
        if self.promotion_piece is None:
            return
        pos = self.promotion_piece.board_pos

        self.piece_node.remove(self.promotion_piece)
        self.pieces[pos[0]][pos[1]] = promotion(self, pos, self.promotion_piece.side)
        self.piece_node.add(self.pieces[pos[0]][pos[1]])
        self.pieces[pos[0]][pos[1]].board_pos = pos

        self.promotion_piece = None
        self.promotion_area = {}
        for node in (self.promotion_area_node, self.promotion_piece_node):
            for sprite in node.get_children():
                node.remove(sprite)

    def advance_turn(self) -> None:
        self.turn_side = self.turn_side.opponent()

    def on_key_press(self, symbol, modifiers):
        if symbol == key.R:
            if modifiers & key.MOD_ACCEL:  # CMD on OSX, CTRL otherwise
                self.shuffle()
            self.reset_board()
            return
        if symbol == key.T and modifiers & key.MOD_ACCEL:
            self.turn_side = Side.ANY
        if symbol == key.W and modifiers & key.MOD_ACCEL:
            self.turn_side = Side.WHITE
        if symbol == key.B and modifiers & key.MOD_ACCEL:
            self.turn_side = Side.BLACK
        if self.selected_piece is not None and self.turn_side not in (self.get_side(self.selected_piece), Side.ANY):
            self.deselect_piece()

    def run(self):
        pass

