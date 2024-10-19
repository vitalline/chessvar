from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.piece import Piece


class LionCub(Piece):
    name = 'Lion Cub'
    file_name = 'WmaWamW'
    asset_folder = 'crook'

    def __init__(self, board, **kwargs):
        movements = []
        for i, j in rot([(1, 0)]):
            movements.append(
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [
                        (k, l, 1) for k, l in rot([(1, 0)]) if (i, j) != (-k, -l)
                    ])
                ])
            )
            movements.append(
                movement.ChainMovement(board, [
                    movement.MultiMovement(board, capture=[
                        movement.RiderMovement(board, [(i, j, 1)])
                    ]),
                    movement.MultiMovement(board, move=[
                        movement.RiderMovement(board, [
                            (k, l, 1) for k, l in rot([(1, 0)]) + [(0, 0)] if (i, j) != (-k, -l)
                        ])
                    ])
                ])
            )
        super().__init__(
            board,
            movement.MultiMovement(board, movements),
            **kwargs
        )


class Rhino(Piece):
    name = 'Rhino'
    file_name = 'W[W-F]'
    asset_folder = 'crook'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(i or k, j or k, 1) for k in (1, -1)])
                ]) for i, j in rot([(1, 0)])
            ]),
            **kwargs
        )


class Boyscout(Piece):
    name = 'Boyscout'
    file_name = 'zB'
    asset_folder = 'crook'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.MultiMovement(board, [
                movement.RepeatMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1), (-i, -j, 1)]),
                    movement.RiderMovement(board, [(i, -j, 1), (-i, j, 1)]),
                ]) for i, j in symv([(1, 1)])
            ]),
            **kwargs
        )


class Griffon(Piece):
    name = 'Griffon'
    file_name = 'F[F-R]'
    asset_folder = 'crook'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(i, 0), (0, j)])
                ]) for i, j in rot([(1, 1)])
            ]),
            **kwargs
        )
