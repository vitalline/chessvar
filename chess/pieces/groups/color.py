from chess.movement import movement
from chess.movement.util import rot, symv
from chess.pieces.piece import Piece
from chess.pieces.side import Side


class ElkRdr(Piece):
    name = 'Elkrider'
    file_name = '(NNw,Rb)'
    asset_folder = 'color'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.ColorMovement(
                board,
                light=[movement.RiderMovement(board, rot([(1, 2), (2, 1)]))],
                dark=[movement.RiderMovement(board, rot([(1, 0)]))],
            ),
            **kwargs
        )


class CaribRdr(Piece):
    name = 'Caribourider'
    file_name = '(Rw,NNb)'
    asset_folder = 'color'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.ColorMovement(
                board,
                light=[movement.RiderMovement(board, rot([(1, 0)]))],
                dark=[movement.RiderMovement(board, rot([(1, 2), (2, 1)]))],
            ),
            **kwargs
        )


class DCannon(Piece):
    name = 'Deuterocannon'
    file_name = '(mRcpRw,Nb)'
    asset_folder = 'color'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.ColorMovement(
                board,
                light=[movement.MultiMovement(
                    board,
                    move=[movement.RiderMovement(board, rot([(1, 0)]))],
                    capture=[movement.CannonRiderMovement(board, rot([(1, 0)]))]
                )],
                dark=[movement.RiderMovement(board, rot([(1, 2, 1), (2, 1, 1)]))],
            ),
            **kwargs
        )


class Nightlight(Piece):
    name = 'Nightlight'
    file_name = '(fBbhNw,FW[W-DD]b)'
    asset_folder = 'color'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            movement.ColorMovement(
                board,
                light=[movement.RiderMovement(board, symv([(-1, 2, 1), (-2, 1, 1), (1, 1)]))],
                dark=[movement.MultiMovement(board, [movement.RiderMovement(board, rot([(1, 1, 1)]))] + [
                    movement.BentMovement(board, [
                        movement.RiderMovement(board, [(i, j, 1)]),
                        movement.RiderMovement(board, [(2 * i, 2 * j)])
                    ]) for i, j in rot([(1, 0)])
                ])],
            ),
            **kwargs
        )


class Nanqueen(Piece):
    name = 'Nanqueen'
    file_name = '(Qi,NNKo)'
    asset_folder = 'color'

    def __init__(self, board, **kwargs):
        same_color_movement = movement.RiderMovement(board, rot([(1, 0), (1, 1)]))
        different_color_movement = movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1), (1, 2), (2, 1)]))
        side = kwargs.get('side')
        if side == Side.WHITE:
            start_pos = (0, board.board_width // 2 - 1)
        elif side == Side.BLACK:
            start_pos = (board.board_height - 1, board.board_width // 2 - 1)
        else:
            super().__init__(board, movement.ColorMovement(board), **kwargs)
            return
        super().__init__(
            board,
            movement.ColorMovement(
                board,
                light=[same_color_movement if board.is_light_square(start_pos) else different_color_movement],
                dark=[same_color_movement if board.is_dark_square(start_pos) else different_color_movement]
            ),
            **kwargs
        )
