from chess.movement import movement
from chess.movement.util import rot
from chess.pieces.pieces import Piece


class MachineRdr(Piece):
    name = 'Machine Rider'
    file_name = 'WD2[W-D][D-W]'
    asset_folder = 'multimove'

    def __init__(self, board, board_pos, side):
        movements = [movement.RiderMovement(board, rot([(2, 0, 2)]))]
        for i, j in rot([(1, 0)]):
            for k, l in [(1, 2), (2, 1)]:
                movements.append(
                    movement.BentMovement(board, [
                        movement.RiderMovement(board, [(k * i, k * j, 1)]),
                        movement.RiderMovement(board, [(l * i, l * j, 1)])
                    ])
                )
        super().__init__(board, board_pos, side, movement.MultiMovement(board, movements))


class Allnight(Piece):
    name = 'Allnight'
    file_name = 'AN'
    asset_folder = 'multimove'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 2, 1), (2, 1, 1), (2, 2, 1)]))
        )


class Tusker(Piece):
    name = 'Tusker'
    file_name = 'FA2asmpafFmpafasF'
    asset_folder = 'multimove'

    def __init__(self, board, board_pos, side):
        movements = [movement.RiderMovement(board, rot([(2, 2, 2)]))]
        for i, j in rot([(1, 1)]):
            for k, l in [(1, 2), (2, 1)]:
                movements.append(
                    movement.BentMovement(board, [
                        movement.RiderMovement(board, [(k * i, k * j, 1)]),
                        movement.RiderMovement(board, [(l * -i, l * j, 1), (l * i, l * -j, 1)])
                    ])
                )
        super().__init__(board, board_pos, side, movement.MultiMovement(board, movements))

class Hierophant(Piece):
    name = 'Hierophant'
    file_name = 'KD2A2[W-D][D-W][F-A][A-F]'
    asset_folder = 'multimove'

    def __init__(self, board, board_pos, side):
        movements = [movement.RiderMovement(board, rot([(2, 0, 2), (2, 2, 2)]))]
        for i, j in rot([(1, 0), (1, 1)]):
            for k, l in [(1, 2), (2, 1)]:
                movements.append(
                    movement.BentMovement(board, [
                        movement.RiderMovement(board, [(k * i, k * j, 1)]),
                        movement.RiderMovement(board, [(l * i, l * j, 1)])
                    ])
                )
        super().__init__(board, board_pos, side, movement.MultiMovement(board, movements))
