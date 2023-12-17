from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece


class LameDuck(Piece):
    name = 'Lame Duck'
    file_name = 'zora_rook'
    asset_folder = 'zora'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1, 1), (1, 0, 0, 2)]))
        )


class Diamond(Piece):
    name = 'Diamond'
    file_name = 'rhombus'
    asset_folder = 'geometry'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1, 1), (2, 0, 1)]))
        )


class Onyx(Piece):
    name = 'Onyx'
    file_name = 'circles'
    asset_folder = 'geometry'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 0, 2)]))
        )


class Squire(Piece):
    name = 'Squire'
    file_name = 'woodland_queen'
    asset_folder = 'woodland'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 0, 2), (1, 1, 0, 2), (1, 2, 1), (2, 1, 1)]))
        )
