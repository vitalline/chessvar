from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.pieces import Piece


class Whelk(Piece):
    name = 'Whelk'
    file_name = 'fWfDsbR'
    asset_folder = 'backward'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(1, 0, 1), (2, 0, 1), (0, 1), (-1, 0)]))
        )


class Walrus(Piece):
    name = 'Walrus'
    file_name = 'fNfRbhQ'
    asset_folder = 'backward'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(1, 0), (2, 1, 1), (-1, 0), (-1, 1)]))
        )


class Seagull(Piece):
    name = 'Seagull'
    file_name = 'fFfAsbBcfafF'
    asset_folder = 'backward'
    colorbound = True

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.RiderMovement(board, symv([(1, 1, 1), (2, 2, 1), (-1, 1)]))
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


class Shark(Piece):
    name = 'Shark'
    file_name = 'RfhNbB'
    asset_folder = 'backward'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0)]) + symv([(1, 2, 1), (2, 1, 1), (-1, 1)]))
        )
