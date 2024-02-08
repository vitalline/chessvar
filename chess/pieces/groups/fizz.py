from math import ceil

from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.pieces import Piece, Side


class LRhino(Piece):
    name = 'Left Rhino'
    file_name = 'KafrK'
    asset_folder = 'fizz'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(*ij, 1)]),
                    movement.RiderMovement(board, [(*kl, 1)])
                ]) for ij, kl in zip(
                    [(1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0)],
                    [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
                )
            ]),
            side == Side.WHITE
        )


class RRhino(Piece):
    name = 'Right Rhino'
    file_name = 'KafrK'
    asset_folder = 'fizz'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(*ij, 1)]),
                    movement.RiderMovement(board, [(*kl, 1)])
                ]) for ij, kl in zip(
                    [(1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0)],
                    [(0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1)]
                )
            ]),
            side == Side.BLACK
        )


class Wyvern(Piece):
    name = 'Wyvern'
    file_name = 'WyafshhW'
    asset_folder = 'fizz'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.HalflingRiderMovement(board, [(i or k, j or k)], 1)
                ]) for i, j in rot([(1, 0)]) for k in (1, -1)
            ])
        )


class Crabinal(Piece):
    name = 'Crabinal'
    file_name = 'ffbsNhhB'
    asset_folder = 'fizz'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.RiderMovement(board, symv([(2, 1, 1), (-1, 2, 1)])),
                movement.HalflingRiderMovement(board, rot([(1, 1)]))
            ])
        )


class EagleScout(Piece):
    name = 'Eagle Scout'
    file_name = 'WzB'
    asset_folder = 'fizz'

    def __init__(self, board, board_pos, side):
        movements = []
        for i, j in [(1, 1), (-1, 1), (-1, -1), (1, -1)]:
            for k, l in [(-i, j), (i, -j)]:
                rider_movements = []
                for m in range(int(ceil(max(board.board_width, board.board_height) / 2))):
                    rider_movements.append(movement.RiderMovement(board, [(i, j, 1)]))
                    rider_movements.append(movement.RiderMovement(board, [(k, l, 1)]))
                movements.append(movement.BentMovement(board, rider_movements))
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [movement.RiderMovement(board, rot([(1, 0, 1)]))] + movements)
        )
