from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.piece import Piece


class Heart(Piece):
    name = 'Heart'
    file_name = 'hhRA'
    asset_folder = 'hobbit'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.MultiMovement(board, [
                movement.RiderMovement(board, rot([(2, 2, 1)])),
                movement.HalflingRiderMovement(board, rot([(1, 0)]))
            ]),
            **kwargs
        )


class Drake(Piece):
    name = 'Drake'
    file_name = 'FhhyafsF'
    asset_folder = 'hobbit'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i or k, j or k, 1)]),
                    movement.HalflingRiderMovement(board, [(i, j)], 1)
                ]) for i, j in rot([(1, 0)]) for k in (1, -1)
            ]),
            **kwargs
        )


class Barcinal(Piece):
    name = 'Barcinal'
    file_name = 'fsbbNhhB'
    asset_folder = 'hobbit'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.MultiMovement(board, [
                movement.RiderMovement(board, symv([(1, 2, 1), (-2, 1, 1)])),
                movement.HalflingRiderMovement(board, rot([(1, 1)]))
            ]),
            **kwargs
        )


class Hannibal(Piece):
    name = 'Hannibal'
    file_name = 'hhNNhhQ'
    asset_folder = 'hobbit'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.HalflingRiderMovement(board, rot([(1, 0), (1, 1), (1, 2), (2, 1)])),
            **kwargs
        )
