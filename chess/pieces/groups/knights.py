from chess.movement import movement
from chess.movement.util import sym, symv
from chess.pieces import pieces


class ChargeRook(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Charging Rook',
            file_name=f'{side.file_name()}_rook',
            asset_folder='classic',
            movement=movement.RiderMovement(board, symv([(1, 0), (0, 1), (-1, 0, 1), (-1, 1, 1)]))
        )


class Fibnif(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Fibnif',
            file_name=f'{side.file_name()}_knight',
            asset_folder='classic',
            movement=movement.RiderMovement(board, sym([(1, 1, 1), (2, 1, 1)]))
        )


class ChargeKnight(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Charging Knight',
            file_name=f'{side.file_name()}_bishop',
            asset_folder='classic',
            movement=movement.RiderMovement(board, symv([(2, 1, 1), (1, 2, 1), (0, 1, 1), (-1, 0, 1), (-1, 1, 1)]))
        )


class Colonel(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Colonel',
            file_name=f'{side.file_name()}_queen',
            asset_folder='classic',
            movement=movement.RiderMovement(
                board, sym([(1, 1, 1)]) + symv([(2, 1, 1), (1, 2, 1), (1, 0), (0, 1), (-1, 0, 1), (-1, 1, 1)])
            )
        )