from chess.movement import movement
from chess.movement.util import rot, sym, symv
from chess.pieces.pieces import Piece


class Wader(Piece):
    name = 'Wader'
    file_name = 'star4'
    asset_folder = 'geometry'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (2, 0)]))
        )


class Darter(Piece):
    name = 'Darter'
    file_name = 'star3'
    asset_folder = 'geometry'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1)]) + symv([(2, 1, 1), (-2, 2)]))
        )


class Faalcon(Piece):
    name = 'Faalcon'
    file_name = 'triangles'
    asset_folder = 'geometry'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, sym([(1, 1, 1), (2, 2)]))
        )


class Kingfisher(Piece):
    name = 'Flying Kingfisher'
    file_name = 'octagon'
    asset_folder = 'geometry'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1), (2, 0), (2, 2)]))
        )
