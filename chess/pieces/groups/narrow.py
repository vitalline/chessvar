from math import ceil

from chess.movement import movement
from chess.movement.util import rot, symh, symv
from chess.pieces.pieces import Piece


class Deerfly(Piece):
    name = 'Deerfly'
    file_name = 'vRK'
    asset_folder = 'narrow'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1)]) + symh([(1, 0)]))
        )


class Ship(Piece):
    name = 'Ship'
    file_name = 'mpsyasW'
    asset_folder = 'narrow'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i or k, j or k, 1)]),
                    movement.RiderMovement(board, [(i, j)])
                ]) for i, j in symh([(1, 0)]) for k in (1, -1)
            ])
        )


class Filescout(Piece):
    name = 'Filescout'
    file_name = 'Fmpsasafq(az)WsD'
    asset_folder = 'narrow'

    def __init__(self, board, board_pos, side):
        movements = [movement.RiderMovement(board, symv([(0, 2, 1)]))]
        for i, j in rot([(1, 1)]):
            rider_movements = []
            for m in range(int(ceil(max(board.board_width, board.board_height) / 2))):
                rider_movements.append(movement.RiderMovement(board, [(i, j, 1)]))
                rider_movements.append(movement.RiderMovement(board, [(i, -j, 1)]))
            movements.append(movement.BentMovement(board, rider_movements))
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, movements)
        )


class Horsefly(Piece):
    name = 'Horsefly'
    file_name = 'vRNK'
    asset_folder = 'narrow'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1), (1, 2, 1), (2, 1, 1)]) + symh([(1, 0)]))
        )
