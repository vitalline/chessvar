from chess.movement import types
from chess.movement.util import rot
from chess.pieces.piece import Piece


class Naysayer(Piece):
    name = 'Naysayer'
    file_name = 'nAAnH'
    asset_folder = 'horse'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [types.RiderMovement(board, rot([(1, 0, 3, 3)]))] + [
                types.RepeatMovement(board, [
                    types.RiderMovement(board, [(i, j, 2, 2) for i, j in rot([(1, 1)])])
                ])
            ]),
            **kwargs
        )


class HorseRdr(Piece):
    name = 'Horserider'
    file_name = 'afs(afzafz)W'
    asset_folder = 'horse'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [
                types.RepeatMovement(board, [
                    types.RiderMovement(board, [(i, j, 1)]),
                    types.RiderMovement(board, [(i or k, j or k, 1) for k in (1, -1)])
                ], 1) for i, j in rot([(1, 0)])
            ]),
            **kwargs
        )


class Tapir(Piece):
    name = 'Tapir'
    file_name = '[W-F]nA'
    asset_folder = 'horse'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [types.RiderMovement(board, rot([(1, 1, 2, 2)]))] + [
                types.BentMovement(board, [
                    types.RiderMovement(board, [(i, j, 1)]),
                    types.RiderMovement(board, [(i or k, j or k, 1) for k in (1, -1)])
                ], 1) for i, j in rot([(1, 0)])
            ]),
            **kwargs
        )


class Marauder(Piece):
    name = 'Marauder'
    file_name = 'Wafs(afz)W'
    asset_folder = 'horse'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [
                types.RepeatMovement(board, [
                    types.RiderMovement(board, [(i, j, 1)]),
                    types.RiderMovement(board, [(i, 0, 1), (0, j, 1)])
                ]) for i, j in rot([(1, 1)])
            ]),
            **kwargs
        )
