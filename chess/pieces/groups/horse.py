from copy import deepcopy
from math import ceil

from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece


class Naysayer(Piece):
    name = 'Naysayer'
    file_name = 'nAAnH'
    asset_folder = 'horse'

    def __init__(self, board, board_pos, side):
        movements = []
        for i, j in rot([(1, 1)]):
            rider_movements = []
            for m in range(int(ceil(max(board.board_width, board.board_height) / 2))):
                rider_movements.append(movement.RiderMovement(board, [(i, j, 2, 2)]))
            movements.append(movement.BentMovement(board, rider_movements))
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [movement.RiderMovement(board, rot([(1, 0, 3, 3)]))] + movements)
        )


class Horserider(Piece):
    name = 'Horserider'
    file_name = 'afs(afzafz)W'
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


class Tapir(Piece):
    name = 'Tapir'
    file_name = 'afsWnA'
    asset_folder = 'horse'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [movement.RiderMovement(board, rot([(1, 1, 2, 2)]))] + [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(i or k, j or k, 1)])
                ]) for i, j in rot([(1, 0)]) for k in (1, -1)
            ])
        )


class Marauder(Piece):
    name = 'Marauder'
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
