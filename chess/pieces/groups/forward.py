from chess.movement import types
from chess.movement.util import rot2, symv
from chess.pieces.piece import Piece


class IvoryRook(Piece):
    name = 'Ivory Rook'
    file_name = 'vRsWsD'
    asset_folder = 'forward'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot2([(1, 0), (0, 1, 1), (0, 2, 1)])),
            **kwargs
        )


class Knishop(Piece):
    name = 'Knishop'
    file_name = 'fhNbB'
    asset_folder = 'forward'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, symv([(1, 2, 1), (2, 1, 1), (-1, 1)])),
            **kwargs
        )


class Bishight(Piece):
    name = 'Bishight'
    file_name = 'fBbhN'
    asset_folder = 'forward'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, symv([(-1, 2, 1), (-2, 1, 1), (1, 1)])),
            **kwargs
        )


class Forequeen(Piece):
    name = 'Forequeen'
    file_name = 'fhQsQbhNK'
    asset_folder = 'forward'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(
                board, symv([(1, 0), (1, 1), (0, 1), (-1, 0, 1), (-1, 1, 1), (-1, 2, 1), (-2, 1, 1)])
            ),
            **kwargs
        )
