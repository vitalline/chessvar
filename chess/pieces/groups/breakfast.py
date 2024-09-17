from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.piece import Piece


class Belwaffle(Piece):
    name = 'Belwaffle'
    file_name = 'pRWA'
    asset_folder = 'breakfast'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.RiderMovement(board, rot([(1, 0, 1), (2, 2, 1)])),
                movement.CannonRiderMovement(board, rot([(1, 0)]))
            ]),
            **kwargs
        )


class Pancake(Piece):
    name = 'Pancake'
    file_name = 'pNNK'
    asset_folder = 'breakfast'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1)])),
                movement.CannonRiderMovement(board, rot([(1, 2), (2, 1)]))
            ]),
            **kwargs
        )


class Bacon(Piece):
    name = 'Bacon'
    file_name = 'pBFD'
    asset_folder = 'breakfast'
    colorbound = True

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.RiderMovement(board, rot([(1, 1, 1), (2, 0, 1)])),
                movement.CannonRiderMovement(board, rot([(1, 1)]))
            ]),
            **kwargs
        )


class Omelet(Piece):
    name = 'Omelet'
    file_name = 'pQK'
    asset_folder = 'breakfast'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1)])),
                movement.CannonRiderMovement(board, rot([(1, 0), (1, 1)]))
            ]),
            **kwargs
        )
