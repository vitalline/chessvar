from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.pieces import Piece


class Snail(Piece):
    name = 'Snail'
    file_name = 'mWmfDcabWcfabD'
    asset_folder = 'demirifle'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RangedCaptureRiderMovement(board, rot([(1, 0, 1)]) + [(2, 0, 1)])
        )


class Crab(Piece):
    name = 'Crab'
    file_name = 'mffbsNcffbsabN'
    asset_folder = 'demirifle'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RangedCaptureRiderMovement(board, symv([(2, 1, 1), (-1, 2, 1)]))
        )


class Lobster(Piece):
    name = 'Lobster'
    file_name = 'mfAmbFcfabAcbabF'
    asset_folder = 'demirifle'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RangedCaptureRiderMovement(board, symv([(2, 2, 1), (-1, 1, 1)]))
        )


class Crabsnail(Piece):
    name = 'Crabsnail'
    file_name = 'mWmfDmffbsNcabWcfabDcffbsabN'
    asset_folder = 'demirifle'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RangedCaptureRiderMovement(board, symv([(2, 1, 1), (-1, 2, 1)]) + rot([(1, 0, 1)]) + [(2, 0, 1)])
        )
