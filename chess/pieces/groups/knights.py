from chess.movement import movement
from chess.movement.util import sym, symv
from chess.pieces.pieces import Piece


class ChargeRook(Piece):
    name = 'Charging Rook'
    file_name = 'overlord'
    asset_folder = 'medieval'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(1, 0), (0, 1), (-1, 0, 1), (-1, 1, 1)]))
        )


class Fibnif(Piece):
    name = 'Fibnif'
    file_name = 'two_headed_knight'
    asset_folder = 'fantasy'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, sym([(1, 1, 1), (2, 1, 1)]))
        )


class ChargeKnight(Piece):
    name = 'Charging Knight'
    file_name = 'mare'
    asset_folder = 'nature'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(2, 1, 1), (1, 2, 1), (0, 1, 1), (-1, 0, 1), (-1, 1, 1)]))
        )


class Colonel(Piece):
    name = 'Colonel'
    file_name = 'centaur_rook'
    asset_folder = 'centaur'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(
                board, sym([(1, 1, 1)]) + symv([(2, 1, 1), (1, 2, 1), (1, 0), (0, 1), (-1, 0, 1), (-1, 1, 1)])
            )
        )
