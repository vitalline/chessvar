from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece


class Bireme(Piece):
    name = 'Bireme'
    file_name = 'D[D-R]'
    asset_folder = 'inadjacent'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(2 * i, 2 * j, 1)]),
                    movement.RiderMovement(board, [(i, j)])
                ]) for i, j in rot([(1, 0)])
            ]),
            **kwargs
        )


class Tigon(Piece):
    name = 'Tigon'
    file_name = 'nCnZ'
    asset_folder = 'inadjacent'

    def __init__(self, board, board_pos, side, **kwargs):
        movements = []
        for i, j in rot([(1, 0)]):
            for k in (1, -1):
                w = (i, j, 1)
                f = (i or k, j or k, 1)
                for directions in [(w, w, f), (w, f, f), (f, w, w), (f, f, w)]:
                    movements.extend([
                        movement.BentMovement(board, [
                            movement.RiderMovement(board, [direction]) for direction in directions
                        ], 2),
                    ])
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, movements),
            **kwargs
        )


class Bicycle(Piece):
    name = 'Bicycle'
    file_name = 'A[A-B]'
    asset_folder = 'inadjacent'
    colorbound = True

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(2 * i, 2 * j, 1)]),
                    movement.RiderMovement(board, [(i, j)])
                ]) for i, j in rot([(1, 1)])
            ]),
            **kwargs
        )


class Biplane(Piece):
    name = 'Biplane'
    file_name = 'D[D-R]A[A-B]'
    asset_folder = 'inadjacent'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(2 * i, 2 * j, 1)]),
                    movement.RiderMovement(board, [(i, j)])
                ]) for i, j in rot([(1, 0), (1, 1)])
            ]),
            **kwargs
        )
