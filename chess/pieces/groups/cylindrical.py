from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.piece import Piece


class Waffle(Piece):
    name = 'Cylindrical Waffle'
    file_name = 'oWoA'
    asset_folder = 'cylindrical'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.CylindricalRiderMovement(board, rot([(1, 0, 1), (2, 2, 1)])),
            **kwargs
        )


class Knight(Piece):
    name = 'Cylindrical Knight'
    file_name = 'oN'
    asset_folder = 'cylindrical'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.CylindricalRiderMovement(board, rot([(1, 2, 1), (2, 1, 1)])),
            **kwargs
        )


class Bishop(Piece):
    name = 'Cylindrical Bishop'
    file_name = 'oB'
    asset_folder = 'cylindrical'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.CylindricalRiderMovement(board, rot([(1, 1)])),
            **kwargs
        )


class Chancellor(Piece):
    name = 'Cylindrical Chancellor'
    file_name = 'oRoN'
    asset_folder = 'cylindrical'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.CylindricalRiderMovement(board, rot([(1, 0), (1, 2, 1), (2, 1, 1)])),
            **kwargs
        )
