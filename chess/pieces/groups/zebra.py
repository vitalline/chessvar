from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.pieces import Piece


class Zed(Piece):
    name = 'Zed'
    file_name = 'ZD'
    asset_folder = 'zebra'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(2, 0, 1), (2, 3, 1), (3, 2, 1)]))
        )


class Officer(Piece):
    name = 'Officer'
    file_name = 'ZfKbW'
    asset_folder = 'zebra'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(-1, 0, 1), (1, 0, 1), (1, 1, 1)]) + rot([(2, 3, 1), (3, 2, 1)]))
        )


class Levey(Piece):
    name = 'Levey'
    file_name = 'B2afafsF'
    asset_folder = 'zebra'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 2)]),
                    movement.RiderMovement(board, [(k, l, 1)])
                ]) for i, j in rot([(1, 1)]) for k, l in ((i, 0), (0, j))
            ])
        )


class Relish(Piece):
    name = 'Relish'
    file_name = 'RafsWafsafW'
    asset_folder = 'zebra'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [movement.RiderMovement(board, rot([(1, 0)]))] + [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(i or k, j or k, 2)])
                ]) for i, j in rot([(1, 0)]) for k in (1, -1)
            ])
        )
