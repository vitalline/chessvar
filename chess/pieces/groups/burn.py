from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece


class Caddy(Piece):
    name = 'Caddy'
    file_name = 'CD'
    asset_folder = 'burn'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 3, 1), (3, 1, 1), (2, 0, 1)]))
        )


class Sorcerer(Piece):
    name = 'Sorcerer'
    file_name = 'ZW'
    asset_folder = 'burn'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (2, 3, 1), (3, 2, 1)]))
        )


class DragonHorse(Piece):
    name = 'Dragon Horse'
    file_name = 'BW'
    asset_folder = 'burn'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (1, 1)]))
        )


class DragonKing(Piece):
    name = 'Dragon King'
    file_name = 'RF'
    asset_folder = 'burn'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0), (1, 1, 1)]))
        )
