from chess.movement import types
from chess.movement.util import rot
from chess.pieces.piece import Piece


class Bede(Piece):
    name = 'Bede'
    file_name = 'BD'
    asset_folder = 'colorbound'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 1), (2, 0, 1)])),
            **kwargs
        )


class Waffle(Piece):
    name = 'Waffle'
    file_name = 'WA'
    asset_folder = 'colorbound'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0, 1), (2, 2, 1)])),
            **kwargs
        )


class Fad(Piece):
    name = 'Fad'
    file_name = 'FAD'
    asset_folder = 'colorbound'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 1, 1), (2, 0, 1), (2, 2, 1)])),
            **kwargs
        )


class Archbishop(Piece):
    name = 'Archbishop'
    file_name = 'BN'
    asset_folder = 'colorbound'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 1), (1, 2, 1), (2, 1, 1)])),
            **kwargs
        )


# Note: The reason we redefine the King class here is that colorbound Rook-like pieces should preserve color on castling
# This implementation castles three squares kingside and two squares queenside - the CwDA rule for Colorbound Clobberers
# This version of the King should also be used for all other armies in which the Rook replacements are colorbound pieces
class King(Piece):
    name = 'King'
    file_name = 'K'
    asset_folder = 'classic'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(
                board, [
                    types.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1)])),
                    types.CastlingMovement(
                        board, (0, 2), (0, 3), (0, -2),
                        movement_gap=[(0, 1), (0, 2)], en_passant_gap=[(0, 0), (0, 1)]
                    ),
                    types.CastlingMovement(
                        board, (0, -3), (0, -4), (0, 2),
                        movement_gap=[(0, -1), (0, -2), (0, -3)], en_passant_gap=[(0, 0), (0, -1), (0, -2)]
                    )
                ]
            ),
            **kwargs
        )
