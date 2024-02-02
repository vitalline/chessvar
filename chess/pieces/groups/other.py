from chess.movement import movement
from chess.movement.util import rot, sym, symv
from chess.pieces.pieces import Piece


class DupliKnight(Piece):
    name = 'Dupli-Knight'
    file_name = 'aN'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.ChainMovement(
                board, [
                    movement.RiderMovement(board, sym([(1, 2, 1), (2, 1, 1)])),
                    movement.RiderMovement(board, sym([(1, 2, 1), (2, 1, 1)]))
                ]
            )
        )


class Darter(Piece):
    name = 'Darter'
    file_name = 'fNWbAA'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1)]) + symv([(2, 1, 1), (-2, 2)]))
        )


class Unicorn(Piece):
    name = 'Unicorn'
    file_name = 'N[mW-B]'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [movement.RiderMovement(board, sym([(1, 2, 1), (2, 1, 1)]))] + [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i + k, j + l, 1)]),
                    movement.RiderMovement(board, [(i, j, 0, 1)])
                ], 1) for i, j in rot([(1, 1)]) for k, l in ((-i, 0), (0, -j))
            ])
        )
