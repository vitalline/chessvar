from chess.movement import types
from chess.movement.util import rot
from chess.pieces.piece import Piece


class Llama(Piece):
    name = 'Llama'
    file_name = 'W2[W-W-F]'
    asset_folder = 'camel'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [
                types.BentMovement(board, [
                    types.RiderMovement(board, [(i, j, 2)]),
                    types.RiderMovement(board, [(i or k, j or k, 1) for k in (1, -1)])
                ]) for i, j in rot([(1, 0)])
            ]),
            **kwargs
        )


class Cashier(Piece):
    name = 'Cashier'
    file_name = 'CW'
    asset_folder = 'camel'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0, 1), (1, 3, 1), (3, 1, 1)])),
            **kwargs
        )


class Cabbage(Piece):
    name = 'Cabbage'
    file_name = 'BC'
    asset_folder = 'camel'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 1), (1, 3, 1), (3, 1, 1)])),
            **kwargs
        )


class Warlock(Piece):
    name = 'Warlock'
    file_name = 'RCF'
    asset_folder = 'camel'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0), (1, 1, 1), (1, 3, 1), (3, 1, 1)])),
            **kwargs
        )
