from chess.pieces.pieces import Piece, Side


class NoPiece(Piece):
    name = '(No Piece)'
    file_name = 'none'
    asset_folder = 'util'

    def __init__(self, board, board_pos, side=Side.NONE, **kwargs):
        super().__init__(board, board_pos, Side.NONE, **kwargs)
        self.side = side

    def is_empty(self):
        return True
