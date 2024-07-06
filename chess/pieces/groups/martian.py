from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece


class Padwar(Piece):
    name = 'Padwar'
    file_name = 'WaaW'
    asset_folder = 'martian'

    def __init__(self, board, board_pos, side):
        movements = [movement.RiderMovement(board, rot([(1, 0, 1)]))]
        for i, j in rot([(1, 0)]):
            for k, l in rot([(1, 0)]):
                if (i, j) != (-k, -l):
                    movements.append(
                        movement.BentMovement(board, [
                            movement.RiderMovement(board, [(i, j, 1)]),
                            movement.RiderMovement(board, [(k, l, 1)]),
                            movement.RiderMovement(board, [
                                (m, n, 1) for m, n in rot([(1, 0)]) if (m, n) != (-i, -j) and (m, n) != (-k, -l)
                            ])
                        ], 2)
                    )
        super().__init__(board, board_pos, side, movement.MultiMovement(board, movements))


class Marker(Piece):
    name = 'Marker'
    file_name = 'avsK'
    asset_folder = 'martian'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, rot([(1, i, 1)])),
                    movement.RiderMovement(board, rot([(1, j, 1)]))
                ], 1) for i, j in [(0, 1), (1, 0)]
            ])
        )


class Walker(Piece):
    name = 'Walker'
    file_name = 'FaaF'
    asset_folder = 'martian'
    colorbound = True

    def __init__(self, board, board_pos, side):
        movements = [movement.RiderMovement(board, rot([(1, 1, 1)]))]
        for i, j in rot([(1, 1)]):
            for k, l in rot([(1, 1)]):
                if (i, j) != (-k, -l):
                    movements.append(
                        movement.BentMovement(board, [
                            movement.RiderMovement(board, [(i, j, 1)]),
                            movement.RiderMovement(board, [(k, l, 1)]),
                            movement.RiderMovement(board, [
                                (m, n, 1) for m, n in rot([(1, 1)]) if (m, n) != (-i, -j) and (m, n) != (-k, -l)
                            ])
                        ], 2)
                    )
        super().__init__(board, board_pos, side, movement.MultiMovement(board, movements))


class Chief(Piece):
    name = 'Chief'
    file_name = 'KnDnNnA'
    asset_folder = 'martian'

    def __init__(self, board, board_pos, side):
        movements = []
        for i, j in rot([(1, 0)]):
            for k in (1, -1):
                w = (i, j, 1)
                f = (i or k, j or k, 1)
                for directions in [(w, w), (w, f), (f, w), (f, f)]:
                    movements.extend([
                        movement.BentMovement(board, [
                            movement.RiderMovement(board, [direction]) for direction in directions
                        ]),
                    ])
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, movements)
        )
