from chess.movement.base import RiderMovement
from chess.movement.util import sym
from chess.pieces.piece import Piece


class Knight(Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Knight',
            file_name=f'{side.file_name()}_knight',
            asset_folder='pieces',
            movement=RiderMovement(board, sym([(1, 2, 1), (2, 1, 1)]))
        )
