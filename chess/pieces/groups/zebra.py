from math import ceil

from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece


class Eliphas(Piece):
    name = 'Eliphas'
    file_name = 'WafsWafsafW'
    asset_folder = 'zebra'

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


class Sorcerer(Piece):
    name = 'Sorcerer'
    file_name = 'ZW'
    asset_folder = 'zebra'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (2, 3, 1), (3, 2, 1)]))
        )


class Adze(Piece):
    name = 'Adze'
    file_name = 'ZA'
    asset_folder = 'zebra'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(2, 2, 1), (2, 3, 1), (3, 2, 1)]))
        )


class IMarauder(Piece):
    name = 'Contramarauder'
    file_name = 'Fafs(afz)F'
    asset_folder = 'zebra'

    def __init__(self, board, board_pos, side):
        movements = []
        for i, j in rot([(1, 0)]):
            for k in (1, -1):
                rider_movements = []
                for m in range(int(ceil(max(board.board_width, board.board_height) / 2))):
                    rider_movements.append(movement.RiderMovement(board, [(i or k, j or k, 1)]))
                    rider_movements.append(movement.RiderMovement(board, [(i, j, 1)]))
                movements.append(movement.BentMovement(board, rider_movements))
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, movements)
        )
