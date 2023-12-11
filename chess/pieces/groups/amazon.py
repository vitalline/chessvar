from chess.movement import movement
from chess.movement.util import rot
from chess.pieces import pieces


class Amazon(pieces.Piece):
    name = 'Amazon'
    file_name = 'centaur_queen'
    asset_folder = 'centaur'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement=movement.RiderMovement(board, rot([(1, 0), (1, 1), (1, 2, 1), (2, 1, 1)]))
        )