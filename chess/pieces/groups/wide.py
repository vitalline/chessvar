from chess.movement import types
from chess.movement.util import rot, sym, symh, symv
from chess.pieces.piece import Piece


class Ogre(Piece):
    name = 'Ogre'
    file_name = 'vNvWsR'
    asset_folder = 'wide'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, sym([(0, 1), (1, 0, 1), (2, 1, 1)])),
            **kwargs
        )


class Sidesail(Piece):
    name = 'Sidesail'
    file_name = 'mpvyasWafsF'
    asset_folder = 'wide'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [
                types.BentMovement(board, [
                    types.RiderMovement(board, [(i or k, j or k, 1) for k in (1, -1)]),
                    types.RiderMovement(board, [(i, j)])
                ]) for i, j in symv([(0, 1)])
            ] + [
                types.BentMovement(board, [
                    types.RiderMovement(board, [(i or k, j or k, 1) for k in (1, -1)]),
                    types.RiderMovement(board, [(i, j, 1)])
                ]) for i, j in symh([(1, 0)])
            ]),
            **kwargs
        )


class Sidewinder(Piece):
    name = 'Sidewinder'
    file_name = 'Fmpvasafq(az)WvD'
    asset_folder = 'wide'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [types.RiderMovement(board, symh([(2, 0, 1)]))] + [
                types.RepeatMovement(board, [
                    types.RiderMovement(board, [(i, j, 1)]),
                    types.RiderMovement(board, [(-i, j, 1)])
                ]) for i, j in rot([(1, 1)])
            ]),
            **kwargs
        )


class Ogress(Piece):
    name = 'Ogress'
    file_name = 'NKsR'
    asset_folder = 'wide'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, sym([(0, 1), (1, 0, 1), (1, 1, 1), (1, 2, 1), (2, 1, 1)])),
            **kwargs
        )
