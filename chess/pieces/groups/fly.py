from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.pieces import Piece


class Quetzal(Piece):
    name = 'Quetzal'
    file_name = 'pQ'
    asset_folder = 'fly'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.CannonRiderMovement(board, rot([(1, 0), (1, 1)]))
        )


class Owl(Piece):
    name = 'Owl'
    file_name = 'WAA'
    asset_folder = 'fly'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (2, 2)]))
        )


class Hoatzin(Piece):
    name = 'Hoatzin'
    file_name = 'F[F-DD]'
    asset_folder = 'fly'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i or k, j or k, 1)]),
                    movement.RiderMovement(board, [(i * 2, j * 2)])
                ]) for i, j in rot([(1, 0)]) for k in (1, -1)
            ])
        )


class Eagle(Piece):
    name = 'Eagle'
    file_name = 'RbBfFfAcfafF'
    asset_folder = 'fly'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.RiderMovement(board, rot([(1, 0)]) + symv([(-1, 1), (1, 1, 1), (2, 2, 1)]))
            ] + [
                movement.ChainMovement(board, [
                    movement.MultiMovement(board, capture=[
                        movement.RiderMovement(board, [(i, j, 1)])
                    ]),
                    movement.MultiMovement(board, move_or_capture=[
                        movement.RiderMovement(board, [(i, j, 1), (0, 0)])
                    ])
                ]) for i, j in symv([(1, 1)])
            ])
        )
