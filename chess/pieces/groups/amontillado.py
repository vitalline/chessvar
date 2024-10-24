from chess.movement import types
from chess.movement.util import rot, symv
from chess.pieces.piece import Piece


class Hasdrubal(Piece):
    name = 'Hasdrubal'
    file_name = 'fsbbNNhhR'
    asset_folder = 'amontillado'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [
                types.RiderMovement(board, symv([(1, 2), (-2, 1)])),
                types.HalflingRiderMovement(board, rot([(1, 0)]))
            ]),
            **kwargs
        )


class Barcfil(Piece):
    name = 'Barcfil'
    file_name = 'AfsbbN'
    asset_folder = 'amontillado'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, symv([(1, 2, 1), (2, 2, 1), (-2, 1, 1), (-2, 2, 1)])),
            **kwargs
        )


class Bed(Piece):
    name = 'Bed'
    file_name = 'hhBD'
    asset_folder = 'amontillado'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [
                types.RiderMovement(board, rot([(2, 0, 1)])),
                types.HalflingRiderMovement(board, rot([(1, 1)]))
            ]),
            **kwargs
        )


class Hamilcar(Piece):
    name = 'Hamilcar'
    file_name = 'fsbbNNffbsNhhQ'
    asset_folder = 'amontillado'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [
                types.RiderMovement(board, symv([(1, 2), (-2, 1), (2, 1, 1), (-1, 2, 1)])),
                types.HalflingRiderMovement(board, rot([(1, 0), (1, 1)]))
            ]),
            **kwargs
        )
