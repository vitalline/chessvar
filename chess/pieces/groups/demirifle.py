from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.pieces import Piece


class Snail(Piece):
    name = 'Snail'
    file_name = 'mccWmccfD'
    asset_folder = 'demirifle'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.AutoRangedAutoCaptureRiderMovement(board, rot([(1, 0, 1)]) + [(2, 0, 1)])
        )


class Crab(Piece):
    name = 'Crab'
    file_name = 'mccffbsN'
    asset_folder = 'demirifle'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.AutoRangedAutoCaptureRiderMovement(board, symv([(2, 1, 1), (-1, 2, 1)]))
        )


class Lobster(Piece):
    name = 'Lobster'
    file_name = 'mccfAmccbF'
    asset_folder = 'demirifle'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.AutoRangedAutoCaptureRiderMovement(board, symv([(2, 2, 1), (-1, 1, 1)]))
        )


class Crabsnail(Piece):
    name = 'Crabsnail'
    file_name = 'mccWmccfDmccffbsN'
    asset_folder = 'demirifle'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.AutoRangedAutoCaptureRiderMovement(
                board, symv([(2, 0, 1), (2, 1, 1), (-1, 2, 1)]) + rot([(1, 0, 1)])
            )
        )
