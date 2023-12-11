from chess.pieces.pieces import Piece, Side


class NoPiece(Piece):
    def __init__(self, board, board_pos, side=Side.NONE):
        super().__init__(
            board, board_pos, side,
            name='',
            file_name=f'none',
            asset_folder='util',
            movement=None
        )
