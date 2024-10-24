from chess.movement import types
from chess.movement.util import rot, sym, symh, symv
from chess.pieces.piece import Piece


class Mosquito(Piece):
    name = 'Mosquito'
    file_name = 'WvNsDD'
    asset_folder = 'buzz'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0, 1)]) + sym([(2, 1, 1), (0, 2)])),
            **kwargs
        )


class Dragonfly(Piece):
    name = 'Dragonfly'
    file_name = 'vRsN'
    asset_folder = 'buzz'
    colorbound = True  # ...well yes, but actually no.
    # this piece is filebound, not colorbound. but it still needs a (0, ±2) step for castling if it's replacing the rook
    # setting "colorbound = True" will make the piece behave like a colorbound piece for castling and nothing else (yet)

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, sym([(1, 0), (1, 2, 1)])),
            **kwargs
        )


class Locust(Piece):
    name = 'Locust'
    file_name = 'vWvDDsNN'
    asset_folder = 'buzz'
    colorbound = True  # same as the above, the piece is filebound (not colorbound), but needs a (0, ±2) step regardless

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, sym([(1, 0, 1), (2, 0), (1, 2)])),
            **kwargs
        )


class Mantis(Piece):
    name = 'Mantis'
    file_name = 'BvNsD[sD-sR]'
    asset_folder = 'buzz'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [types.RiderMovement(board, sym([(1, 1), (2, 1, 1)]))] + [
                types.BentMovement(board, [
                    types.RiderMovement(board, [(i, j, 1)]),
                    types.RiderMovement(board, [(k, l) for k, l in symh([(1, 0)])])
                ]) for i, j in symv([(0, 2)])
            ]),
            **kwargs
        )
