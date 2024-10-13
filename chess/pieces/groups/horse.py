from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.piece import Piece


class Naysayer(Piece):
    name = 'Naysayer'
    file_name = 'nAAnH'
    asset_folder = 'horse'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.MultiMovement(board, [movement.RiderMovement(board, rot([(1, 0, 3, 3)]))] + [
                movement.RepeatMovement(board, [
                    movement.RiderMovement(board, [(i, j, 2, 2)])
                ]) for i, j in rot([(1, 1)])
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
            movement.MultiMovement(board, [
                movement.RepeatMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(i or k, j or k, 1)])
                ], 1) for i, j in rot([(1, 0)]) for k in (1, -1)
            ]),
            **kwargs
        )


class Tapir(Piece):
    name = 'Tapir'
    file_name = 'afsWnA'
    asset_folder = 'horse'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.MultiMovement(board, [movement.RiderMovement(board, rot([(1, 1, 2, 2)]))] + [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(i or k, j or k, 1)])
                ], 1) for i, j in rot([(1, 0)]) for k in (1, -1)
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
            movement.MultiMovement(board, [
                movement.RepeatMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(i or k, j or k, 1)])
                ]) for i, j in rot([(1, 0)]) for k in (1, -1)
            ]),
            **kwargs
        )
