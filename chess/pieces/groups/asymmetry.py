from chess.movement import movement
from chess.movement.util import rot, rot2, symh
from chess.pieces.pieces import Piece


class LBiok(Piece):
    name = 'Left Biok'
    file_name = 'sRflbrB'
    asset_folder = 'asymmetry'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot2([(0, -1), (1, -1)]))
        )


class RBiok(Piece):
    name = 'Right Biok'
    file_name = 'sRfrblB'
    asset_folder = 'asymmetry'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot2([(0, 1), (1, 1)]))
        )


class Knisher(Piece):
    name = 'Knisher'
    file_name = '(lBrhNl,rBlhNr)'
    asset_folder = 'asymmetry'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.SideMovement(
                board,
                left=[movement.RiderMovement(board, symh([(1, -1), (1, 2, 1), (2, 1, 1)]))],
                right=[movement.RiderMovement(board, symh([(1, 1), (1, -2, 1), (2, -1, 1)]))],
            )
        )


class Blizzard(Piece):
    name = 'Blizzard'
    file_name = '(FflbrBfrrfbllbCl,FfrblBfllfbrrbCr)'
    asset_folder = 'asymmetry'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.SideMovement(
                board,
                left=[movement.RiderMovement(board, rot2([(1, -1), (1, 1, 1), (1, 3, 1), (3, 1, 1)]))],
                right=[movement.RiderMovement(board, rot2([(1, 1), (1, -1, 1), (1, -3, 1), (3, -1, 1)]))],
            )
        )


class Archannel(Piece):
    name = 'Archannel'
    file_name = '(RlBrhNl,RrBlhNr)'
    asset_folder = 'asymmetry'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.SideMovement(
                board,
                left=[movement.RiderMovement(board, rot([(1, 0)]) + symh([(1, -1), (1, 2, 1), (2, 1, 1)]))],
                right=[movement.RiderMovement(board, rot([(1, 0)]) + symh([(1, 1), (1, -2, 1), (2, -1, 1)]))],
            )
        )
