from chess.movement import movement
from chess.movement.util import rot, sym
from chess.pieces.pieces import Piece


class Panda(Piece):
    name = 'Panda'
    file_name = 'paladin'
    asset_folder = 'medieval'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.ChainMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(2 * i, 2 * j)])
                ]) for i, j in rot([(1, 0)])
            ])
        )


class Marquis(Piece):
    name = 'Marquis'
    file_name = 'tailor'
    asset_folder = 'medieval'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (1, 2, 1), (2, 1, 1)]))
        )


class Unicorn(Piece):
    name = 'Unicorn'
    file_name = 'unicorn'
    asset_folder = 'fantasy'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [movement.RiderMovement(board, sym([(1, 2, 1), (2, 1, 1)]))] + [
                movement.ChainMovement(board, [
                    movement.RiderMovement(board, [(i + k, j + l, 1)]),
                    movement.RiderMovement(board, [(i, j, 0, 1)])
                ], 1) for i, j in rot([(1, 1)]) for k, l in ((-i, 0), (0, -j))
            ])
        )


class ErlQueen(Piece):
    name = 'Erl Queen'
    file_name = 'minister'
    asset_folder = 'medieval'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.ChainMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(2 * i, 2 * j)])
                ]) for i, j in rot([(1, 0), (1, 1)])
            ])
        )
