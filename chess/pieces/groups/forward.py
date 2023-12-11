from chess.movement import movement
from chess.movement.util import symv
from chess.pieces import pieces


class Knishop(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Knishop',
            file_name=f'{side.file_name()}_jester',
            asset_folder='medieval',
            movement=movement.RiderMovement(board, symv([(1, 2, 1), (2, 1, 1), (-1, 1)]))
        )


class Bishight(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Bishight',
            file_name=f'{side.file_name()}_priest',
            asset_folder='medieval',
            movement=movement.RiderMovement(board, symv([(-1, 2, 1), (-2, 1, 1), (1, 1)]))
        )


class Forequeen(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Forequeen',
            file_name=f'{side.file_name()}_pasha',
            asset_folder='medieval',
            movement=movement.RiderMovement(
                board, symv([(1, 0), (1, 1), (0, 1), (-1, 0, 1), (-1, 1, 1), (-1, 2, 1), (-2, 1, 1)])
            )
        )
