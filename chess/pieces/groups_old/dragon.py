from chess.movement import movement
from chess.movement.util import rot, sym
from chess.pieces.pieces import Piece


class DragonHorse(Piece):
    name = 'Dragon Horse'
    file_name = 'kelpie'
    asset_folder = 'fantasy'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, rot([(1, 1), (1, 0, 1)]))
        )


class Dragonfly(Piece):
    name = 'Dragonfly'
    file_name = 'angel'
    asset_folder = 'fantasy'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.RiderMovement(board, sym([(1, 0), (1, 2, 1)]))
        )


class Dragoon(Piece):
    name = 'Dragoon'
    file_name = 'guardian'
    asset_folder = 'medieval'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(
                board,
                [movement.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1)]))],
                [movement.FirstMoveRiderMovement(board, [], sym([(2, 1, 1)]))]
            )
        )


class Wyvern(Piece):
    name = 'Wyvern'
    file_name = 'dragon'
    asset_folder = 'fantasy'

    def __init__(self, board, board_pos, side):
        super().__init__(
            board, board_pos, side,
            movement.MultiMovement(board, [
                movement.RiderMovement(board, sym([(1, 1), (2, 1, 1)])),
                *(movement.BentMovement(board, [
                    movement.RiderMovement(board, [(0, 2 * i, 1)]),
                    movement.RiderMovement(board, [(0, 1 * i)])
                ]) for i in (1, -1))
            ])
        )
