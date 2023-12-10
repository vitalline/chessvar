from chess.movement.base import FirstMoveRiderMovement, MoveCaptureMovement, RiderMovement
from chess.pieces.piece import PromotablePiece


class Pawn(PromotablePiece):
    def __init__(self, board, board_pos, side, promotions, promotion_tiles):
        super().__init__(
            board, board_pos, side,
            name='Pawn',
            file_name=f'{side.file_name()}_pawn',
            asset_folder='pieces',
            movement=MoveCaptureMovement(
                FirstMoveRiderMovement(board, [(1, 0, 1)], [(1, 0, 2)]),
                RiderMovement(board, [(1, 1, 1), (1, -1, 1)]),
            ),
            promotions=promotions,
            promotion_tiles=promotion_tiles
        )
