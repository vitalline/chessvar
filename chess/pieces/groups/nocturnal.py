from chess.movement import types
from chess.movement.util import rot, symv
from chess.pieces.piece import Piece


class Bard(Piece):
    name = 'Bard'
    file_name = 'DfsbbNN'
    asset_folder = 'nocturnal'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(2, 0, 1)]) + symv([(1, 2), (-2, 1)])),
            **kwargs
        )


class Nightsling(Piece):
    name = 'Nightsling'
    file_name = 'NmNNcpNN'
    asset_folder = 'nocturnal'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(
                board,
                move=[
                    types.RiderMovement(board, rot([(1, 2), (2, 1)]))
                ],
                capture=[
                    types.RiderMovement(board, rot([(1, 2, 1), (2, 1, 1)])),
                    types.CannonRiderMovement(board, rot([(1, 2), (2, 1)]))
                ]
            ),
            **kwargs
        )


class MoaRdr(Piece):
    name = 'Moarider'
    file_name = 'afs(afzafz)F'
    asset_folder = 'nocturnal'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.MultiMovement(board, [
                types.RepeatMovement(board, [
                    types.RiderMovement(board, [(i, j, 1)]),
                    types.RiderMovement(board, [(i, 0, 1), (0, j, 1)])
                ], 1) for i, j in rot([(1, 1)])
            ]),
            **kwargs
        )


class Nanking(Piece):
    name = 'Nanking'
    file_name = 'NNK'
    asset_folder = 'nocturnal'

    def __init__(self, board, **kwargs):
        super().__init__(
            board,
            types.RiderMovement(board, rot([(1, 0, 1), (1, 1, 1), (1, 2), (2, 1)])),
            **kwargs
        )
