from math import ceil

from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece


class LionCub(Piece):
    name = 'Lion Cub'
    file_name = 'WmaWamW'
    asset_folder = 'crook'

    def __init__(self, board, board_pos, side):
        movements = []
        for i, j in rot([(1, 0)]):
            movements.append(
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [
                        (k, l, 1) for k, l in rot([(1, 0)]) if (i, j) != (-k, -l)
                    ])
                ])
            )
            movements.append(
                movement.ChainMovement(board, [
                    movement.MultiMovement(board, capture=[
                        movement.RiderMovement(board, [(i, j, 1)])
                    ]),
                    movement.MultiMovement(board, move=[
                        movement.RiderMovement(board, [
                            (k, l, 1) for k, l in rot([(1, 0)]) + [(0, 0)] if (i, j) != (-k, -l)
                        ])
                    ])
                ])
            )
        super().__init__(board, board_pos, side, movement.MultiMovement(board, movements))


class Rhino(Piece):
    name = 'Rhino'
    file_name = 'WafsW'
    asset_folder = 'crook'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(i or k, j or k, 1)])
                ]) for i, j in rot([(1, 0)]) for k in (1, -1)
            ])
        )


class Boyscout(Piece):
    name = 'Boyscout'
    file_name = 'zB'
    asset_folder = 'crook'
    colorbound = True

    def __init__(self, board, board_pos, side):
        movements = []
        for i, j in rot([(1, 1)]):
            for k, l in [(-i, j), (i, -j)]:
                rider_movements = []
                for m in range(int(ceil(max(board.board_width, board.board_height) / 2))):
                    rider_movements.append(movement.RiderMovement(board, [(i, j, 1)]))
                    rider_movements.append(movement.RiderMovement(board, [(k, l, 1)]))
                movements.append(movement.BentMovement(board, rider_movements))
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, movements)
        )


class Griffon(Piece):
    name = 'Griffon'
    file_name = 'FyafsF'
    asset_folder = 'crook'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i or k, j or k, 1)]),
                    movement.RiderMovement(board, [(i, j)])
                ]) for i, j in rot([(1, 0)]) for k in (1, -1)
            ])
        )
