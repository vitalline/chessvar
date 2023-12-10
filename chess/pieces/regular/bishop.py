from chess.movement.base import RiderMovement
from chess.movement.util import sym
from chess.pieces.piece import Piece


class Bishop(Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Bishop',
            file_name=f'{side.file_name()}_bishop',
            asset_folder='pieces',
            movement=RiderMovement(board, sym([(1, 1)]))
        )
