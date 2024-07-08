from math import ceil

from chess.movement import movement
from chess.movement.util import rot, sym, symh, symv
from chess.pieces.pieces import Piece


class Ogre(Piece):
    name = 'Ogre'
    file_name = 'vNvWsR'
    asset_folder = 'wide'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, sym([(0, 1), (1, 0, 1), (2, 1, 1)])),
            **kwargs
        )


class Sidesail(Piece):
    name = 'Sidesail'
    file_name = 'mpvyasWafsF'
    asset_folder = 'wide'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i or k, j or k, 1)]),
                    movement.RiderMovement(board, [(i, j)])
                ]) for i, j in symv([(0, 1)]) for k in (1, -1)
            ] + [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i or k, j or k, 1)]),
                    movement.RiderMovement(board, [(i, j, 1)])
                ]) for i, j in symh([(1, 0)]) for k in (1, -1)
            ]),
            **kwargs
        )


class Sidewinder(Piece):
    name = 'Sidewinder'
    file_name = 'Fmpvasafq(az)WvD'
    asset_folder = 'wide'
    colorbound = True

    def __init__(self, board, board_pos, side, **kwargs):
        movements = [movement.RiderMovement(board, symh([(2, 0, 1)]))]
        for i, j in rot([(1, 1)]):
            rider_movements = []
            for m in range(int(ceil(max(board.board_width, board.board_height) / 2))):
                rider_movements.append(movement.RiderMovement(board, [(i, j, 1)]))
                rider_movements.append(movement.RiderMovement(board, [(-i, j, 1)]))
            movements.append(movement.BentMovement(board, rider_movements))
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, movements),
            **kwargs
        )


class Ogress(Piece):
    name = 'Ogress'
    file_name = 'NKsR'
    asset_folder = 'wide'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, sym([(0, 1), (1, 0, 1), (1, 1, 1), (1, 2, 1), (2, 1, 1)])),
            **kwargs
        )
