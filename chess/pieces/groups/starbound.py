from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.piece import Piece


class Star(Piece):
    name = 'Star'
    file_name = 'sfRbB'
    asset_folder = 'starbound'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.RiderMovement(board, symv([(1, 0), (0, 1), (-1, 1)])),
            **kwargs
        )


class Lancer(Piece):
    name = 'Lancer'
    file_name = 'KfR'
    asset_folder = 'starbound'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.RiderMovement(board, symv([(1, 0), (1, 1, 1), (0, 1, 1), (-1, 1, 1), (-1, 0, 1)])),
            **kwargs
        )


class SineRdr(Piece):
    name = 'Sinerider'
    file_name = 'fFmfafFfafmFmfaqFfaqmFsRbB'
    asset_folder = 'starbound'

    def __init__(self, board, **kwargs):
        movements = [movement.RiderMovement(board, symv([(0, 1), (-1, 1)]))]
        for i, j in rot([(1, 1)]):
            movements.append(
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(1, i, 1)]),
                    movement.RiderMovement(board, [(1, j, 1)])
                ])
            )
            movements.append(
                movement.ChainMovement(board, [
                    movement.MultiMovement(board, capture=[
                        movement.RiderMovement(board, [(1, i, 1)])
                    ]),
                    movement.MultiMovement(board, move=[
                        movement.RiderMovement(board, [(1, j, 1), (0, 0)])
                    ])
                ])
            )
        super().__init__(
            board,
            movement.MultiMovement(board, movements),
            **kwargs
        )


class Turneagle(Piece):
    name = 'Turneagle'
    file_name = 'FmcaFR'
    asset_folder = 'starbound'

    def __init__(self, board, **kwargs):
        movements = [movement.RiderMovement(board, rot([(1, 0)]))]
        for i, j in rot([(1, 1)]):
            movements.append(
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [
                        (k, l, 1) for k, l in rot([(1, 1)]) if (i, j) != (-k, -l)
                    ])
                ])
            )
            movements.append(
                movement.ChainMovement(board, [
                    movement.MultiMovement(board, capture=[
                        movement.RiderMovement(board, [(i, j, 1)])
                    ]),
                    movement.MultiMovement(board, move_or_capture=[
                        movement.RiderMovement(board, [
                            (k, l, 1) for k, l in rot([(1, 1)]) + [(0, 0)] if (i, j) != (-k, -l)
                        ])
                    ])
                ])
            )
        super().__init__(
            board,
            movement.MultiMovement(board, movements),
            **kwargs
        )
