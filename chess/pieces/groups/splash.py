from chess.movement import types
from chess.movement.util import rot
from chess.pieces.piece import Piece


class Mammoth(Piece):
    name = 'Mammoth'
    file_name = 'R4nA'
    asset_folder = 'splash'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0, 4), (1, 1, 2, 2)])),
            **kwargs
        )


class Gecko(Piece):
    name = 'Gecko'
    file_name = 'GK'
    asset_folder = 'splash'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1), (3, 3, 1)])),
            **kwargs
        )


class Deacon(Piece):
    name = 'Deacon'
    file_name = 'B4W'
    asset_folder = 'splash'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0, 1), (1, 1, 4)])),
            **kwargs
        )


class Brigadier(Piece):
    name = 'Brigadier'
    file_name = 'R4FN'
    asset_folder = 'splash'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0, 4), (1, 1, 1), (1, 2, 1), (2, 1, 1)])),
            **kwargs
        )
