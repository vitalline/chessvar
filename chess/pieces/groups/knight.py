from chess.movement import types
from chess.movement.util import sym, symv
from chess.pieces.piece import Piece


class Forerook(Piece):
    name = 'Forerook'
    file_name = 'fsRbhK'
    asset_folder = 'knight'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, symv([(1, 0), (0, 1), (-1, 0, 1), (-1, 1, 1)])),
            **kwargs
        )


class Fibnif(Piece):
    name = 'Fibnif'
    file_name = 'fbNF'
    asset_folder = 'knight'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, sym([(1, 1, 1), (2, 1, 1)])),
            **kwargs
        )


class Foreknight(Piece):
    name = 'Foreknight'
    file_name = 'fNbhsK'
    asset_folder = 'knight'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, symv([(2, 1, 1), (1, 2, 1), (0, 1, 1), (-1, 0, 1), (-1, 1, 1)])),
            **kwargs
        )


class Colonel(Piece):
    name = 'Colonel'
    file_name = 'fhNfsRK'
    asset_folder = 'knight'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(
                board, sym([(1, 1, 1)]) + symv([(2, 1, 1), (1, 2, 1), (1, 0), (0, 1), (-1, 0, 1), (-1, 1, 1)])
            ),
            **kwargs
        )
