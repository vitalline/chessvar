from chess.movement import types
from chess.movement.util import rot
from chess.pieces.piece import Piece


class Frog(Piece):
    name = 'Frog'
    file_name = 'FH'
    asset_folder = 'fairy'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 1, 1), (3, 0, 1)])),
            **kwargs
        )


class Dullahan(Piece):
    name = 'Dullahan'
    file_name = 'NF'
    asset_folder = 'fairy'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 1, 1), (1, 2, 1), (2, 1, 1)])),
            **kwargs
        )


class Elephant(Piece):
    name = 'Elephant'
    file_name = 'FA'
    asset_folder = 'fairy'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 1, 1), (2, 2, 1)])),
            **kwargs
        )


class Unicorn(Piece):
    name = 'Unicorn'
    file_name = 'BNN'
    asset_folder = 'fairy'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 1), (1, 2), (2, 1)])),
            **kwargs
        )
