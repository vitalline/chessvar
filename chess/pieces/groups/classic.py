from chess.movement import movement
from chess.movement.util import rot, sym
from chess.pieces import pieces


class Rook(pieces.Piece):
    name = 'Rook'
    file_name = 'rook'
    asset_folder = 'classic'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0)]))
        )


class Knight(pieces.Piece):
    name = 'Knight'
    file_name = 'knight'
    asset_folder = 'classic'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, sym([(1, 2, 1), (2, 1, 1)]))
        )


class Bishop(pieces.Piece):
    name = 'Bishop'
    file_name = 'bishop'
    asset_folder = 'classic'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, sym([(1, 1)]))
        )


class Queen(pieces.Piece):
    name = 'Queen'
    file_name = 'queen'
    asset_folder = 'classic'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0), (1, 1)]))
        )


class King(pieces.RoyalPiece):
    name = 'King'
    file_name = 'king'
    asset_folder = 'classic'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(
                board, [
                    movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1)])),
                    movement.CastlingMovement(board, (0, 2), (0, 3), (0, -2), [(0, 1), (0, 2)]),
                    movement.CastlingMovement(board, (0, -2), (0, -4), (0, 3), [(0, -1), (0, -2), (0, -3)]),
                ]
            )
        )


class Pawn(pieces.PromotablePiece):
    name = 'Pawn'
    file_name = 'pawn'
    asset_folder = 'classic'

    def __init__(self, board, board_pos, side, promotions=None, promotion_squares=None):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(
                board,
                move=[movement.EnPassantTargetMovement(board, [(1, 0, 1)], [(1, 0, 2)], [(1, 0, 1)])],
                capture=[movement.EnPassantMovement(board, [(1, 1, 1), (1, -1, 1)])],
            ),
            promotions,
            promotion_squares
        )
