from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.piece import Piece


class Snail(Piece):
    name = 'Snail'
    file_name = 'mccWmccfD'
    asset_folder = 'demirifle'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.AutoRangedAutoCaptureRiderMovement(board, rot([(1, 0, 1)]) + [(2, 0, 1)]),
            **kwargs
        )


class Crab(Piece):
    name = 'Crab'
    file_name = 'mccffbsN'
    asset_folder = 'demirifle'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.AutoRangedAutoCaptureRiderMovement(board, symv([(2, 1, 1), (-1, 2, 1)])),
            **kwargs
        )


class Lobster(Piece):
    name = 'Lobster'
    file_name = 'mccfAmccbF'
    asset_folder = 'demirifle'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.AutoRangedAutoCaptureRiderMovement(board, symv([(2, 2, 1), (-1, 1, 1)])),
            **kwargs
        )


class Crabsnail(Piece):
    name = 'Crabsnail'
    file_name = 'mccWmccfDmccffbsN'
    asset_folder = 'demirifle'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.AutoRangedAutoCaptureRiderMovement(
                board, symv([(2, 0, 1), (2, 1, 1), (-1, 2, 1)]) + rot([(1, 0, 1)])
            ),
            **kwargs
        )
