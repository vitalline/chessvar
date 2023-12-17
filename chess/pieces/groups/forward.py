from chess.movement import movement
from chess.movement.util import symv
from chess.pieces.pieces import Piece


class Knishop(Piece):
    name = 'Knishop'
    file_name = 'jester'
    asset_folder = 'medieval'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(1, 2, 1), (2, 1, 1), (-1, 1)]))
        )


class Bishight(Piece):
    name = 'Bishight'
    file_name = 'priest'
    asset_folder = 'medieval'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(-1, 2, 1), (-2, 1, 1), (1, 1)]))
        )


class Forequeen(Piece):
    name = 'Forequeen'
    file_name = 'pasha'
    asset_folder = 'medieval'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(
                board, symv([(1, 0), (1, 1), (0, 1), (-1, 0, 1), (-1, 1, 1), (-1, 2, 1), (-2, 1, 1)])
            )
        )
