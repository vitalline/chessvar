from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece


class Ouroboros(Piece):
    name = 'Ouroboros'
    file_name = 'ND'
    asset_folder = 'beast'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 2, 1), (2, 0, 1), (2, 1, 1)]))
        )


class Quagga(Piece):
    name = 'Quagga'
    file_name = 'ZF'
    asset_folder = 'beast'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1, 1), (2, 3, 1), (3, 2, 1)]))
        )


class Roc(Piece):
    name = 'Roc'
    file_name = 'CA'
    asset_folder = 'beast'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 3, 1), (2, 2, 1), (3, 1, 1)]))
        )


class Buffalo(Piece):
    name = 'Buffalo'
    file_name = 'NCZ'
    asset_folder = 'beast'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 2, 1), (1, 3, 1), (2, 1, 1), (2, 3, 1), (3, 1, 1), (3, 2, 1)]))
        )
