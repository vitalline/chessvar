from chess.movement import types
from chess.movement.util import rot, symv
from chess.pieces.piece import Piece


class Heart(Piece):
    name = 'Heart'
    file_name = 'hhRA'
    asset_folder = 'hobbit'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [
                types.RiderMovement(board, rot([(2, 2, 1)])),
                types.HalflingRiderMovement(board, rot([(1, 0)]))
            ]),
            **kwargs
        )


class Drake(Piece):
    name = 'Drake'
    file_name = 'Fhh[F-R]'
    asset_folder = 'hobbit'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [
                types.BentMovement(board, [
                    types.RiderMovement(board, [(i, j, 1)]),
                    types.HalflingRiderMovement(board, [(i, 0), (0, j)], 1)
                ]) for i, j in rot([(1, 1)])
            ]),
            **kwargs
        )


class Barcinal(Piece):
    name = 'Barcinal'
    file_name = 'fsbbNhhB'
    asset_folder = 'hobbit'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [
                types.RiderMovement(board, symv([(1, 2, 1), (-2, 1, 1)])),
                types.HalflingRiderMovement(board, rot([(1, 1)]))
            ]),
            **kwargs
        )


class Hannibal(Piece):
    name = 'Hannibal'
    file_name = 'hhNNhhQ'
    asset_folder = 'hobbit'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.HalflingRiderMovement(board, rot([(1, 0), (1, 1), (1, 2), (2, 1)])),
            **kwargs
        )
