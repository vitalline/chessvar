from chess.movement import movement
from chess.movement.util import rot, sym
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


class Napoleon(Piece):
    name = 'Napoleon'
    file_name = 'fbNW'
    asset_folder = 'mash'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1)]) + sym([(2, 1, 1)]))
        )


class Bandage(Piece):
    name = 'Bandage'
    file_name = 'B4nD'
    asset_folder = 'mash'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1, 4), (1, 0, 2, 2)]))
        )


class Rancor(Piece):
    name = 'Rancor'
    file_name = 'R4N2'
    asset_folder = 'mash'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 4), (1, 2, 2), (2, 1, 2)]))
        )
