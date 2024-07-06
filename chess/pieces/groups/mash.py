from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece


class Forfer(Piece):
    name = 'Forfer'
    file_name = 'FR4'
    asset_folder = 'mash'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1, 1), (1, 0, 4)]))
        )


class Scout(Piece):
    name = 'Scout'
    file_name = 'WH'
    asset_folder = 'mash'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (3, 0, 1)]))
        )


class Bandit(Piece):
    name = 'Bandit'
    file_name = 'B4nD'
    asset_folder = 'mash'
    colorbound = True

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1, 4), (1, 0, 2, 2)]))
        )


class Rancher(Piece):
    name = 'Rancher'
    file_name = 'R4N2'
    asset_folder = 'mash'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 4), (1, 2, 2), (2, 1, 2)]))
        )
