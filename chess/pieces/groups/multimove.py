from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.piece import Piece


class MachineRdr(Piece):
    name = 'Machinerider'
    file_name = 'WD2[W-D][D-W]'
    asset_folder = 'multimove'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [movement.RiderMovement(board, rot([(2, 0, 2)]))] + [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(k * i, k * j, 1)]),
                    movement.RiderMovement(board, [(l * i, l * j, 1)])
                ]) for i, j in rot([(1, 0)]) for k, l in [(1, 2), (2, 1)]
            ]),
            **kwargs
        )


class Allnight(Piece):
    name = 'Allnight'
    file_name = 'AN'
    asset_folder = 'multimove'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 2, 1), (2, 1, 1), (2, 2, 1)])),
            **kwargs
        )


class Tusker(Piece):
    name = 'Tusker'
    file_name = 'FA2asmpafFmpafasF'
    asset_folder = 'multimove'
    colorbound = True

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [movement.RiderMovement(board, rot([(2, 2, 2)]))] + [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(k * i, k * j, 1)]),
                    movement.RiderMovement(board, [(l * -i, l * j, 1), (l * i, l * -j, 1)])
                ]) for i, j in rot([(1, 1)]) for k, l in [(1, 2), (2, 1)]
            ]),
            **kwargs
        )


class Hierophant(Piece):
    name = 'Hierophant'
    file_name = 'KD2A2[W-D][D-W][F-A][A-F]'
    asset_folder = 'multimove'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [movement.RiderMovement(board, rot([(2, 0, 2), (2, 2, 2)]))] + [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(k * i, k * j, 1)]),
                    movement.RiderMovement(board, [(l * i, l * j, 1)])
                ]) for i, j in rot([(1, 0), (1, 1)]) for k, l in [(1, 2), (2, 1)]
            ]),
            **kwargs
        )
