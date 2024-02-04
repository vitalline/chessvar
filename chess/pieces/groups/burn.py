from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece


class Champion(Piece):
    name = 'Champion'
    file_name = 'WAD'
    asset_folder = 'burn'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (2, 0, 1), (2, 2, 1)]))
        )


class DraHorse(Piece):
    name = 'Dragon Horse'
    file_name = 'BW'
    asset_folder = 'burn'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (1, 1)]))
        )


class Wizard(Piece):
    name = 'Wizard'
    file_name = 'CF'
    asset_folder = 'burn'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1, 1), (1, 3, 1), (3, 1, 1)]))
        )


class DraKing(Piece):
    name = 'Dragon King'
    file_name = 'RF'
    asset_folder = 'burn'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0), (1, 1, 1)]))
        )
