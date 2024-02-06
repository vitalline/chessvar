from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece, RoyalPiece


class Bede(Piece):
    name = 'Bede'
    file_name = 'BD'
    asset_folder = 'colorbound'

    def __init__(self, board, board_pos, side):

        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1), (2, 0, 1)]))
        )


class Waffle(Piece):
    name = 'Waffle'
    file_name = 'WA'
    asset_folder = 'colorbound'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (2, 2, 1)]))
        )


class Fad(Piece):
    name = 'Fad'
    file_name = 'FAD'
    asset_folder = 'colorbound'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1, 1), (2, 0, 1), (2, 2, 1)]))
        )


class Archbishop(Piece):
    name = 'Archbishop'
    file_name = 'BN'
    asset_folder = 'colorbound'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1), (1, 2, 1), (2, 1, 1)]))
        )


class King(RoyalPiece):
    name = 'King'
    file_name = 'K'
    asset_folder = 'classic'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(
                board, [
                    movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1)])),
                    movement.CastlingMovement(board, (0, 2), (0, 3), (0, -2), [(0, 1), (0, 2)]),
                    movement.CastlingMovement(board, (0, -3), (0, -4), (0, 2), [(0, -1), (0, -2), (0, -3)])
                ]
            )
        )
