from chess.movement import movement
from chess.movement.util import rot
from chess.pieces import pieces


class Forfer(pieces.Piece):
    name = 'Forfer'
    file_name = 'fortress'
    asset_folder = 'medieval'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1, 1), (1, 0, 4)]))
        )


class B4nD(pieces.Piece):
    name = 'B4nD'
    file_name = 'pylon'
    asset_folder = 'fantasy'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1, 4), (1, 0, 2, 2)]))
        )


class N2R4(pieces.Piece):
    name = 'N2R4'
    file_name = 'sun'
    asset_folder = 'helios'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 4), (1, 2, 2), (2, 1, 2)]))
        )
