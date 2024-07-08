from copy import deepcopy
from math import ceil

from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.pieces import Piece


class Bard(Piece):
    name = 'Bard'
    file_name = 'DfsbbNN'
    asset_folder = 'nocturnal'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(2, 0, 1)]) + symv([(1, 2), (-2, 1)])),
            **kwargs
        )


class Nightsling(Piece):
    name = 'Nightsling'
    file_name = 'NmNNcpNN'
    asset_folder = 'nocturnal'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(
                board,
                move=[
                    movement.RiderMovement(board, rot([(1, 2), (2, 1)]))
                ],
                capture=[
                    movement.RiderMovement(board, rot([(1, 2, 1), (2, 1, 1)])),
                    movement.CannonRiderMovement(board, rot([(1, 2), (2, 1)]))
                ]
            ),
            **kwargs
        )


class MoaRdr(Piece):
    name = 'Moarider'
    file_name = 'afs(afzafz)F'
    asset_folder = 'nocturnal'

    def __init__(self, board, board_pos, side, **kwargs):
        movements = []
        for i, j in rot([(1, 0)]):
            for k in (1, -1):
                rider_movements = []
                for m in range(int(ceil(max(board.board_width, board.board_height) / 2))):
                    rider_movements.append(movement.RiderMovement(board, [(i or k, j or k, 1)]))
                    rider_movements.append(movement.RiderMovement(board, [(i, j, 1)]))
                    movements.append(movement.BentMovement(board, deepcopy(rider_movements), m * 2 + 1))
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, movements),
            **kwargs
        )


class Nanking(Piece):
    name = 'Nanking'
    file_name = 'NNK'
    asset_folder = 'nocturnal'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1), (1, 2), (2, 1)])),
            **kwargs
        )
