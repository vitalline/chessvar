from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.piece import Piece


class Caecilian(Piece):
    name = 'Caecilian'
    file_name = 'HA'
    asset_folder = 'stone'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.RiderMovement(board, rot([(2, 2, 1), (3, 0, 1)])),
            **kwargs
        )


class Brick(Piece):
    name = 'Brick'
    file_name = 'WDG'
    asset_folder = 'stone'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.RiderMovement(board, rot([(1, 0, 1), (2, 0, 1), (3, 3, 1)])),
            **kwargs
        )


class Stele(Piece):
    name = 'Stele'
    file_name = 'FmcaF'
    asset_folder = 'stone'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [
                        (k, l, 1) for k, l in rot([(1, 1)]) if (i, j) != (-k, -l)
                    ])
                ]) for i, j in rot([(1, 1)])
            ] + [
                movement.ChainMovement(board, [
                    movement.MultiMovement(board, capture=[
                        movement.RiderMovement(board, [(i, j, 1)])
                    ]),
                    movement.MultiMovement(board, move_or_capture=[
                        movement.RiderMovement(board, [
                            (k, l, 1) for k, l in rot([(1, 1)]) + [(0, 0)] if (i, j) != (-k, -l)
                        ])
                    ])
                ]) for i, j in rot([(1, 1)])
            ]),
            **kwargs
        )


class Caryatid(Piece):
    name = 'Caryatid'
    file_name = 'WmcaW'
    asset_folder = 'stone'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [
                        (k, l, 1) for k, l in rot([(1, 0)]) if (i, j) != (-k, -l)
                    ])
                ]) for i, j in rot([(1, 0)])
            ] + [
                movement.ChainMovement(board, [
                    movement.MultiMovement(board, capture=[
                        movement.RiderMovement(board, [(i, j, 1)])
                    ]),
                    movement.MultiMovement(board, move_or_capture=[
                        movement.RiderMovement(board, [
                            (k, l, 1) for k, l in rot([(1, 0)]) + [(0, 0)] if (i, j) != (-k, -l)
                        ])
                    ])
                ]) for i, j in rot([(1, 0)])
            ]),
            **kwargs
        )
