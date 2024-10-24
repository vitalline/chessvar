from chess.movement import types
from chess.movement.util import rot
from chess.pieces.piece import Piece


class Veteran(Piece):
    name = 'Veteran'
    file_name = '{R,KAD}'
    asset_folder = 'probable'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.ProbabilisticMovement(board, [
                types.RiderMovement(board, rot([(1, 0)])),
                types.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1), (2, 0, 1), (2, 2, 1)]))
            ]),
            **kwargs
        )


class RedPanda(Piece):
    name = 'Red Panda'
    file_name = '{W[W-DD],N}'
    asset_folder = 'probable'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.ProbabilisticMovement(board, [
                types.MultiMovement(board, [
                    types.BentMovement(board, [
                        types.RiderMovement(board, [(i, j, 1)]),
                        types.RiderMovement(board, [(2 * i, 2 * j)])
                    ]) for i, j in rot([(1, 0)])
                ]),
                types.RiderMovement(board, rot([(1, 2, 1), (2, 1, 1)]))
            ]),
            **kwargs
        )


class Tempofad(Piece):
    name = 'Tempofad'
    file_name = '{B,FAD}'
    asset_folder = 'probable'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.ProbabilisticMovement(board, [
                types.RiderMovement(board, rot([(1, 1)])),
                types.RiderMovement(board, rot([(1, 1, 1), (2, 0, 1), (2, 2, 1)]))
            ]),
            **kwargs
        )


class WaterBuffalo(Piece):
    name = 'Water Buffalo'
    file_name = '{Q,NCZ}'
    asset_folder = 'probable'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.ProbabilisticMovement(board, [
                types.RiderMovement(board, rot([(1, 0), (1, 1)])),
                types.RiderMovement(board, rot([(1, 2, 1), (1, 3, 1), (2, 1, 1), (2, 3, 1), (3, 1, 1), (3, 2, 1)]))
            ]),
            **kwargs
        )
