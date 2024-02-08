from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.pieces import Piece


class ElkRdr(Piece):
    name = 'Elkrider'
    file_name = '(NNl,Rd)'
    asset_folder = 'color'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.ColorMovement(
                board,
                light=[movement.RiderMovement(board, rot([(1, 2), (2, 1)]))],
                dark=[movement.RiderMovement(board, rot([(1, 0)]))]
            )
        )


class CaribRdr(Piece):
    name = 'Caribourider'
    file_name = '(Rl,NNd)'
    asset_folder = 'color'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.ColorMovement(
                board,
                light=[movement.RiderMovement(board, rot([(1, 0)]))],
                dark=[movement.RiderMovement(board, rot([(1, 2), (2, 1)]))]
            )
        )


class DCannon(Piece):
    name = 'Deuterocannon'
    file_name = '(mRcpRl,Nd)'
    asset_folder = 'color'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.ColorMovement(
                board,
                light=[movement.MultiMovement(
                    board,
                    move=[movement.RiderMovement(board, rot([(1, 0)]))],
                    capture=[movement.CannonRiderMovement(board, rot([(1, 0)]))]
                )],
                dark=[movement.RiderMovement(board, rot([(1, 2, 1), (2, 1, 1)]))]
            )
        )


class Nightlight(Piece):
    name = 'Nightlight'
    file_name = '(fBbhNl,FW[W-DD]d)'
    asset_folder = 'color'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.ColorMovement(
                board,
                light=[movement.RiderMovement(board, symv([(-1, 2, 1), (-2, 1, 1), (1, 1)]))],
                dark=[movement.MultiMovement(board, [movement.RiderMovement(board, rot([(1, 1, 1)]))] + [
                    movement.BentMovement(board, [
                        movement.RiderMovement(board, [(i, j, 1)]),
                        movement.RiderMovement(board, [(2 * i, 2 * j)])
                    ]) for i, j in rot([(1, 0)])
                ])]
            )
        )


class Nanqueen(Piece):
    name = 'Nanqueen'
    file_name = '(Qi,NNKo)'
    asset_folder = 'color'

    def __init__(self, board, board_pos, side):
        starting_movement = movement.RiderMovement(board, rot([(1, 0), (1, 1)]))
        opposite_movement = movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1), (1, 2), (2, 1)]))
        super().__init__(
            board, board_pos, side,
            movement.ColorMovement(
                board,
                light=[starting_movement if board.is_light_square(board_pos) else opposite_movement],
                dark=[starting_movement if board.is_dark_square(board_pos) else opposite_movement]
            )
        )
