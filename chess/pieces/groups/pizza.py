from chess.movement import movement
from chess.movement.util import rot, sym, symv
from chess.pieces import pieces


class Pepperoni(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Pepperoni',
            file_name=f'{side.file_name()}_circle',
            asset_folder='geometry',
            movement=movement.RiderMovement(board, symv([(2, 2, 1)]) + sym([(0, 2, 1), (1, 1, 1), (1, 0, 1)]))
        )


class Mushroom(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Mushroom',
            file_name=f'{side.file_name()}_mushroom',
            asset_folder='nature',
            movement=movement.RiderMovement(board, symv([(2, 1, 1), (1, 3, 1), (-1, 1, 1), (-2, 1, 1)]))
        )


class Sausage(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Sausage',
            file_name=f'{side.file_name()}_courier_runner',
            asset_folder='courier',
            movement=movement.RiderMovement(board, sym([(3, 0, 1), (2, 1, 1), (1, 1, 1), (0, 1, 1)]))
        )


class Meatball(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Meatball',
            file_name=f'{side.file_name()}_courier_rook',
            asset_folder='courier',
            movement=movement.RiderMovement(
                board, symv([(2, 1, 1)]) + rot([(1, 0, 1), (1, 1, 1), (2, 0, 1), (2, 2, 1)])
            )
        )
