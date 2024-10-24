from chess.movement import types
from chess.movement.util import rot, symv
from chess.pieces.piece import Piece


class Paladin(Piece):
    name = 'Paladin'
    file_name = 'NmWcF'
    asset_folder = 'pawn'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(
                board,
                move_or_capture=[types.RiderMovement(board, rot([(1, 2, 1), (2, 1, 1)]))],
                move=[types.RiderMovement(board, rot([(1, 0, 1)]))],
                capture=[types.RiderMovement(board, rot([(1, 1, 1)]))]
            ),
            **kwargs
        )


class Guarddog(Piece):
    name = 'Guarddog'
    file_name = 'mfRcfBfsbbNN'
    asset_folder = 'pawn'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(
                board,
                move_or_capture=[types.RiderMovement(board, symv([(1, 2), (-2, 1)]))],
                move=[types.RiderMovement(board, [(1, 0)])],
                capture=[types.RiderMovement(board, symv([(1, 1)]))]
            ),
            **kwargs
        )


class Stewardess(Piece):
    name = 'Stewardess'
    file_name = 'mRcB'
    asset_folder = 'pawn'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(
                board,
                move=[types.RiderMovement(board, rot([(1, 0)]))],
                capture=[types.RiderMovement(board, rot([(1, 1)]))]
            ),
            **kwargs
        )


class Dowager(Piece):
    name = 'Dowager'
    file_name = 'mRcBffbsNN'
    asset_folder = 'pawn'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(
                board,
                move_or_capture=[types.RiderMovement(board, symv([(2, 1), (-1, 2)]))],
                move=[types.RiderMovement(board, rot([(1, 0)]))],
                capture=[types.RiderMovement(board, rot([(1, 1)]))]
            ),
            **kwargs
        )
