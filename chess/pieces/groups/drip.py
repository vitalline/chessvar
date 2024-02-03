from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.pieces import Piece


class Lobefin(Piece):
    name = 'Lobefin'
    file_name = 'DfAAbB'
    asset_folder = 'drip'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(2, 0)]) + symv([(2, 2), (-1, 1)])),
        )


class Crabrider(Piece):
    name = 'Crabrider'
    file_name = 'ffbsNN'
    asset_folder = 'drip'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(2, 1), (-1, 2)])),
        )


class Sandbar(Piece):
    name = 'Sandbar'
    file_name = 'WfDfsbbN'
    asset_folder = 'drip'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(1, 2, 1), (-2, 1, 1)]) + rot([(1, 0, 1)]) + [(2, 0, 1)]),
        )


class Oyster(Piece):
    name = 'Oyster'
    file_name = 'WfDffbsNNfAAbB'
    asset_folder = 'drip'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(2, 1), (2, 2), (-1, 1), (-1, 2)]) + rot([(1, 0, 1)]) + [(2, 0, 1)]),
        )
