import math

from chess.movement import movement
from chess.movement.util import rot, sym, symv
from chess.pieces.pieces import Piece, Side


class LRhino(Piece):
    name = 'Left Rhino'
    file_name = 'KafrK'
    asset_folder = 'fizz'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.ChainMovement(board, [
                    movement.RiderMovement(board, [(*ij, 1)]),
                    movement.RiderMovement(board, [(*kl, 1)])
                ]) for ij, kl in zip(
                    [(1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0)],
                    [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)],
                )
            ]),
            side == Side.WHITE
        )


class RRhino(Piece):
    name = 'Right Rhino'
    file_name = 'KafrK'
    asset_folder = 'fizz'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.ChainMovement(board, [
                    movement.RiderMovement(board, [(*ij, 1)]),
                    movement.RiderMovement(board, [(*kl, 1)])
                ]) for ij, kl in zip(
                    [(1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0)],
                    [(0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1)],
                )
            ]),
            side == Side.BLACK
        )


class Gnohmon(Piece):
    name = 'Gnohmon'
    file_name = 'vNvWnH'
    asset_folder = 'fizz'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, sym([(0, 1, 3, 3), (1, 0, 1), (2, 1, 1), (1, 0, 3, 3)]))
        )


class Crabinal(Piece):
    name = 'Crabinal'
    file_name = 'ffNbsNhhB'
    asset_folder = 'fizz'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side
        )
        self.update_movement()

    def moves(self, theoretical: bool = False):
        self.update_movement()
        yield from super().moves(theoretical)

    def update_movement(self):
        self.movement = movement.MultiMovement(self.board, [
            movement.RiderMovement(self.board, symv([(2, 1, 1), (-1, 2, 1)]))
        ] + [
            movement.RiderMovement(self.board, [
                (i, j, max(1, min(
                    math.ceil(
                        ((self.board.board_height - self.board_pos[0] - 1)
                         if i == self.side.direction()
                         else self.board_pos[0]) / 2
                    ),
                    math.ceil(
                        ((self.board.board_width - self.board_pos[1] - 1)
                         if j > 0
                         else self.board_pos[1]) / 2
                    )
                )))
            ]) for i, j in rot([(1, 1)])
        ])


class EagleScout(Piece):
    name = 'Eagle Scout'
    file_name = 'WzFF'
    asset_folder = 'fizz'

    def __init__(self, board, board_pos, side):
        chain_movements = []
        for i, j in [(1, 1), (-1, 1), (-1, -1), (1, -1)]:
            for k, l in [(-i, j), (i, -j)]:
                rider_movements = []
                for m in range(int(math.ceil(max(board.board_width, board.board_height) / 2))):
                    rider_movements.append(movement.RiderMovement(board, [(i, j, 1)]))
                    rider_movements.append(movement.RiderMovement(board, [(k, l, 1)]))
                chain_movements.append(movement.ChainMovement(board, rider_movements))
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [movement.RiderMovement(board, rot([(1, 0, 1)]))] + chain_movements)
        )
