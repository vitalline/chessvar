from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.pieces import Piece


class Hasdrubal(Piece):
    name = 'Hasdrubal'
    file_name = 'fsbbNNhhR'
    asset_folder = 'amontillado'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.RiderMovement(board, symv([(1, 2), (-2, 1)])),
                movement.HalflingRiderMovement(board, rot([(1, 0)]))
            ])
        )


class Barcfil(Piece):
    name = 'Barcfil'
    file_name = 'AfsbbN'
    asset_folder = 'amontillado'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(1, 2, 1), (2, 2, 1), (-2, 1, 1), (-2, 2, 1)]))
        )

class Bed(Piece):
    name = 'Bed'
    file_name = 'hhBD'
    asset_folder = 'amontillado'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.RiderMovement(board, rot([(2, 0, 1)])),
                movement.HalflingRiderMovement(board, rot([(1, 1)]))
            ])
        )


class Hamilcar(Piece):
    name = 'Hamilcar'
    file_name = 'fsbbNNffbsNhhQ'
    asset_folder = 'amontillado'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.RiderMovement(board, symv([(1, 2), (-2, 1), (2, 1, 1), (-1, 2, 1)])),
                movement.HalflingRiderMovement(board, rot([(1, 0), (1, 1)]))
            ])
        )
