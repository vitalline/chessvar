from chess.movement import movement
from chess.movement.util import rot
from chess.pieces import pieces


class Amazon(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Amazon',
            file_name=f'{side.file_name()}_centaur_queen',
            asset_folder='centaur',
            movement=movement.RiderMovement(board, rot([(1, 0), (1, 1), (1, 2, 1), (2, 1, 1)]))
        )