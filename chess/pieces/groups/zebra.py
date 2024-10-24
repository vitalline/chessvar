from chess.movement import types
from chess.movement.util import rot
from chess.pieces.piece import Piece


class Eliphas(Piece):
    name = 'Eliphas'
    file_name = 'W[W-F][W-F-F]'
    asset_folder = 'zebra'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [
                types.BentMovement(board, [
                    types.RiderMovement(board, [(i, j, 1)]),
                    types.RiderMovement(board, [(i or k, j or k, 2) for k in (1, -1)])
                ]) for i, j in rot([(1, 0)])
            ]),
            **kwargs
        )


class Sorcerer(Piece):
    name = 'Sorcerer'
    file_name = 'ZW'
    asset_folder = 'zebra'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0, 1), (2, 3, 1), (3, 2, 1)])),
            **kwargs
        )


class Adze(Piece):
    name = 'Adze'
    file_name = 'ZA'
    asset_folder = 'zebra'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(2, 2, 1), (2, 3, 1), (3, 2, 1)])),
            **kwargs
        )


class IMarauder(Piece):
    name = 'Contramarauder'
    file_name = 'Fafs(afz)F'
    asset_folder = 'zebra'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [
                types.RepeatMovement(board, [
                    types.RiderMovement(board, [(i or k, j or k, 1)]),
                    types.RiderMovement(board, [(i, j, 1)])
                ]) for i, j in rot([(1, 0)]) for k in (1, -1)
            ]),
            **kwargs
        )
