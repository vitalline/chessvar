from chess.movement import types
from chess.movement.util import rot, symv
from chess.pieces.piece import Piece


class Wader(Piece):
    name = 'Wader'
    file_name = 'WDD'
    asset_folder = 'avian'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0, 1), (2, 0)])),
            **kwargs
        )


class Darter(Piece):
    name = 'Darter'
    file_name = 'fNWbAA'
    asset_folder = 'avian'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0, 1)]) + symv([(2, 1, 1), (-2, 2)])),
            **kwargs
        )


class Falcon(Piece):
    name = 'Falcon'
    file_name = 'FAA'
    asset_folder = 'avian'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 1, 1), (2, 2)])),
            **kwargs
        )


class Kingfisher(Piece):
    name = 'Kingfisher'
    file_name = 'KAADD'
    asset_folder = 'avian'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1), (2, 0), (2, 2)])),
            **kwargs
        )
