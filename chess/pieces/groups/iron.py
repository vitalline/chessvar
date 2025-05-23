from chess.movement import types
from chess.movement.util import rot, symv
from chess.pieces.piece import Piece


class Musth(Piece):
    name = 'Musth'
    file_name = 'FAfsW'
    asset_folder = 'iron'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 1, 1), (2, 2, 1)]) + symv([(0, 1, 1)]) + [(1, 0, 1)]),
            **kwargs
        )


class Officer(Piece):
    name = 'Officer'
    file_name = 'vNvWfF'
    asset_folder = 'iron'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, symv([(1, 0, 1), (1, 1, 1), (-1, 0, 1), (2, 1, 1), (-2, 1, 1)])),
            **kwargs
        )


class SilverRdr(Piece):
    name = 'Silverrider'
    file_name = 'BfR'
    asset_folder = 'iron'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 1)]) + [(1, 0)]),
            **kwargs
        )


class GoldRdr(Piece):
    name = 'Goldrider'
    file_name = 'RfB'
    asset_folder = 'iron'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0)]) + symv([(1, 1)])),
            **kwargs
        )
