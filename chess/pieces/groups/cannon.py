from chess.movement import movement
from chess.movement.util import rot, sym
from chess.pieces.piece import Piece


class Howitzer(Piece):
    name = 'Howitzer'
    file_name = 'WssRmpR'
    asset_folder = 'cannon'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.MultiMovement(
                board,
                move_or_capture=[
                    movement.RiderMovement(board, rot([(1, 0, 1)])),
                    movement.SpaciousRiderMovement(board, rot([(1, 0)]))
                ], move=[
                    movement.CannonRiderMovement(board, rot([(1, 0)]))
                ]
            ),
            **kwargs
        )


class Mortar(Piece):
    name = 'Mortar'
    file_name = 'WssRcpR'
    asset_folder = 'cannon'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.MultiMovement(
                board,
                move_or_capture=[
                    movement.RiderMovement(board, rot([(1, 0, 1)])),
                    movement.SpaciousRiderMovement(board, rot([(1, 0)]))
                ],
                capture=[
                    movement.CannonRiderMovement(board, rot([(1, 0)]))
                ]
            ),
            **kwargs
        )


class Napoleon(Piece):
    name = 'Napoleon'
    file_name = 'fbNW'
    asset_folder = 'cannon'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.RiderMovement(board, rot([(1, 0, 1)]) + sym([(2, 1, 1)])),
            **kwargs
        )


class Carronade(Piece):
    name = 'Carronade'
    file_name = 'ssBpB'
    asset_folder = 'cannon'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.MultiMovement(board, [
                # movement.RiderMovement(board, rot([(1, 1, 1)])),
                movement.SpaciousRiderMovement(board, rot([(1, 1)])),
                movement.CannonRiderMovement(board, rot([(1, 1)]))
            ]),
            **kwargs
        )


class Bertha(Piece):
    name = 'Bertha'
    file_name = 'WssQpQ'
    asset_folder = 'cannon'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.MultiMovement(board, [
                movement.RiderMovement(board, rot([(1, 0, 1)])),
                # movement.RiderMovement(board, rot([(1, 1, 1)])),
                movement.SpaciousRiderMovement(board, rot([(1, 0)])),
                movement.SpaciousRiderMovement(board, rot([(1, 1)])),
                movement.CannonRiderMovement(board, rot([(1, 0)])),
                movement.CannonRiderMovement(board, rot([(1, 1)]))
            ]),
            **kwargs
        )

