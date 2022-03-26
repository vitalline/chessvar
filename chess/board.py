from random import sample

from cocos import scene
from cocos.batch import BatchNode
from cocos.director import director
from cocos.layer import ColorLayer
from cocos.sprite import Sprite
from cocos.text import Label

from pyglet.window import key, mouse

from chess.movement import *
from chess.movement.base import *
from chess.piece import Piece, Side, Type

piece_row = [2, 3, 4, 5, 5, 4, 3, 2]
pawn_row = [1] * 8
empty_row = [0] * 8

white_row = [Side.WHITE] * 8
black_row = [Side.BLACK] * 8
neutral_row = [Side.NONE] * 8

types = [piece_row, pawn_row, empty_row, empty_row, empty_row, empty_row, pawn_row, piece_row]
sides = [white_row, white_row, neutral_row, neutral_row, neutral_row, neutral_row, black_row, black_row]

board_width = 8
board_height = 8
cell_size = 50

highlight_color = 255, 255, 204
highlight_opacity = 25
selection_opacity = 50
marker_opacity = 50


movements = []


def get_cell_color(pos: Tuple[int, int]) -> Tuple[int, int, int]:
    if (pos[0] + pos[1]) % 2:
        return 255, 204, 153
    else:
        return 187, 119, 51


def get_royal_color(side: Side) -> Tuple[int, int, int]:
    if side == Side.WHITE:
        return 255, 255, 204
    else:
        return 255, 153, 153


