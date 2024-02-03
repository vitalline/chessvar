from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.pieces import Piece


class Platypus(Piece):
    name = 'Platypus'
    file_name = 'B2sR2fW'
    asset_folder = 'iron'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(1, 0, 1), (1, 1, 2), (0, 1, 2), (-1, 1, 2)]))
        )


class Enforcer(Piece):
    name = 'Enforcer'
    file_name = 'vvNfKbW'
    asset_folder = 'iron'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(1, 0, 1), (1, 1, 1), (-1, 0, 1), (2, 1, 1), (-2, 1, 1)]))
        )


class SRider(Piece):
    name = 'Silverrider'
    file_name = 'BfR'
    asset_folder = 'iron'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1)]) + [(1, 0)])
        )


class GRider(Piece):
    name = 'Goldrider'
    file_name = 'RfB'
    asset_folder = 'iron'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0)]) + symv([(1, 1)]))
        )
