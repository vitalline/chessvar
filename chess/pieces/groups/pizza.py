from chess.movement import movement
from chess.movement.util import rot, sym, symv
from chess.pieces.piece import Piece


class Pepperoni(Piece):
    name = 'Pepperoni'
    file_name = 'sDfAvWF'
    asset_folder = 'pizza'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.RiderMovement(board, symv([(2, 2, 1)]) + sym([(0, 2, 1), (1, 1, 1), (1, 0, 1)])),
            **kwargs
        )


class Mushroom(Piece):
    name = 'Mushroom'
    file_name = 'vNfsCbF'
    asset_folder = 'pizza'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.RiderMovement(board, symv([(2, 1, 1), (1, 3, 1), (-1, 1, 1), (-2, 1, 1)])),
            **kwargs
        )


class Sausage(Piece):
    name = 'Sausage'
    file_name = 'sWFvNvH'
    asset_folder = 'pizza'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.RiderMovement(board, sym([(3, 0, 1), (2, 1, 1), (1, 1, 1), (0, 1, 1)])),
            **kwargs
        )


class Meatball(Piece):
    name = 'Meatball'
    file_name = 'KADfN'
    asset_folder = 'pizza'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.RiderMovement(board, symv([(2, 1, 1)]) + rot([(1, 0, 1), (1, 1, 1), (2, 0, 1), (2, 2, 1)])),
            **kwargs
        )
