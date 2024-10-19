from chess.movement import movement
from chess.movement.util import rot, sym, symh, symv
from chess.pieces.piece import Piece


class Ogre(Piece):
    name = 'Ogre'
    file_name = 'vNvWsR'
    asset_folder = 'wide'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.RiderMovement(board, sym([(0, 1), (1, 0, 1), (2, 1, 1)])),
            **kwargs
        )


class Sidesail(Piece):
    name = 'Sidesail'
    file_name = 'mpvyasWafsF'
    asset_folder = 'wide'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i or k, j or k, 1) for k in (1, -1)]),
                    movement.RiderMovement(board, [(i, j)])
                ]) for i, j in symv([(0, 1)])
            ] + [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i or k, j or k, 1) for k in (1, -1)]),
                    movement.RiderMovement(board, [(i, j, 1)])
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
            movement.MultiMovement(board, [movement.RiderMovement(board, symh([(2, 0, 1)]))] + [
                movement.RepeatMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(-i, j, 1)])
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
            movement.RiderMovement(board, sym([(0, 1), (1, 0, 1), (1, 1, 1), (1, 2, 1), (2, 1, 1)])),
            **kwargs
        )
