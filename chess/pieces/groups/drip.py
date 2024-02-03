from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.pieces import Piece


class Muskrat(Piece):
    name = 'Muskrat'
    file_name = 'sbRfB'
    asset_folder = 'drip'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(-1, 0), (0, 1), (1, 1)]))
        )


class Crabrider(Piece):
    name = 'Crabrider'
    file_name = 'ffbsNN'
    asset_folder = 'drip'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(2, 1), (-1, 2)])),
        )


class Wizard(Piece):
    name = 'Wizard'
    file_name = 'CF'
    asset_folder = 'drip'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1, 1), (1, 3, 1), (3, 1, 1)]))
        )


class Eagle(Piece):
    name = 'Eagle'
    file_name = 'RbBfFfAcfafF'
    asset_folder = 'drip'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
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
            ])
        )
