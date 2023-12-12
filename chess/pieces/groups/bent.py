from chess.movement import movement
from chess.movement.util import rot
from chess.pieces import pieces


class LGriffon(pieces.Piece):
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
            ])
        )


class RGriffon(pieces.Piece):
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
            ])
        )
        self.scale_x = -1
        self.rotation = 180


class LAanca(pieces.Piece):
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
            ])
        )
        self.scale_x = -1
        self.rotation = 180


class RAanca(pieces.Piece):
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
            ])
        )


class LSastik(pieces.Piece):
    name = 'Left Sastik'
    file_name = 'celtic_eiwaz'
    asset_folder = 'celtic'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(2, 0, 1), (2, -1, 1)]))
        )
        self.scale_x = -1
        self.rotation = 180


class RSastik(pieces.Piece):
    name = 'Right Sastik'
    file_name = 'celtic_eiwaz'
    asset_folder = 'celtic'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(2, 0, 1), (2, 1, 1)]))
        )


class Griffon(pieces.Piece):
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

