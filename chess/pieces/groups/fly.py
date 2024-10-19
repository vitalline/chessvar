from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.piece import Piece


class Quetzal(Piece):
    name = 'Quetzal'
    file_name = 'pQ'
    asset_folder = 'fly'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.CannonRiderMovement(board, rot([(1, 0), (1, 1)])),
            **kwargs
        )


class Owl(Piece):
    name = 'Owl'
    file_name = 'WAA'
    asset_folder = 'fly'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.RiderMovement(board, rot([(1, 0, 1), (2, 2)])),
            **kwargs
        )


class Hoatzin(Piece):
    name = 'Hoatzin'
    file_name = 'F[F-DD]'
    asset_folder = 'fly'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(2 * i, 0), (0, 2 * j)])
                ]) for i, j in rot([(1, 1)])
            ]),
            **kwargs
        )


class Eagle(Piece):
    name = 'Eagle'
    file_name = 'RfFfAbBcfafF'
    asset_folder = 'fly'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.MultiMovement(board, [
                movement.RiderMovement(board, rot([(1, 0)]) + symv([(-1, 1), (1, 1, 1), (2, 2, 1)]))
            ] + [
                movement.ChainMovement(board, [
                    movement.MultiMovement(board, capture=[
                        movement.RiderMovement(board, [(i, j, 1)])
                    ]),
                    movement.MultiMovement(board, move_or_capture=[
                        movement.RiderMovement(board, [(i, j, 1), (0, 0)])
                    ])
                ]) for i, j in symv([(1, 1)])
            ]),
            **kwargs
        )
