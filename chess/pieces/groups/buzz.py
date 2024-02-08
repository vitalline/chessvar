from chess.movement import movement
from chess.movement.util import rot, sym, symh, symv
from chess.pieces.pieces import Piece


class Mosquito(Piece):
    name = 'Mosquito'
    file_name = 'WvNsDD'
    asset_folder = 'buzz'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1)]) + sym([(2, 1, 1), (0, 2)]))
        )


class Dragonfly(Piece):
    name = 'Dragonfly'
    file_name = 'vRsN'
    asset_folder = 'buzz'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, sym([(1, 0), (1, 2, 1)]))
        )


class Locust(Piece):
    name = 'Locust'
    file_name = 'vWvDDsNN'
    asset_folder = 'buzz'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, sym([(1, 0, 1), (2, 0), (1, 2)]))
        )


class Mantis(Piece):
    name = 'Mantis'
    file_name = 'BvNsDmpsafyasW'
    asset_folder = 'buzz'

    def __init__(self, board, board_pos, side):
        movements = [movement.RiderMovement(board, sym([(1, 1), (2, 1, 1)]))]
        for i, j in symv([(0, 2)]):
            for k, l in symh([(1, 0)]):
                movements.append(
                    movement.BentMovement(board, [
                        movement.RiderMovement(board, [(i, j, 1)]),
                        movement.RiderMovement(board, [(k, l)])
                    ])
                )
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, movements)
        )
