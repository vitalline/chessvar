from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.piece import Piece


class Eliphas(Piece):
    name = 'Eliphas'
    file_name = 'WafsWafsafW'
    asset_folder = 'zebra'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(i or k, j or k, 2)])
                ]) for i, j in rot([(1, 0)]) for k in (1, -1)
            ]),
            **kwargs
        )


class Sorcerer(Piece):
    name = 'Sorcerer'
    file_name = 'ZW'
    asset_folder = 'zebra'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (2, 3, 1), (3, 2, 1)])),
            **kwargs
        )


class Adze(Piece):
    name = 'Adze'
    file_name = 'ZA'
    asset_folder = 'zebra'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(2, 2, 1), (2, 3, 1), (3, 2, 1)])),
            **kwargs
        )


class IMarauder(Piece):
    name = 'Contramarauder'
    file_name = 'Fafs(afz)F'
    asset_folder = 'zebra'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.RepeatMovement(board, [
                    movement.RiderMovement(board, [(i or k, j or k, 1)]),
                    movement.RiderMovement(board, [(i, j, 1)])
                ]) for i, j in rot([(1, 0)]) for k in (1, -1)
            ]),
            **kwargs
        )
