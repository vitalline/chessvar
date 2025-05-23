from chess.movement import types
from chess.movement.util import rot, symv
from chess.pieces.piece import Piece


class LRhino(Piece):
    name = 'Left Rhino'
    file_name = 'KaflK'
    asset_folder = 'fizz'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.SpinMovement(board, [
                types.RiderMovement(board, [(*ij, 1)])
                for ij in [(1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1)]
            ], step_count=2),
            **kwargs
        )


class RRhino(Piece):
    name = 'Right Rhino'
    file_name = 'KafrK'
    asset_folder = 'fizz'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.SpinMovement(board, [
                types.RiderMovement(board, [(*ij, 1)])
                for ij in [(1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0)]
            ], step_count=2),
            **kwargs
        )


class Wyvern(Piece):
    name = 'Wyvern'
    file_name = 'Whh[W-B]'
    asset_folder = 'fizz'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [
                types.BentMovement(board, [
                    types.RiderMovement(board, [(i, j, 1)]),
                    types.HalflingRiderMovement(board, [(i or k, j or k) for k in (1, -1)], 1)
                ]) for i, j in rot([(1, 0)])
            ]),
            **kwargs
        )


class Crabinal(Piece):
    name = 'Crabinal'
    file_name = 'ffbsNhhB'
    asset_folder = 'fizz'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [
                types.RiderMovement(board, symv([(2, 1, 1), (-1, 2, 1)])),
                types.HalflingRiderMovement(board, rot([(1, 1)]))
            ]),
            **kwargs
        )


class EagleScout(Piece):
    name = 'Eagle Scout'
    file_name = 'WzB'
    asset_folder = 'fizz'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [types.RiderMovement(board, rot([(1, 0, 1)]))] + [
                types.RepeatMovement(board, [
                    types.RiderMovement(board, [(i, j, 1), (-i, -j, 1)]),
                    types.RiderMovement(board, [(i, -j, 1), (-i, j, 1)]),
                ]) for i, j in symv([(1, 1)])
            ]),
            **kwargs
        )
