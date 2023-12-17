from chess.movement import movement
from chess.movement.util import rot, sym, symv
from chess.pieces.pieces import Piece


class Pepperoni(Piece):
    name = 'Pepperoni'
    file_name = 'circle'
    asset_folder = 'geometry'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(2, 2, 1)]) + sym([(0, 2, 1), (1, 1, 1), (1, 0, 1)]))
        )


class Mushroom(Piece):
    name = 'Mushroom'
    file_name = 'mushroom'
    asset_folder = 'nature'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(2, 1, 1), (1, 3, 1), (-1, 1, 1), (-2, 1, 1)]))
        )


class Sausage(Piece):
    name = 'Sausage'
    file_name = 'courier_runner'
    asset_folder = 'courier'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, sym([(3, 0, 1), (2, 1, 1), (1, 1, 1), (0, 1, 1)]))
        )


class Meatball(Piece):
    name = 'Meatball'
    file_name = 'courier_rook'
    asset_folder = 'courier'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(2, 1, 1)]) + rot([(1, 0, 1), (1, 1, 1), (2, 0, 1), (2, 2, 1)]))
        )
