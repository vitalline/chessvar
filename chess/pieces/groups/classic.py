from chess.movement import movement
from chess.movement.util import sym
from chess.pieces import pieces


class Rook(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Rook',
            file_name=f'{side.file_name()}_rook',
            asset_folder='classic',
            movement=movement.RiderMovement(board, sym([(1, 0)]))
        )


class Knight(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Knight',
            file_name=f'{side.file_name()}_knight',
            asset_folder='classic',
            movement=movement.RiderMovement(board, sym([(1, 2, 1), (2, 1, 1)]))
        )


class Bishop(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Bishop',
            file_name=f'{side.file_name()}_bishop',
            asset_folder='classic',
            movement=movement.RiderMovement(board, sym([(1, 1)]))
        )


class Queen(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Queen',
            file_name=f'{side.file_name()}_queen',
            asset_folder='classic',
            movement=movement.RiderMovement(board, sym([(1, 0), (1, 1)]))
        )


class King(pieces.RoyalPiece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='King',
            file_name=f'{side.file_name()}_king',
            asset_folder='classic',
            movement=movement.MultiMovement(
                board, [
                    movement.RiderMovement(board, sym([(1, 0, 1), (1, 1, 1)])),
                    movement.CastlingMovement(board, (0, 2), (0, 3), (0, -2), [(0, 1), (0, 2)]),
                    movement.CastlingMovement(board, (0, -2), (0, -4), (0, 3), [(0, -1), (0, -2), (0, -3)]),
                ]
            )
        )


class Pawn(pieces.PromotablePiece):
    def __init__(self, board, board_pos, side, promotions, promotion_tiles):
        super().__init__(
            board, board_pos, side,
            name='Pawn',
            file_name=f'{side.file_name()}_pawn',
            asset_folder='classic',
            movement=movement.MultiMovement(
                board,
                move=[movement.EnPassantTargetMovement(board, [(1, 0, 1)], [(1, 0, 2)], [(1, 0, 1)])],
                capture=[movement.EnPassantMovement(board, [(1, 1, 1), (1, -1, 1)])],
            ),
            promotions=promotions,
            promotion_tiles=promotion_tiles
        )
