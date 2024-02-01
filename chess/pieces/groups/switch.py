from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece


class Panda(Piece):
    name = 'Panda'
    file_name = 'W[W-DD]'
    asset_folder = 'switch'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(2 * i, 2 * j)])
                ]) for i, j in rot([(1, 0)])
            ])
        )


class Marquis(Piece):
    name = 'Marquis'
    file_name = 'NW'
    asset_folder = 'switch'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (1, 2, 1), (2, 1, 1)]))
        )


class Bear(Piece):
    name = 'Bear'
    file_name = 'F[F-AA]'
    asset_folder = 'switch'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(2 * i, 2 * j)])
                ]) for i, j in rot([(1, 1)])
            ])
        )


class Pandabear(Piece):
    name = 'Pandabear'
    file_name = 'K[W-DD][F-AA]'
    asset_folder = 'switch'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(2 * i, 2 * j)])
                ]) for i, j in rot([(1, 0), (1, 1)])
            ])
        )
