from chess.movement import types
from chess.movement.util import rot, symv
from chess.pieces.piece import Piece


class Star(Piece):
    name = 'Star'
    file_name = 'sfRbB'
    asset_folder = 'starbound'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, symv([(1, 0), (0, 1), (-1, 1)])),
            **kwargs
        )


class Lancer(Piece):
    name = 'Lancer'
    file_name = 'KfR'
    asset_folder = 'starbound'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, symv([(1, 0), (1, 1, 1), (0, 1, 1), (-1, 1, 1), (-1, 0, 1)])),
            **kwargs
        )


class SineRdr(Piece):
    name = 'Sinerider'
    file_name = 'fFmfafFfafmFmfaqFfaqmFsRbB'
    asset_folder = 'starbound'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [types.RiderMovement(board, symv([(0, 1), (-1, 1)]))] + [
                types.BentMovement(board, [
                    types.RiderMovement(board, symv([(1, 1, 1)])) for _ in range(2)
                ])
            ] + [
                types.ChainMovement(board, [
                    types.MultiMovement(board, capture=[
                        types.RiderMovement(board, symv([(1, 1, 1)]))
                    ]),
                    types.MultiMovement(board, move=[
                        types.RiderMovement(board, symv([(1, 1, 1)]) + [(0, 0)])
                    ])
                ])
            ]),
            **kwargs
        )


class Turneagle(Piece):
    name = 'Turneagle'
    file_name = 'FmcaFR'
    asset_folder = 'starbound'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [types.RiderMovement(board, rot([(1, 0)]))] + [
                types.BentMovement(board, [
                    types.RiderMovement(board, [(i, j, 1)]),
                    types.RiderMovement(board, [(k, l, 1) for k, l in rot([(1, 1)]) if (i, j) != (-k, -l)])
                ]) for i, j in rot([(1, 1)])
            ] + [
                types.ChainMovement(board, [
                    types.MultiMovement(board, capture=[
                        types.RiderMovement(board, [(i, j, 1)])
                    ]),
                    types.MultiMovement(board, both=[
                        types.RiderMovement(board, [
                            (k, l, 1) for k, l in rot([(1, 1)]) + [(0, 0)] if (i, j) != (-k, -l)
                        ])
                    ])
                ]) for i, j in rot([(1, 1)])
            ]),
            **kwargs
        )
