import math

from chess.movement import movement
from chess.movement.util import Position, rot, sym, symv
from chess.pieces import pieces


class LRhino(pieces.Piece):
    name = 'Left Single-Step Rhino'
    file_name = 'king2'
    asset_folder = 'classic2'

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
            ])
        )
        self.scale_x = -1
        self.rotation = 180


class RRhino(pieces.Piece):
    name = 'Right Single-Step Rhino'
    file_name = 'king2'
    asset_folder = 'classic2'

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
            ])
        )


class Gnohmon(pieces.Piece):
    name = 'Gnohmon'
    file_name = 'courier_bishop'
    asset_folder = 'courier'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, sym([(0, 1, 3, 3), (1, 0, 1), (2, 1, 1), (1, 0, 3, 3)]))
        )


class Crabinal(pieces.Piece):
    name = 'Crabinal'
    file_name = 'swords'
    asset_folder = 'medieval'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side, None
        )
        self.update_movement(board_pos)

    def moves(self, pos: Position):
        self.update_movement(pos)
        yield from super().moves(pos)

    def update_movement(self, pos: Position):
        self.movement = movement.MultiMovement(self.board, [
            movement.RiderMovement(self.board, symv([(2, 1, 1), (-1, 2, 1)]))
        ] + [
            movement.RiderMovement(self.board, symv([
                (i, j, min(
                    math.ceil(((self.board.board_height - pos[0] - 1) if i > 0 else pos[0]) / 2),
                    math.ceil(((self.board.board_width - pos[1] - 1) if j > 0 else pos[1]) / 2)
                ))
            ])) for i, j in rot([(1, 1)])
        ])


class EagleScout(pieces.Piece):
    name = 'Eagle Scout'
    file_name = 'crow'
    asset_folder = 'nature'

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
