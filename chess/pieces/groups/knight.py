from chess.movement import movement
from chess.movement.util import sym, symv
from chess.pieces.pieces import Piece


class Forerook(Piece):
    name = 'Forerook'
    file_name = 'fsRbhK'
    asset_folder = 'knight'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(1, 0), (0, 1), (-1, 0, 1), (-1, 1, 1)]))
        )


class Fibnif(Piece):
    name = 'Fibnif'
    file_name = 'fbNF'
    asset_folder = 'knight'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, sym([(1, 1, 1), (2, 1, 1)]))
        )


class Foreknight(Piece):
    name = 'Foreknight'
    file_name = 'fNbhsK'
    asset_folder = 'knight'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(2, 1, 1), (1, 2, 1), (0, 1, 1), (-1, 0, 1), (-1, 1, 1)]))
        )


class Colonel(Piece):
    name = 'Colonel'
    file_name = 'fhNfsRK'
    asset_folder = 'knight'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(
                board, sym([(1, 1, 1)]) + symv([(2, 1, 1), (1, 2, 1), (1, 0), (0, 1), (-1, 0, 1), (-1, 1, 1)])
            )
        )
