from chess.movement import types
from chess.movement.util import rot
from chess.pieces.piece import Piece


class Champion(Piece):
    name = 'Champion'
    file_name = 'WAD'
    asset_folder = 'burn'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0, 1), (2, 0, 1), (2, 2, 1)])),
            **kwargs
        )


class DraHorse(Piece):
    name = 'Dragon Horse'
    file_name = 'BW'
    asset_folder = 'burn'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0, 1), (1, 1)])),
            **kwargs
        )


class Wizard(Piece):
    name = 'Wizard'
    file_name = 'CF'
    asset_folder = 'burn'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 1, 1), (1, 3, 1), (3, 1, 1)])),
            **kwargs
        )


class DraKing(Piece):
    name = 'Dragon King'
    file_name = 'RF'
    asset_folder = 'burn'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0), (1, 1, 1)])),
            **kwargs
        )
