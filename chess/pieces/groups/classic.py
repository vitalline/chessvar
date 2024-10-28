from chess.movement import types
from chess.movement.util import rot, symv
from chess.pieces.piece import Piece
from chess.pieces.types import Royal


class Rook(Piece):
    name = 'Rook'
    file_name = 'R'
    asset_folder = 'classic'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0)])),
            **kwargs
        )


class Knight(Piece):
    name = 'Knight'
    file_name = 'N'
    asset_folder = 'classic'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 2, 1), (2, 1, 1)])),
            **kwargs
        )


class Bishop(Piece):
    name = 'Bishop'
    file_name = 'B'
    asset_folder = 'classic'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 1)])),
            **kwargs
        )


class Queen(Piece):
    name = 'Queen'
    file_name = 'Q'
    asset_folder = 'classic'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0), (1, 1)])),
            **kwargs
        )


class King(Piece, Royal):
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
                        board, (0, -2), (0, -4), (0, 3),
                        movement_gap=[(0, -1), (0, -2), (0, -3)], en_passant_gap=[(0, 0), (0, -1)],
                    )
                ]
            ),
            **kwargs
        )


class Pawn(Piece):
    name = 'Pawn'
    file_name = 'P'
    asset_folder = 'classic'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(
                board,
                move=[
                    types.IndexMovement(
                        board,
                        [
                            [types.EnPassantTargetRiderMovement(board, [(1, 0, 2)])],
                            [types.RiderMovement(board, [(1, 0, 1)])],
                        ],
                    )
                ],
                capture=[
                    types.EnPassantRiderMovement(board, symv([(1, 1, 1)]))
                ]
            ),
            **kwargs
        )
