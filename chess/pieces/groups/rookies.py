from chess.movement import movement
from chess.movement.util import sym, rot
from chess.pieces import pieces


class ShortRook(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Short Rook',
            file_name=f'{side.file_name()}_warden',
            asset_folder='restrictors',
            movement=movement.RiderMovement(board, rot([(1, 0, 4)]))
        )


class WoodyRook(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Woody Rook',
            file_name=f'{side.file_name()}_woodland_rook',
            asset_folder='woodland',
            movement=movement.RiderMovement(board, rot([(1, 0, 1), (2, 0, 1)]))
        )


class HalfDuck(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Half Duck',
            file_name=f'{side.file_name()}_zora_knight',
            asset_folder='zora',
            movement=movement.RiderMovement(board, rot([(1, 1, 1), (2, 0, 1), (3, 0, 1)]))
        )


class Chancellor(pieces.Piece):
    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            name='Chancellor',
            file_name=f'{side.file_name()}_chancellor',
            asset_folder='medieval',
            movement=movement.RiderMovement(board, rot([(1, 0), (1, 2, 1), (2, 1, 1)]))
        )
