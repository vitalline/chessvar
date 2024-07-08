from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.pieces import Piece


class ElkRdr(Piece):
    name = 'Elkrider'
    file_name = '(Rb,NNw)'
    asset_folder = 'color'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.ColorMovement(
                board,
                dark=[movement.RiderMovement(board, rot([(1, 0)]))],
                light=[movement.RiderMovement(board, rot([(1, 2), (2, 1)]))],
            ),
            **kwargs
        )


class CaribRdr(Piece):
    name = 'Caribourider'
    file_name = '(NNb,Rw)'
    asset_folder = 'color'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.ColorMovement(
                board,
                dark=[movement.RiderMovement(board, rot([(1, 2), (2, 1)]))],
                light=[movement.RiderMovement(board, rot([(1, 0)]))],
            ),
            **kwargs
        )


class DCannon(Piece):
    name = 'Deuterocannon'
    file_name = '(Nb,mRcpRw)'
    asset_folder = 'color'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.ColorMovement(
                board,
                dark=[movement.RiderMovement(board, rot([(1, 2, 1), (2, 1, 1)]))],
                light=[movement.MultiMovement(
                    board,
                    move=[movement.RiderMovement(board, rot([(1, 0)]))],
                    capture=[movement.CannonRiderMovement(board, rot([(1, 0)]))]
                )],
            ),
            **kwargs
        )


class Nightlight(Piece):
    name = 'Nightlight'
    file_name = '(FW[W-DD]b,fBbhNw)'
    asset_folder = 'color'

    def __init__(self, board, board_pos, side, **kwargs):
        super().__init__(
            board, board_pos, side,
            movement.ColorMovement(
                board,
                dark=[movement.MultiMovement(board, [movement.RiderMovement(board, rot([(1, 1, 1)]))] + [
                    movement.BentMovement(board, [
                        movement.RiderMovement(board, [(i, j, 1)]),
                        movement.RiderMovement(board, [(2 * i, 2 * j)])
                    ]) for i, j in rot([(1, 0)])
                ])],
                light=[movement.RiderMovement(board, symv([(-1, 2, 1), (-2, 1, 1), (1, 1)]))],
            ),
            **kwargs
        )


class Nanqueen(Piece):
    name = 'Nanqueen'
    file_name = '(Qi,NNKo)'
    asset_folder = 'color'

    def __init__(self, board, board_pos, side, **kwargs):
        starting_movement = movement.RiderMovement(board, rot([(1, 0), (1, 1)]))
        opposite_movement = movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1), (1, 2), (2, 1)]))
        super().__init__(
            board, board_pos, side,
            movement.ColorMovement(
                board,
                light=[starting_movement if board.is_light_square(board_pos) else opposite_movement],
                dark=[starting_movement if board.is_dark_square(board_pos) else opposite_movement]
            ),
            **kwargs
        )
