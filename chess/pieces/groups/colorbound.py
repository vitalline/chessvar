from chess.movement import movement
from chess.movement.util import rot, sym
from chess.pieces import pieces


class Bede(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Bede',
            file_name=f'{side.file_name()}_zora_bishop',
            asset_folder='zora',
            movement=movement.RiderMovement(board, rot([(1, 1), (2, 0, 1)]))
        )


class Waffle(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Waffle',
            file_name=f'{side.file_name()}_sorcerer',
            asset_folder='fantasy',
            movement=movement.RiderMovement(board, rot([(1, 0, 1), (2, 2, 1)]))
        )


class FAD(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='FAD',
            file_name=f'{side.file_name()}_beholder',
            asset_folder='fantasy',
            movement=movement.RiderMovement(board, rot([(1, 1, 1), (2, 0, 1), (2, 2, 1)]))
        )


class Cardinal(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Cardinal',
            file_name=f'{side.file_name()}_archbishop',
            asset_folder='medieval',
            movement=movement.RiderMovement(board, sym([(1, 1), (1, 2, 1), (2, 1, 1)]))
        )


class King(pieces.RoyalPiece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='King',
            file_name=f'{side.file_name()}_king',
            asset_folder='classic',
            movement=movement.MultiMovement(
                board, [
                    movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1)])),
                    movement.CastlingMovement(board, (0, 2), (0, 3), (0, -2), [(0, 1), (0, 2)]),
                    movement.CastlingMovement(board, (0, -3), (0, -4), (0, 2), [(0, -1), (0, -2), (0, -3)]),
                ]
            )
        )