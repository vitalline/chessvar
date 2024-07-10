from chess.pieces.pieces import Piece, Side


class NoPiece(Piece):
    name = '(No Piece)'
    file_name = 'none'
    asset_folder = 'util'

    def __init__(self, board, board_pos, **kwargs):
        kwargs['side'] = Side.NONE
        super().__init__(board, board_pos, **kwargs)

    def is_empty(self):
        return True
