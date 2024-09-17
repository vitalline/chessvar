from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.piece import Piece


class Paladin(Piece):
    name = 'Paladin'
    file_name = 'NmWcF'
    asset_folder = 'pawn'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(
                board,
                move_or_capture=[movement.RiderMovement(board, rot([(1, 2, 1), (2, 1, 1)]))],
                move=[movement.RiderMovement(board, rot([(1, 0, 1)]))],
                capture=[movement.RiderMovement(board, rot([(1, 1, 1)]))]
            ),
            **kwargs
        )


class Guarddog(Piece):
    name = 'Guarddog'
    file_name = 'mfRcfBfsbbNN'
    asset_folder = 'pawn'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(
                board,
                move_or_capture=[movement.RiderMovement(board, symv([(1, 2), (-2, 1)]))],
                move=[movement.RiderMovement(board, [(1, 0)])],
                capture=[movement.RiderMovement(board, symv([(1, 1)]))]
            ),
            **kwargs
        )


class Stewardess(Piece):
    name = 'Stewardess'
    file_name = 'mRcB'
    asset_folder = 'pawn'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(
                board,
                move=[movement.RiderMovement(board, rot([(1, 0)]))],
                capture=[movement.RiderMovement(board, rot([(1, 1)]))]
            ),
            **kwargs
        )


class Dowager(Piece):
    name = 'Dowager'
    file_name = 'mRcBffbsNN'
    asset_folder = 'pawn'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(
                board,
                move_or_capture=[movement.RiderMovement(board, symv([(2, 1), (-1, 2)]))],
                move=[movement.RiderMovement(board, rot([(1, 0)]))],
                capture=[movement.RiderMovement(board, rot([(1, 1)]))]
            ),
            **kwargs
        )
