from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece


class Veteran(Piece):
    name = 'Veteran'
    file_name = '{R,KAD}'
    asset_folder = 'probable'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.ProbabilisticMovement(board, [
                movement.RiderMovement(board, rot([(1, 0)])),
                movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1), (2, 0, 1), (2, 2, 1)]))
            ]),
            **kwargs
        )


class RedPanda(Piece):
    name = 'Red Panda'
    file_name = '{W[W-DD],N}'
    asset_folder = 'probable'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.ProbabilisticMovement(board, [
                movement.MultiMovement(board, [
                    movement.BentMovement(board, [
                        movement.RiderMovement(board, [(i, j, 1)]),
                        movement.RiderMovement(board, [(2 * i, 2 * j)])
                    ]) for i, j in rot([(1, 0)])
                ]),
                movement.RiderMovement(board, rot([(1, 2, 1), (2, 1, 1)]))
            ]),
            **kwargs
        )


class Tempofad(Piece):
    name = 'Tempofad'
    file_name = '{B,FAD}'
    asset_folder = 'probable'
    colorbound = True

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.ProbabilisticMovement(board, [
                movement.RiderMovement(board, rot([(1, 1)])),
                movement.RiderMovement(board, rot([(1, 1, 1), (2, 0, 1), (2, 2, 1)]))
            ]),
            **kwargs
        )


class WaterBuffalo(Piece):
    name = 'Water Buffalo'
    file_name = '{Q,NCZ}'
    asset_folder = 'probable'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.ProbabilisticMovement(board, [
                movement.RiderMovement(board, rot([(1, 0), (1, 1)])),
                movement.RiderMovement(board, rot([(1, 2, 1), (1, 3, 1), (2, 1, 1), (2, 3, 1), (3, 1, 1), (3, 2, 1)]))
            ]),
            **kwargs
        )
