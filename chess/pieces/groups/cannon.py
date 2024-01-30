from chess.movement import movement
from chess.movement.util import rot, sym
from chess.pieces.pieces import Piece


class Howitzer(Piece):
    name = 'Howitzer'
    file_name = 'cannon'
    asset_folder = 'medieval'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(
                board,
                move_or_capture=[
                    movement.RiderMovement(board, rot([(1, 0, 1)])),
                    movement.SpaciousRiderMovement(board, rot([(1, 0)])),
                ],
                move=[
                    movement.CannonRiderMovement(board, rot([(1, 0)])),
                ],
            )
        )


class Mortar(Piece):
    name = 'Mortar'
    file_name = 'cannon2'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(
                board,
                move_or_capture=[
                    movement.RiderMovement(board, rot([(1, 0, 1)])),
                    movement.SpaciousRiderMovement(board, rot([(1, 0)])),
                ],
                capture=[
                    movement.CannonRiderMovement(board, rot([(1, 0)])),
                ],
            ),
            True
        )


class Napoleon(Piece):
    name = 'Napoleon'
    file_name = 'archon'
    asset_folder = 'fantasy'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1)]) + sym([(2, 1, 1)]))
        )


class Carronade(Piece):
    name = 'Carronade'
    file_name = 'archer'
    asset_folder = 'medieval'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(
                board,
                move_or_capture=[
                    movement.SpaciousRiderMovement(board, rot([(1, 1)])),
                    movement.CannonRiderMovement(board, rot([(1, 1)])),
                ],
            )
        )


class BigBertha(Piece):
    name = 'Big Bertha'
    file_name = 'sentry'
    asset_folder = 'medieval'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(
                board,
                move_or_capture=[
                    movement.RiderMovement(board, rot([(1, 0, 1)])),
                    movement.SpaciousRiderMovement(board, rot([(1, 0)])),
                    movement.SpaciousRiderMovement(board, rot([(1, 1)])),
                    movement.CannonRiderMovement(board, rot([(1, 1)])),
                ],
                move=[
                    movement.CannonRiderMovement(board, rot([(1, 0)])),
                ],
            )
        )

