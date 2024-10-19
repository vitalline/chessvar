from chess.movement import movement
from chess.movement.util import rot, symh, symv
from chess.pieces.piece import Piece


class Deerfly(Piece):
    name = 'Deerfly'
    file_name = 'vRK'
    asset_folder = 'narrow'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1)]) + symh([(1, 0)])),
            **kwargs
        )


class Ship(Piece):
    name = 'Ship'
    file_name = 'mpsyasW'
    asset_folder = 'narrow'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i or k, j or k, 1) for k in (1, -1)]),
                    movement.RiderMovement(board, [(i, j)])
                ]) for i, j in symh([(1, 0)])
            ]),
            **kwargs
        )


class Filescout(Piece):
    name = 'Filescout'
    file_name = 'Fmpvasabz(az)WsD'
    asset_folder = 'narrow'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.MultiMovement(board, [movement.RiderMovement(board, symv([(0, 2, 1)]))] + [
                movement.RepeatMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(i, -j, 1)])
                ]) for i, j in rot([(1, 1)])
            ]),
            **kwargs
        )


class Horsefly(Piece):
    name = 'Horsefly'
    file_name = 'vRNK'
    asset_folder = 'narrow'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1), (1, 2, 1), (2, 1, 1)]) + symh([(1, 0)])),
            **kwargs
        )
