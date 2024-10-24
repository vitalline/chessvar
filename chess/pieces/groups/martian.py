from chess.movement import types
from chess.movement.util import rot
from chess.pieces.piece import Piece


class Padwar(Piece):
    name = 'Padwar'
    file_name = 'WaaW'
    asset_folder = 'martian'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [types.RiderMovement(board, rot([(1, 0, 1)]))] + [
                types.BentMovement(board, [
                    types.RiderMovement(board, [(i, j, 1)]),
                    types.RiderMovement(board, [(k, l, 1)]),
                    types.RiderMovement(board, [
                        (m, n, 1) for m, n in rot([(1, 0)]) if (m, n) != (-i, -j) and (m, n) != (-k, -l)
                    ])
                ], 2) for i, j in rot([(1, 0)]) for k, l in rot([(1, 0)]) if (i, j) != (-k, -l)
            ]),
            **kwargs
        )


class Marker(Piece):
    name = 'Marker'
    file_name = 'avsK'
    asset_folder = 'martian'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [
                types.BentMovement(board, [
                    types.RiderMovement(board, rot([(1, i, 1)])),
                    types.RiderMovement(board, rot([(1, j, 1)]))
                ], 1) for i, j in [(0, 1), (1, 0)]
            ]),
            **kwargs
        )


class Walker(Piece):
    name = 'Walker'
    file_name = 'FaaF'
    asset_folder = 'martian'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [types.RiderMovement(board, rot([(1, 1, 1)]))] + [
                types.BentMovement(board, [
                    types.RiderMovement(board, [(i, j, 1)]),
                    types.RiderMovement(board, [(k, l, 1)]),
                    types.RiderMovement(board, [
                        (m, n, 1) for m, n in rot([(1, 1)]) if (m, n) != (-i, -j) and (m, n) != (-k, -l)
                    ])
                ], 2) for i, j in rot([(1, 1)]) for k, l in rot([(1, 1)]) if (i, j) != (-k, -l)
            ]),
            **kwargs
        )


class Chief(Piece):
    name = 'Chief'
    file_name = 'KnDnNnA'
    asset_folder = 'martian'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [
                types.BentMovement(board, [
                    types.RiderMovement(board, [(i, j, 1)]),
                    types.RiderMovement(board, [(i, j, 1), (i or 1, j or 1, 1), (i or -1, j or -1, 1)])
                ]) for i, j in rot([(1, 0)])
            ] + [
                types.BentMovement(board, [
                    types.RiderMovement(board, [(i, j, 1)]),
                    types.RiderMovement(board, [(i, j, 1), (i, 0, 1), (0, j, 1)])
                ]) for i, j in rot([(1, 1)])
            ]),
            **kwargs
        )
