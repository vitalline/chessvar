from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.piece import Piece


class Fencer(Piece):
    name = 'Fencer'
    file_name = 'NH'
    asset_folder = 'perimeter'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.RiderMovement(board, rot([(1, 2, 1), (2, 1, 1), (3, 0, 1)])),
            **kwargs
        )


class Castle(Piece):
    name = 'Castle'
    file_name = 'nDnNnA'
    asset_folder = 'perimeter'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(i, j, 1), (i or 1, j or 1, 1), (i or -1, j or -1, 1)])
                ], 1) for i, j in rot([(1, 0)])
            ] + [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(i, j, 1), (i, 0, 1), (0, j, 1)])
                ], 1) for i, j in rot([(1, 1)])
            ]),
            **kwargs
        )


class Kirin(Piece):
    name = 'Kirin'
    file_name = 'FD'
    asset_folder = 'perimeter'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.RiderMovement(board, rot([(1, 1, 1), (2, 0, 1)])),
            **kwargs
        )


class Fort(Piece):
    name = 'Fort'
    file_name = 'WAND'
    asset_folder = 'perimeter'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.RiderMovement(board, rot([(1, 0, 1), (1, 2, 1), (2, 0, 1), (2, 1, 1), (2, 2, 1)])),
            **kwargs
        )
