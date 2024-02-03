from chess.movement import movement
from chess.movement.util import rot2, symv
from chess.pieces.pieces import Piece


class IvoryRook(Piece):
    name = 'Ivory Rook'
    file_name = 'vRsWsD'
    asset_folder = 'forward'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot2([(1, 0), (0, 1, 1), (0, 2, 1)]))
        )


class Knishop(Piece):
    name = 'Knishop'
    file_name = 'fhNbB'
    asset_folder = 'forward'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(1, 2, 1), (2, 1, 1), (-1, 1)]))
        )


class Bishight(Piece):
    name = 'Bishight'
    file_name = 'fBbhN'
    asset_folder = 'forward'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(-1, 2, 1), (-2, 1, 1), (1, 1)]))
        )


class Forequeen(Piece):
    name = 'Forequeen'
    file_name = 'fhQsQbhNK'
    asset_folder = 'forward'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(
                board, symv([(1, 0), (1, 1), (0, 1), (-1, 0, 1), (-1, 1, 1), (-1, 2, 1), (-2, 1, 1)])
            )
        )
