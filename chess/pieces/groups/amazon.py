from chess.movement import types
from chess.movement.util import rot
from chess.pieces.piece import Piece


class Cannon(Piece):
    name = 'Cannon'
    file_name = 'mRcpR'
    asset_folder = 'amazon'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(
                board,
                move=[types.RiderMovement(board, rot([(1, 0)]))],
                capture=[types.CannonRiderMovement(board, rot([(1, 0)]))]
            ),
            **kwargs
        )


class Camel(Piece):
    name = 'Camel'
    file_name = 'C'
    asset_folder = 'amazon'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 3, 1), (3, 1, 1)])),
            **kwargs
        )


class NightRdr(Piece):
    name = 'Nightrider'
    file_name = 'NN'
    asset_folder = 'amazon'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 2), (2, 1)])),
            **kwargs
        )


class Amazon(Piece):
    name = 'Amazon'
    file_name = 'QN'
    asset_folder = 'amazon'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0), (1, 1), (1, 2, 1), (2, 1, 1)])),
            **kwargs
        )
