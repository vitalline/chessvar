from chess.movement import types
from chess.movement.util import rot, symv
from chess.pieces.piece import Piece


class Whelk(Piece):
    name = 'Whelk'
    file_name = 'fWfDsbR'
    asset_folder = 'backward'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, symv([(1, 0, 1), (2, 0, 1), (0, 1), (-1, 0)])),
            **kwargs
        )


class Walrus(Piece):
    name = 'Walrus'
    file_name = 'fNfRbhQ'
    asset_folder = 'backward'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, symv([(1, 0), (2, 1, 1), (-1, 0), (-1, 1)])),
            **kwargs
        )


class Seagull(Piece):
    name = 'Seagull'
    file_name = 'fFfAbBcfafF'
    asset_folder = 'backward'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [
                types.RiderMovement(board, symv([(1, 1, 1), (2, 2, 1), (-1, 1)]))
            ] + [
                types.ChainMovement(board, [
                    types.MultiMovement(board, capture=[
                        types.RiderMovement(board, [(i, j, 1)])
                    ]),
                    types.MultiMovement(board, move_or_capture=[
                        types.RiderMovement(board, [(i, j, 1), (0, 0)])
                    ])
                ]) for i, j in symv([(1, 1)])
            ]),
            **kwargs
        )


class Shark(Piece):
    name = 'Shark'
    file_name = 'RfhNbB'
    asset_folder = 'backward'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0)]) + symv([(1, 2, 1), (2, 1, 1), (-1, 1)])),
            **kwargs
        )
