from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece


class Bacon(Piece):
    name = 'Bacon'
    file_name = 'FpR'
    asset_folder = 'breakfast'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.RiderMovement(board, rot([(1, 1, 1)])),
                movement.CannonRiderMovement(board, rot([(1, 0)]))
            ])
        )


class Pancake(Piece):
    name = 'Pancake'
    file_name = 'pNNK'
    asset_folder = 'breakfast'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1)])),
                movement.CannonRiderMovement(board, rot([(1, 2), (2, 1)]))
            ])
        )


class Scramble(Piece):
    name = 'Scramble'
    file_name = 'pBmB'
    asset_folder = 'breakfast'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(
                board,
                move_or_capture=[
                    movement.CannonRiderMovement(board, rot([(1, 1)]))
                ],
                move=[
                    movement.RiderMovement(board, rot([(1, 1)]))
                ]
            )
        )


class Omelet(Piece):
    name = 'Omelet'
    file_name = 'KpQ'
    asset_folder = 'breakfast'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1)])),
                movement.CannonRiderMovement(board, rot([(1, 0), (1, 1)]))
            ])
        )
