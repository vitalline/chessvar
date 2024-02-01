from chess.movement import movement
from chess.movement.util import rot, sym
from chess.pieces.pieces import Piece


class Howitzer(Piece):
    name = 'Howitzer'
    file_name = 'WssRmpR'
    asset_folder = 'cannon'

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
    file_name = 'WssRcpR'
    asset_folder = 'cannon'

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
            )
        )


class Carronade(Piece):
    name = 'Carronade'
    file_name = 'FssBpB'
    asset_folder = 'cannon'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(
                board,
                move_or_capture=[
                    movement.RiderMovement(board, rot([(1, 1, 1)])),
                    movement.SpaciousRiderMovement(board, rot([(1, 1)])),
                    movement.CannonRiderMovement(board, rot([(1, 1)])),
                ],
            )
        )


class Bertha(Piece):
    name = 'Bertha'
    file_name = 'KssQpQ'
    asset_folder = 'cannon'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(
                board,
                move_or_capture=[
                    movement.RiderMovement(board, rot([(1, 0, 1)])),
                    movement.RiderMovement(board, rot([(1, 1, 1)])),
                    movement.SpaciousRiderMovement(board, rot([(1, 0)])),
                    movement.SpaciousRiderMovement(board, rot([(1, 1)])),
                    movement.CannonRiderMovement(board, rot([(1, 0)])),
                    movement.CannonRiderMovement(board, rot([(1, 1)])),
                ],
            )
        )

