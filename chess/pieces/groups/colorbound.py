from chess.movement import movement
from chess.movement.util import rot, sym
from chess.pieces.pieces import Piece, RoyalPiece


class Bede(Piece):
    name = 'Bede'
    file_name = 'zora_bishop'
    asset_folder = 'zora'

    def __init__(self, board, board_pos, side):

        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1), (2, 0, 1)]))
        )


class Waffle(Piece):
    name = 'Waffle'
    file_name = 'sorcerer'
    asset_folder = 'fantasy'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (2, 2, 1)]))
        )


class FAD(Piece):
    name = 'FAD'
    file_name = 'beholder'
    asset_folder = 'fantasy'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1, 1), (2, 0, 1), (2, 2, 1)]))
        )


class Cardinal(Piece):
    name = 'Cardinal'
    file_name = 'archbishop'
    asset_folder = 'medieval'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, sym([(1, 1), (1, 2, 1), (2, 1, 1)]))
        )


class King(RoyalPiece):
    name = 'King'
    file_name = 'king'
    asset_folder = 'classic'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(
                board, [
                    movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1)])),
                    movement.CastlingMovement(board, (0, 2), (0, 3), (0, -2), [(0, 1), (0, 2)]),
                    movement.CastlingMovement(board, (0, -3), (0, -4), (0, 2), [(0, -1), (0, -2), (0, -3)]),
                ]
            )
        )
