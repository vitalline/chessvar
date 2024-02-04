from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece


class Trident(Piece):
    name = 'Trident'
    file_name = 'WDH'
    asset_folder = 'thrash'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (2, 0, 1), (3, 0, 1)]))
        )


class Nipper(Piece):
    name = 'Nipper'
    file_name = 'NT'
    asset_folder = 'thrash'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 2, 1), (2, 1, 1), (3, 3, 1)]))
        )


class Bullfrog(Piece):
    name = 'Bullfrog'
    file_name = 'FAH'
    asset_folder = 'thrash'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1, 1), (2, 2, 1), (3, 0, 1)]))
        )


class Duchess(Piece):
    name = 'Duchess'
    file_name = 'KATDH'
    asset_folder = 'thrash'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1), (2, 0, 1), (2, 2, 1), (3, 0, 1), (3, 3, 1)]))
        )
