from chess.movement import movement
from chess.movement.util import rot, sym
from chess.pieces.pieces import Piece, RoyalPiece


class Champion(Piece):
    name = 'Champion'
    file_name = 'WAD'
    asset_folder = 'stone'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 0, 1), (2, 0, 1), (2, 2, 1)]))
        )


class Tower(Piece):
    name = 'Tower'
    file_name = 'HnA'
    asset_folder = 'stone'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(3, 0, 1), (1, 1, 2, 2)]))
        )


class Stele(Piece):
    name = 'Stele'
    file_name = 'FmcaF'
    asset_folder = 'stone'

    def __init__(self, board, board_pos, side):
        movements = []
        for i, j in rot([(1, 1)]):
            movements.append(
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [
                        (k, l, 1) for k, l in rot([(1, 1)]) if (i, j) != (-k, -l)
                    ]),
                ])
            )
            movements.append(
                movement.ChainMovement(board, [
                    movement.MultiMovement(board, capture=[
                        movement.RiderMovement(board, [(i, j, 1)])
                    ]),
                    movement.MultiMovement(board, move_or_capture=[
                        movement.RiderMovement(board, [
                            (k, l, 1) for k, l in rot([(1, 1)]) + [(0, 0)] if (i, j) != (-k, -l)
                        ]),
                    ])
                ])
            )
        super().__init__(board, board_pos, side, movement.MultiMovement(board, movements))


class Caryatid(Piece):
    name = 'Caryatid'
    file_name = 'WmcaW'
    asset_folder = 'stone'

    def __init__(self, board, board_pos, side):
        movements = []
        for i, j in rot([(1, 0)]):
            movements.append(
                movement.BentMovement(board, [
                    movement.RiderMovement(board, [(i, j, 1)]),
                    movement.RiderMovement(board, [
                        (k, l, 1) for k, l in rot([(1, 0)]) if (i, j) != (-k, -l)
                    ]),
                ])
            )
            movements.append(
                movement.ChainMovement(board, [
                    movement.MultiMovement(board, capture=[
                        movement.RiderMovement(board, [(i, j, 1)])
                    ]),
                    movement.MultiMovement(board, move_or_capture=[
                        movement.RiderMovement(board, [
                            (k, l, 1) for k, l in rot([(1, 0)]) + [(0, 0)] if (i, j) != (-k, -l)
                        ]),
                    ])
                ])
            )
        super().__init__(board, board_pos, side, movement.MultiMovement(board, movements))
