from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece, Side


class LGriffon(Piece):
    name = 'Left Griffon'
    file_name = 'griffin'
    asset_folder = 'fantasy'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.ChainMovement(board, [
                    movement.RiderMovement(board, [(*ij, 1)]),
                    movement.RiderMovement(board, [kl])
                ]) for ij, kl in zip(
                    [(1, 1), (-1, 1), (-1, -1), (1, -1)],
                    [(1, 0), (0, 1), (-1, 0), (0, -1)],
                )
            ]),
            side == Side.BLACK
        )


class RGriffon(Piece):
    name = 'Right Griffon'
    file_name = 'griffin'
    asset_folder = 'fantasy'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.ChainMovement(board, [
                    movement.RiderMovement(board, [(*ij, 1)]),
                    movement.RiderMovement(board, [kl])
                ]) for ij, kl in zip(
                    [(1, 1), (-1, 1), (-1, -1), (1, -1)],
                    [(0, 1), (-1, 0), (0, -1), (1, 0)],
                )
            ]),
            side == Side.WHITE
        )


class LAanca(Piece):
    name = 'Left Aanca'
    file_name = 'celtic_nauthiz'
    asset_folder = 'celtic'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.ChainMovement(board, [
                    movement.RiderMovement(board, [(*ij, 1)]),
                    movement.RiderMovement(board, [kl])
                ]) for ij, kl in zip(
                    [(1, 0), (0, 1), (-1, 0), (0, -1)],
                    [(1, -1), (1, 1), (-1, 1), (-1, -1)],
                )
            ]),
            side == Side.WHITE
        )


class RAanca(Piece):
    name = 'Right Aanca'
    file_name = 'celtic_nauthiz'
    asset_folder = 'celtic'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.ChainMovement(board, [
                    movement.RiderMovement(board, [(*ij, 1)]),
                    movement.RiderMovement(board, [kl])
                ]) for ij, kl in zip(
                    [(1, 0), (0, 1), (-1, 0), (0, -1)],
                    [(1, 1), (-1, 1), (-1, -1), (1, -1)],
                )
            ]),
            side == Side.BLACK
        )


class LSastik(Piece):
    name = 'Left Sastik'
    file_name = 'celtic_eiwaz'
    asset_folder = 'celtic'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(2, 0, 1), (2, -1, 1)])),
            side == Side.WHITE
        )


class RSastik(Piece):
    name = 'Right Sastik'
    file_name = 'celtic_eiwaz'
    asset_folder = 'celtic'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(2, 0, 1), (2, 1, 1)])),
            side == Side.BLACK
        )


class Griffon(Piece):
    name = 'Griffon'
    file_name = 'manticore'
    asset_folder = 'fantasy'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.ChainMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(k, l)])
                ]) for i, j in rot([(1, 1)]) for k, l in ((i, 0), (0, j))
            ])
        )
