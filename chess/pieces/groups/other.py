from chess.movement import movement
from chess.movement.util import rot, sym, symv
from chess.pieces.pieces import Piece


class DupliKnight(Piece):
    name = 'Dupli-Knight'
    file_name = 'aN'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.ChainMovement(
                board, [
                    movement.RiderMovement(board, sym([(1, 2, 1), (2, 1, 1)])),
                    movement.RiderMovement(board, sym([(1, 2, 1), (2, 1, 1)]))
                ]
            )
        )


class Knife(Piece):
    name = 'Knife'
    file_name = 'NF'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, sym([(1, 1, 1), (1, 2, 1), (2, 1, 1)]))
        )


class Gnomon(Piece):
    name = 'Gnomon'
    file_name = 'vNvWnH'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, sym([(0, 1, 3, 3), (1, 0, 1), (2, 1, 1), (1, 0, 3, 3)]))
        )


class Crabster(Piece):
    name = 'Crabster'
    file_name = 'ffbsNfAbF'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(2, 1, 1), (2, 2, 1), (-1, 1, 1), (-1, 2, 1)]))
        )


class Caddy(Piece):
    name = 'Caddy'
    file_name = 'CD'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 3, 1), (3, 1, 1), (2, 0, 1)]))
        )


class Unicorn(Piece):
    name = 'Unicorn'
    file_name = 'N[mW-B]'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [movement.RiderMovement(board, sym([(1, 2, 1), (2, 1, 1)]))] + [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i + k, j + l, 1)]),
                    movement.RiderMovement(board, [(i, j, 0, 1)])
                ], 1) for i, j in rot([(1, 1)]) for k, l in ((-i, 0), (0, -j))
            ])
        )


class Tower(Piece):
    name = 'Tower'
    file_name = 'HnA'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(3, 0, 1), (1, 1, 2, 2)]))
        )


class Muskrat(Piece):
    name = 'Muskrat'
    file_name = 'sbRfB'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(-1, 0), (0, 1), (1, 1)]))
        )


class Guard2(Piece):
    name = 'Guardpotentate'
    file_name = 'Q2'
    asset_folder = 'horse'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 2), (1, 1, 2)]))
        )


class Mammoth(Piece):
    name = 'Mammoth'
    file_name = 'R4nA'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 4), (1, 1, 2, 2)]))
        )


class Kirin(Piece):
    name = 'Kirin'
    file_name = 'FD'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1, 1), (2, 0, 1)]))
        )


class Deacon(Piece):
    name = 'Deacon'
    file_name = 'B4W'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 4)]))
        )


class Brigadier(Piece):
    name = 'Brigadier'
    file_name = 'R4FN'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 4), (1, 1, 1), (1, 2, 1), (2, 1, 1)]))
        )


class Zed(Piece):
    name = 'Zed'
    file_name = 'ZD'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(2, 0, 1), (2, 3, 1), (3, 2, 1)]))
        )


class Officer(Piece):
    name = 'Officer'
    file_name = 'ZfKbW'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, symv([(-1, 0, 1), (1, 0, 1), (1, 1, 1)]) + rot([(2, 3, 1), (3, 2, 1)]))
        )


class Levey(Piece):
    name = 'Levey'
    file_name = 'B2afafsF'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 2)]),
                    movement.RiderMovement(board, [(k, l, 1)])
                ]) for i, j in rot([(1, 1)]) for k, l in ((i, 0), (0, j))
            ])
        )


class Relish(Piece):
    name = 'Relish'
    file_name = 'RafsWafsafW'
    asset_folder = 'other'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [movement.RiderMovement(board, rot([(1, 0)]))] + [
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [(i or k, j or k, 2)])
                ]) for i, j in rot([(1, 0)]) for k in (1, -1)
            ])
        )
