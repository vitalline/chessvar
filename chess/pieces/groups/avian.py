from chess.movement import movement
from chess.movement.util import rot, sym
from chess.pieces.pieces import Piece


class Wader(Piece):
    name = 'Wader'
    file_name = 'WDD'
    asset_folder = 'avian'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (2, 0)]))
        )


class Nightrider(Piece):
    name = 'Nightrider'
    file_name = 'NN'
    asset_folder = 'avian'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, sym([(1, 2), (2, 1)]))
        )


class Faalcon(Piece):
    name = 'Faalcon'
    file_name = 'FAA'
    asset_folder = 'avian'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, sym([(1, 1, 1), (2, 2)]))
        )


class Kingfisher(Piece):
    name = 'Kingfisher'
    file_name = 'KAADD'
    asset_folder = 'avian'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1), (2, 0), (2, 2)]))
        )
