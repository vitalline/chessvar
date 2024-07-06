from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece


class Waffle(Piece):
    name = 'Waffle'
    file_name = 'oWoA'
    asset_folder = 'cylindrical'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.CylindricalRiderMovement(board, rot([(1, 0, 1), (2, 2, 1)]))
        )


class Knight(Piece):
    name = 'Knight'
    file_name = 'oN'
    asset_folder = 'cylindrical'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.CylindricalRiderMovement(board, rot([(1, 2, 1), (2, 1, 1)]))
        )


class Bishop(Piece):
    name = 'Bishop'
    file_name = 'oB'
    asset_folder = 'cylindrical'
    colorbound = True

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.CylindricalRiderMovement(board, rot([(1, 1)]))
        )


class Chancellor(Piece):
    name = 'Chancellor'
    file_name = 'oRoN'
    asset_folder = 'cylindrical'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.CylindricalRiderMovement(board, rot([(1, 0), (1, 2, 1), (2, 1, 1)]))
        )
