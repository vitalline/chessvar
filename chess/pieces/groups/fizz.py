from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.piece import Piece


class LRhino(Piece):
    name = 'Left Rhino'
    file_name = 'KaflK'
    asset_folder = 'fizz'

    def __init__(self, board, board_pos, side, **kwargs):
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
            **kwargs
        )


class RRhino(Piece):
    name = 'Right Rhino'
    file_name = 'KafrK'
    asset_folder = 'fizz'

    def __init__(self, board, board_pos, side, **kwargs):
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
            **kwargs
        )


class Wyvern(Piece):
    name = 'Wyvern'
    file_name = 'WhhyafsW'
    asset_folder = 'fizz'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.HalflingRiderMovement(board, [(i or k, j or k)], 1)
                ]) for i, j in rot([(1, 0)]) for k in (1, -1)
            ]),
            **kwargs
        )


class Crabinal(Piece):
    name = 'Crabinal'
    file_name = 'ffbsNhhB'
    asset_folder = 'fizz'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.RiderMovement(board, symv([(2, 1, 1), (-1, 2, 1)])),
                movement.HalflingRiderMovement(board, rot([(1, 1)]))
            ]),
            **kwargs
        )


class EagleScout(Piece):
    name = 'Eagle Scout'
    file_name = 'WzB'
    asset_folder = 'fizz'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [movement.RiderMovement(board, rot([(1, 0, 1)]))] + [
                movement.RepeatMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(k, l, 1)])
                ]) for i, j in rot([(1, 1)]) for k, l in [(-i, j), (i, -j)]
            ]),
            **kwargs
        )
