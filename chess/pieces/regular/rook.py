from chess.movement.base import RiderMovement
from chess.movement.util import sym
from chess.pieces.piece import Piece


class Rook(Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Rook',
            file_name=f'{side.file_name()}_rook',
            asset_folder='pieces',
            movement=RiderMovement(board, sym([(1, 0)]))
        )
