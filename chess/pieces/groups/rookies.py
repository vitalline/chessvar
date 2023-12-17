from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece


class ShortRook(Piece):
    name = 'Short Rook'
    file_name = 'warden'
    asset_folder = 'restrictors'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 4)]))
        )


class WoodyRook(Piece):
    name = 'Woody Rook'
    file_name = 'woodland_rook'
    asset_folder = 'woodland'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (2, 0, 1)]))
        )


class HalfDuck(Piece):
    name = 'Half Duck'
    file_name = 'zora_knight'
    asset_folder = 'zora'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1, 1), (2, 0, 1), (3, 0, 1)]))
        )


class Chancellor(Piece):
    name = 'Chancellor'
    file_name = 'chancellor'
    asset_folder = 'medieval'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0), (1, 2, 1), (2, 1, 1)]))
        )
