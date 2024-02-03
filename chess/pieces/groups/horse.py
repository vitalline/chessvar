from copy import deepcopy
from math import ceil

from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece


class Guard2(Piece):
    name = 'Guardpotentate'
    file_name = 'Q2'
    asset_folder = 'horse'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 2), (1, 1, 2)]))
        )


class Horserider(Piece):
    name = 'Horserider'
    file_name = 'Wafs(afzafz)W'
    asset_folder = 'horse'

    def __init__(self, board, board_pos, side):
        movements = []
        for i, j in rot([(1, 0)]):
            for k in (1, -1):
                rider_movements = []
                for m in range(int(ceil(max(board.board_width, board.board_height) / 2))):
                    rider_movements.append(movement.RiderMovement(board, [(i, j, 1)]))
                    rider_movements.append(movement.RiderMovement(board, [(i or k, j or k, 1)]))
                    movements.append(movement.BentMovement(board, deepcopy(rider_movements), m * 2 + 1))
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, movements)
        )


class Elephas(Piece):
    name = 'Elephas'
    file_name = 'WafsWafsafW'
    asset_folder = 'horse'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(i or k, j or k, 2)])
                ]) for i, j in rot([(1, 0)]) for k in (1, -1)
            ])
        )


class Marauder(Piece):
    name = 'Horserider'
    file_name = 'Wafs(afz)W'
    asset_folder = 'horse'

    def __init__(self, board, board_pos, side):
        movements = []
        for i, j in rot([(1, 0)]):
            for k in (1, -1):
                rider_movements = []
                for m in range(int(ceil(max(board.board_width, board.board_height) / 2))):
                    rider_movements.append(movement.RiderMovement(board, [(i, j, 1)]))
                    rider_movements.append(movement.RiderMovement(board, [(i or k, j or k, 1)]))
                movements.append(movement.BentMovement(board, rider_movements))
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, movements)
        )