class Board(ColorLayer):

    def __init__(self):
        self.is_event_handler = True
        director.init(width=500, height=500, autoscale=False)
        super().__init__(192, 168, 142, 1000)

        # super boring initialization stuff (bluh bluh)
        self.board_width, self.board_height = board_width, board_height
        self.clicked_piece = None
        self.selected_piece = None
        self.piece_was_clicked = False  # used to discern two-click moving from dragging
        self.turn_side = Side.WHITE
        self.piece_sprites = list()
        self.board_sprites = list()
        self.row_labels = list()
        self.col_labels = list()
        self.moves = list()
        self.board = BatchNode()
        self.highlight = Sprite("assets/util/highlight.png", color=highlight_color, opacity=0)
        self.selection = Sprite("assets/util/selection.png", opacity=0)
        self.pieces = BatchNode()
        self.move_markers = BatchNode()
        self.active_pieces = BatchNode()
        self.add(self.board, z=1)
        self.add(self.highlight, z=2)
        self.add(self.selection, z=2)
        self.add(self.pieces, z=3)
        self.add(self.move_markers, z=3)
        self.add(self.active_pieces, z=4)

        global movements
        movements = get_movements(self)
        # self.movements = [None] + movements[-1:-6:-1]
        self.movements = [None] + sample(movements, 5)
        self.movements[1].directions = balance_pawn(self.movements[1].directions)
        self.types = [Type.NONE] + sample(list(Type.__members__.values())[1:], 5)

        label_kwargs = {
            'font_name': 'Courier New',
            'font_size': 20,
            'bold': True,
            'color': (0, 0, 0, 1000)
        }

        for row in range(self.board_height):
            self.board_sprites += [[]]
            self.piece_sprites += [[]]
            self.row_labels += [
                Label(str(row + 1), self.get_position((row, -0.9)),
                      anchor_x='center', anchor_y='center', **label_kwargs),
                Label(str(row + 1), self.get_position((row, 7.9)),
                      anchor_x='center', anchor_y='center', **label_kwargs),
            ]

        for col in range(self.board_width):
            self.row_labels += [
                Label(chr(col + ord('a')), self.get_position((-0.9, col)),
                      anchor_x='center', anchor_y='center', **label_kwargs),
                Label(chr(col + ord('a')), self.get_position((7.9, col)),
                      anchor_x='center', anchor_y='center', **label_kwargs),
            ]

        for row, col in product(range(self.board_height), range(self.board_width)):

            self.board_sprites[row] += [Sprite("assets/util/cell.png")]
            self.board_sprites[row][col].position = self.get_position((row, col))
            self.board_sprites[row][col].color = get_cell_color((row, col))
            self.board.add(self.board_sprites[row][col])

            self.piece_sprites[row] += [Piece(self,
                                              sides[row][col],
                                              self.types[types[row][col]],
                                              movement=self.movements[types[row][col]])]
            self.piece_sprites[row][col].position = self.get_position((row, col))
            self.piece_sprites[row][col].color = get_royal_color(sides[row][col]) \
                if types[row][col] == 5 else (255, 255, 255)
            self.pieces.add(self.piece_sprites[row][col])

        for label in self.row_labels + self.col_labels:
            self.add(label, z=1)

        director.run(scene.Scene(self))

    def reset_movements(self):
        self.movements = [None] + sample(movements, 5)
        self.movements[1].directions = balance_pawn(self.movements[1].directions)
        self.types = [Type.NONE] + sample(list(Type.__members__.values())[1:], 5)

    def reset_board(self):
        self.deselect_piece()  # you know, just in case
        self.turn_side = Side.WHITE

        for sprite in self.pieces.get_children():
            self.pieces.remove(sprite)

        self.piece_sprites = list()

        for row in range(self.board_height):
            self.piece_sprites += [[]]

        for row, col in product(range(self.board_height), range(self.board_width)):
            self.piece_sprites[row] += [Piece(self,
                                              sides[row][col],
                                              self.types[types[row][col]],
                                              movement=self.movements[types[row][col]])]
            self.piece_sprites[row][col].position = self.get_position((row, col))
            self.piece_sprites[row][col].color = get_royal_color(sides[row][col]) \
                if types[row][col] == 5 else (255, 255, 255)
            self.pieces.add(self.piece_sprites[row][col])

    def get_coordinates(self, x: float, y: float) -> Tuple[int, int]:
        window_width, window_height = director.get_window_size()
        x, y = director.get_virtual_coordinates(x, y)
        col = round((x - window_width / 2) / cell_size + (self.board_width - 1) / 2)
        row = round((y - window_height / 2) / cell_size + (self.board_height - 1) / 2)
        return row, col

    def get_position(self, pos: Tuple[int, int]) -> Tuple[float, float]:
        window_width, window_height = director.get_window_size()
        row, col = pos
        x = (col - (self.board_width - 1) / 2) * cell_size + window_width / 2
        y = (row - (self.board_height - 1) / 2) * cell_size + window_height / 2
        return x, y

    # From now on we shall unanimously assume that the first coordinate corresponds to row number (AKA vertical axis).
    def get_cell(self, pos: Tuple[int, int]) -> Sprite:
        return self.board_sprites[pos[0]][pos[1]]

    def get_piece(self, pos: Tuple[int, int]) -> Piece:
        return self.piece_sprites[pos[0]][pos[1]]

    def get_side(self, pos: Tuple[int, int]) -> Side:
        return self.get_piece(pos).side

    def not_on_board(self, pos: Tuple[int, int]) -> bool:
        return pos[0] < 0 or pos[0] >= self.board_height or pos[1] < 0 or pos[1] >= self.board_width

    def not_a_piece(self, pos: Union[None, Tuple[int, int]]) -> bool:
        return pos is None or self.not_on_board(pos) or self.get_piece(pos).is_empty()

    def nothing_selected(self) -> bool:
        return self.not_a_piece(self.selected_piece)

    def not_movable(self, pos: Union[None, Tuple[int, int]]) -> bool:
        return self.not_a_piece(pos) or self.get_piece(pos).side != self.turn_side

    def find_move(self, pos: Tuple[int, int]) -> Union[None, Move]:
        for move in self.moves:
            if pos == move.pos_to:
                return move
        return None

    def select_piece(self, pos: Tuple[int, int]) -> None:
        if self.not_on_board(pos):
            return  # there's nothing to select off the board
        if pos == self.selected_piece:
            return  # piece already selected, nothing else to do

        # set selection properties for the selected cell
        self.selected_piece = pos
        self.selection.opacity = selection_opacity
        self.selection.position = self.get_position(pos)

        # move the piece to active piece node (to be displayed on top of everything else)
        piece = self.get_piece(self.selected_piece)
        self.pieces.remove(piece)
        self.active_pieces.add(piece)

        self.moves = list()
        for move in piece.moves(pos):
            self.moves.append(move)
            self.move_markers.add(Sprite(f"assets/util/{'move' if self.not_a_piece(move.pos_to) else 'capture'}.png",
                                         position=self.get_position(move.pos_to),
                                         opacity=marker_opacity))

    def deselect_piece(self) -> None:
        self.selection.opacity = 0
        self.piece_was_clicked = False

        if self.nothing_selected():
            return

        # move the piece to general piece node
        piece = self.get_piece(self.selected_piece)
        self.active_pieces.remove(piece)
        self.pieces.add(piece)

        self.selected_piece = None
        self.moves = list()
        for child in list(self.move_markers.get_children()):
            self.move_markers.remove(child)

    def on_mouse_press(self, x, y, buttons, modifiers) -> None:
        if buttons & mouse.LEFT:
            pos = self.get_coordinates(x, y)
            self.clicked_piece = pos  # we need this in order to discern what are we dragging
            if self.not_movable(pos):
                return
            self.deselect_piece()  # just in case we had something previously selected
            self.select_piece(pos)

    def on_mouse_motion(self, x, y, dx, dy) -> None:
        pos = self.get_coordinates(x + dx, y + dy)
        if self.not_on_board(pos):
            self.highlight.opacity = 0
        else:
            self.highlight.opacity = highlight_opacity
            self.highlight.position = self.get_position(pos)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers) -> None:
        self.on_mouse_motion(x, y, dx, dy)  # move the highlight as well!
        if buttons & mouse.LEFT and self.clicked_piece == self.selected_piece:  # if we are dragging the selected piece:
            sprite = self.get_piece(self.selected_piece)
            sprite.x = x
            sprite.y = y

    def on_mouse_release(self, x, y, buttons, modifiers) -> None:
        if buttons & mouse.LEFT:
            if self.nothing_selected():
                return
            selected = self.selected_piece
            pos = self.get_coordinates(x, y)
            if self.not_on_board(pos):
                if self.piece_was_clicked:
                    self.deselect_piece()
                    return
                pos = selected  # to avoid dragging a piece off the board, place them back on their cell
            move = self.find_move(pos)
            if move is None:
                if self.piece_was_clicked:
                    self.deselect_piece()
                    return
                pos = selected  # is an invalid move has been attempted, do the same
            self.piece_was_clicked = self.clicked_piece == pos
            self.clicked_piece = None
            piece = self.get_piece(selected)
            piece.position = self.get_position(pos)  # place the piece on the intended position

            if selected == pos:
                return  # don't remove the selection since the piece wasn't dragged off its cell
            self.deselect_piece()  # remove selection. we have stored the position anyway

            self.pieces.remove(self.piece_sprites[pos[0]][pos[1]])         # remove the piece from the end position
            self.piece_sprites[pos[0]][pos[1]] = piece                     # put the moved piece on the end position
            self.piece_sprites[selected[0]][selected[1]] = Piece(self)     # put an empty piece on the start position
            self.pieces.add(self.piece_sprites[selected[0]][selected[1]])  # and attach it to the piece rendering node

            self.turn_side = self.turn_side.opponent()

    def on_key_press(self, symbol, modifiers):
        if symbol == key.R:
            if modifiers & key.MOD_ACCEL:  # CMD on OSX, CTRL otherwise
                self.reset_movements()
            self.reset_board()

    def run(self):
        pass

