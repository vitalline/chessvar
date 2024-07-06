from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece


class Llama(Piece):
    name = 'Llama'
    file_name = 'R2afafsW'
    asset_folder = 'camel'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 2)]),
                    movement.RiderMovement(board, [(i or k, j or k, 1)])
                ]) for i, j in rot([(1, 0)]) for k in (1, -1)
            ])
        )


class Cashier(Piece):
    name = 'Cashier'
    file_name = 'CW'
    asset_folder = 'camel'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (1, 3, 1), (3, 1, 1)]))
        )


class Cabbage(Piece):
    name = 'Cabbage'
    file_name = 'BC'
    asset_folder = 'camel'
    colorbound = True

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1), (1, 3, 1), (3, 1, 1)]))
        )


class Warlock(Piece):
    name = 'Warlock'
    file_name = 'RCF'
    asset_folder = 'camel'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0), (1, 1, 1), (1, 3, 1), (3, 1, 1)]))
        )
