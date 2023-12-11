from chess.movement.movement import RiderMovement, MultiMovement, FirstMoveRiderMovement, EnPassantMovement, \
    EnPassantTargetMovement, CastlingMovement
from chess.movement.util import sym
from chess.pieces.piece import Piece, PromotablePiece


class Rook(Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Rook',
            file_name=f'{side.file_name()}_rook',
            asset_folder='pieces',
            movement=RiderMovement(board, sym([(1, 0)]))
        )


class Knight(Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Knight',
            file_name=f'{side.file_name()}_knight',
            asset_folder='pieces',
            movement=RiderMovement(board, sym([(1, 2, 1), (2, 1, 1)]))
        )


class Bishop(Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Bishop',
            file_name=f'{side.file_name()}_bishop',
            asset_folder='pieces',
            movement=RiderMovement(board, sym([(1, 1)]))
        )


class Queen(Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Queen',
            file_name=f'{side.file_name()}_queen',
            asset_folder='pieces',
            movement=RiderMovement(board, sym([(1, 0), (1, 1)]))
        )


class King(Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='King',
            file_name=f'{side.file_name()}_king',
            asset_folder='pieces',
            movement=MultiMovement(
                board, [
                    RiderMovement(board, sym([(1, 0, 1), (1, 1, 1)])),
                    CastlingMovement(board, (0, 2), (0, 3), (0, -2)),
                    CastlingMovement(board, (0, -2), (0, -4), (0, 3)),
                ]
            )
        )


class Pawn(PromotablePiece):
    def __init__(self, board, board_pos, side, promotions, promotion_tiles):
        super().__init__(
            board, board_pos, side,
            name='Pawn',
            file_name=f'{side.file_name()}_pawn',
            asset_folder='pieces',
            movement=MultiMovement(
                board,
                move=[EnPassantTargetMovement(board, [(1, 0, 1)], [(1, 0, 2)], [(1, 0, 1)])],
                capture=[EnPassantMovement(board, [(1, 1, 1), (1, -1, 1)])],
            ),
            promotions=promotions,
            promotion_tiles=promotion_tiles
        )
