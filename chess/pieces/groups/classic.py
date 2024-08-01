from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.pieces import Piece, PromotablePiece, RoyalPiece


class Rook(Piece):
    name = 'Rook'
    file_name = 'R'
    asset_folder = 'classic'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0)])),
            **kwargs
        )


class Knight(Piece):
    name = 'Knight'
    file_name = 'N'
    asset_folder = 'classic'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 2, 1), (2, 1, 1)])),
            **kwargs
        )


class Bishop(Piece):
    name = 'Bishop'
    file_name = 'B'
    asset_folder = 'classic'
    colorbound = True

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1)])),
            **kwargs
        )


class Queen(Piece):
    name = 'Queen'
    file_name = 'Q'
    asset_folder = 'classic'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0), (1, 1)])),
            **kwargs
        )


class King(RoyalPiece):
    name = 'King'
    file_name = 'K'
    asset_folder = 'classic'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(
                board, [
                    movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1)])),
                    movement.CastlingMovement(
                        board, (0, 2), (0, 3), (0, -2),
                        movement_gap=[(0, 1), (0, 2)], en_passant_gap=[(0, 0), (0, 1)]
                    ),
                    movement.CastlingMovement(
                        board, (0, -2), (0, -4), (0, 3),
                        movement_gap=[(0, -1), (0, -2), (0, -3)], en_passant_gap=[(0, 0), (0, -1)],
                    )
                ]
            ),
            **kwargs
        )


class Pawn(PromotablePiece):
    name = 'Pawn'
    file_name = 'P'
    asset_folder = 'classic'

    def __init__(self, board, board_pos, side, promotions=None, promotion_squares=None, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(
                board,
                move=[
                    movement.FirstMoveMovement(
                        board,
                        [movement.RiderMovement(board, [(1, 0, 1)])],
                        [movement.EnPassantTargetRiderMovement(board, [(1, 0, 2)])]
                    )
                ],
                capture=[
                    movement.EnPassantRiderMovement(board, symv([(1, 1, 1)]))
                ]
            ),
            promotions,
            promotion_squares,
            **kwargs
        )
