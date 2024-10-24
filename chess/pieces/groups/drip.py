from chess.movement import types
from chess.movement.util import rot, symv
from chess.pieces.piece import Piece


class Lobefin(Piece):
    name = 'Lobefin'
    file_name = 'DfAAbB'
    asset_folder = 'drip'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(2, 0, 1)]) + symv([(2, 2), (-1, 1)])),
            **kwargs
        )


class CrabRdr(Piece):
    name = 'Crabrider'
    file_name = 'ffbsNN'
    asset_folder = 'drip'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, symv([(2, 1), (-1, 2)])),
            **kwargs
        )


class Sandbar(Piece):
    name = 'Sandbar'
    file_name = 'WfDfsbbNN'
    asset_folder = 'drip'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, symv([(1, 2), (-2, 1)]) + rot([(1, 0, 1)]) + [(2, 0, 1)]),
            **kwargs
        )


class Oyster(Piece):
    name = 'Oyster'
    file_name = 'WfDffbsNNfAAbB'
    asset_folder = 'drip'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, symv([(2, 1), (2, 2), (-1, 1), (-1, 2)]) + rot([(1, 0, 1)]) + [(2, 0, 1)]),
            **kwargs
        )
