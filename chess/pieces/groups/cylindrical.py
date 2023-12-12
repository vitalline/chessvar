from chess.movement import movement
from chess.movement.util import rot, sym
from chess.pieces import pieces


class CyWaffle(pieces.Piece):
    name = 'Cylindrical Waffle'
    file_name = 'sorcerer2'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.CylindricalRiderMovement(board, rot([(1, 0, 1), (2, 2, 1)]))
        )


class CyKnight(pieces.Piece):
    name = 'Cylindrical Knight'
    file_name = 'knight2'
    asset_folder = 'classic2'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.CylindricalRiderMovement(board, sym([(1, 2, 1), (2, 1, 1)]))
        )


class CyBishop(pieces.Piece):
    name = 'Cylindrical Bishop'
    file_name = 'bishop2'
    asset_folder = 'classic2'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.CylindricalRiderMovement(board, sym([(1, 1)]))
        )


class CyChancellor(pieces.Piece):
    name = 'Cylindrical Chancellor'
    file_name = 'chancellor2'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.CylindricalRiderMovement(board, rot([(1, 0), (1, 2, 1), (2, 1, 1)]))
        )
