from chess.movement import types
from chess.movement.util import rot, rot2, symh
from chess.pieces.piece import Piece


class LQue(Piece):
    name = 'Left Que'
    file_name = 'sRflbrB'
    asset_folder = 'asymmetry'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot2([(0, -1), (1, -1)])),
            **kwargs
        )


class RQue(Piece):
    name = 'Right Que'
    file_name = 'sRfrblB'
    asset_folder = 'asymmetry'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot2([(0, 1), (1, 1)])),
            **kwargs
        )


class Knish(Piece):
    name = 'Knish'
    file_name = '(lBrhNl,rBlhNr)'
    asset_folder = 'asymmetry'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.SideMovement(
                board,
                left=[types.RiderMovement(board, symh([(1, -1), (1, 2, 1), (2, 1, 1)]))],
                right=[types.RiderMovement(board, symh([(1, 1), (1, -2, 1), (2, -1, 1)]))],
            ),
            **kwargs
        )


class Blizzard(Piece):
    name = 'Blizzard'
    file_name = '(FflbrBfrrfbllbCl,FfrblBfllfbrrbCr)'
    asset_folder = 'asymmetry'
    colorbound = True

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.SideMovement(
                board,
                left=[types.RiderMovement(board, rot2([(1, -1), (1, 1, 1), (1, 3, 1), (3, 1, 1)]))],
                right=[types.RiderMovement(board, rot2([(1, 1), (1, -1, 1), (1, -3, 1), (3, -1, 1)]))],
            ),
            **kwargs
        )


class Chanqueen(Piece):
    name = 'Chanqueen'
    file_name = '(RlBrhNl,RrBlhNr)'
    asset_folder = 'asymmetry'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.SideMovement(
                board,
                left=[types.RiderMovement(board, rot([(1, 0)]) + symh([(1, -1), (1, 2, 1), (2, 1, 1)]))],
                right=[types.RiderMovement(board, rot([(1, 0)]) + symh([(1, 1), (1, -2, 1), (2, -1, 1)]))],
            ),
            **kwargs
        )
