import math

from chess.movement import movement
from chess.movement.util import mul, rot
from chess.pieces.pieces import Piece


class Hero(Piece):
    name = 'Hero'
    file_name = 'crusader'
    asset_folder = 'medieval'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.ChainMovement(board, [
                    movement.RiderMovement(board, [(*mul(ij, k), 1)]),
                    movement.RiderMovement(board, [(*mul(ij, 3 - k), 1)])
                ]) for ij in rot([(1, 0)]) for k in (1, 2)
            ])
        )


class Shaman(Piece):
    name = 'Shaman'
    file_name = 'monk'
    asset_folder = 'medieval'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.ChainMovement(board, [
                    movement.RiderMovement(board, [(*mul(ij, k), 1)]),
                    movement.RiderMovement(board, [(*mul(ij, 3 - k), 1)])
                ]) for ij in rot([(1, 1)]) for k in (1, 2)
            ])
        )


class WarElephant(Piece):
    name = 'War Elephant'
    file_name = 'elephant'
    asset_folder = 'nature'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.ChainMovement(board, [
                    movement.RiderMovement(board, [(*mul(ij, k), 1)]),
                    movement.RiderMovement(board, [(*mul(ij, 3 - k), 1)])
                ]) for ij in rot([(1, 0), (1, 1)]) for k in (1, 2)
            ])
        )

