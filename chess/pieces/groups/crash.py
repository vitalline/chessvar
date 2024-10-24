from chess.movement import types
from chess.movement.util import rot, symv
from chess.pieces.piece import Piece


class Merlion(Piece):
    name = 'Merlion'
    file_name = 'ADcK'
    asset_folder = 'crash'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(
                board,
                move_or_capture=[types.RiderMovement(board, rot([(2, 0, 1), (2, 2, 1)]))],
                capture=[types.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1)]))]
            ),
            **kwargs
        )


class Biskni(Piece):
    name = 'Biskni'
    file_name = 'mBcN'
    asset_folder = 'crash'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(
                board,
                move=[types.RiderMovement(board, rot([(1, 1)]))],
                capture=[types.RiderMovement(board, rot([(1, 2, 1), (2, 1, 1)]))]
            ),
            **kwargs
        )


class IStewardess(Piece):
    name = 'Contrastewardess'
    file_name = 'mBcR'
    asset_folder = 'crash'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(
                board,
                move=[types.RiderMovement(board, rot([(1, 1)]))],
                capture=[types.RiderMovement(board, rot([(1, 0)]))]
            ),
            **kwargs
        )


class IPaladess(Piece):
    name = 'Antipaladess'
    file_name = 'NmBcR'
    asset_folder = 'crash'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(
                board,
                move_or_capture=[types.RiderMovement(board, symv([(1, 2, 1), (2, 1, 1)]))],
                move=[types.RiderMovement(board, rot([(1, 1)]))],
                capture=[types.RiderMovement(board, rot([(1, 0)]))]
            ),
            **kwargs
        )
