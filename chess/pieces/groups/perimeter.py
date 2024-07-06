from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece


class Fencer(Piece):
    name = 'Fencer'
    file_name = 'NH'
    asset_folder = 'perimeter'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 2, 1), (2, 1, 1), (3, 0, 1)]))
        )


class Castle(Piece):
    name = 'Castle'
    file_name = 'nDnNnA'
    asset_folder = 'perimeter'

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
                        ], 1),
                    ])
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, movements)
        )


class Kirin(Piece):
    name = 'Kirin'
    file_name = 'FD'
    asset_folder = 'perimeter'
    colorbound = True

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1, 1), (2, 0, 1)]))
        )


class Fort(Piece):
    name = 'Fort'
    file_name = 'WAND'
    asset_folder = 'perimeter'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (1, 2, 1), (2, 0, 1), (2, 1, 1), (2, 2, 1)]))
        )
