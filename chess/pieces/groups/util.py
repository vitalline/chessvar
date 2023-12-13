from chess.pieces.pieces import Piece, Side


class NoPiece(Piece):
    name = ''
    file_name = 'none'
    asset_folder = 'util'

    def __init__(self, board, board_pos, side=Side.NONE):
        super().__init__(board, board_pos, Side.NONE)
        self.side = side
