from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.piece import Piece


class Fork(Piece):
    name = 'Fork'
    file_name = 'R4'
    asset_folder = 'rookie'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 4)])),
            **kwargs
        )


class Woodrook(Piece):
    name = 'Woodrook'
    file_name = 'WD'
    asset_folder = 'rookie'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (2, 0, 1)])),
            **kwargs
        )


class Dove(Piece):
    name = 'Dove'
    file_name = 'HFD'
    asset_folder = 'rookie'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1, 1), (2, 0, 1), (3, 0, 1)])),
            **kwargs
        )


class Chancellor(Piece):
    name = 'Chancellor'
    file_name = 'RN'
    asset_folder = 'rookie'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0), (1, 2, 1), (2, 1, 1)])),
            **kwargs
        )
