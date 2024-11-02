from chess.pieces.piece import Piece
from chess.pieces.side import Side
from chess.pieces.types import Immune


class NonMovingPiece(Piece):
    name = '(Non-moving Piece)'
    file_name = 'none'
    asset_folder = 'util'
    default_side = Side.NONE

    def __init__(self, board, **kwargs):
        kwargs['side'] = self.default_side
        kwargs['movement'] = None
        super().__init__(board, **kwargs)

    def __str__(self):
        return '???' if self.is_hidden else self.name.strip()

    def of(self, side: Side) -> Piece:
        side = self.default_side
        return super().of(side)


class NoPiece(NonMovingPiece):
    name = '(Nothing)'

    def is_empty(self):
        return True


class Obstacle(NonMovingPiece):
    name = '(Obstacle)'
    file_name = 'square'
    default_side = Side.NEUTRAL

    def __init__(self, board, **kwargs):
        super().__init__(board, **kwargs)
        self.color = board.color_scheme.get('wall_color', board.color_scheme['background_color'])

    def is_empty(self):
        return False


class Block(Obstacle):
    name = 'Block'
    file_name = 'block'


class Border(Obstacle, Immune):
    name = 'Border'
    file_name = 'square'


class Wall(Obstacle, Immune):
    name = 'Wall'
    file_name = 'wall'
