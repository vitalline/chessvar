from chess.pieces.piece import Piece
from chess.pieces.side import Side
from chess.pieces.types import Empty, Immune


class UtilityPiece(Piece):
    name = '(Utility Piece)'
    default_side = Side.NONE

    def __init__(self, board, **kwargs):
        if kwargs.get('side') is None:
            kwargs['side'] = self.default_side
        super().__init__(board, **kwargs)
        self.should_hide = False
        self.is_hidden = False

    def reload(self, *args, **kwargs):
        self.should_hide = False
        self.is_hidden = False

    @classmethod
    def type(cls) -> str:
        return cls.__name__

    def __str__(self):
        return self.name.strip() if self.side is self.default_side else super().__str__()


class BackgroundPiece(UtilityPiece):
    name = '(Background Piece)'

    def __init__(self, board, **kwargs):
        super().__init__(board, **kwargs)
        self.set_color()

    def reload(self, *args, **kwargs):
        super().reload(*args, **kwargs)
        self.set_color()

    def set_color(self, *args, **kwargs):
        self.color = self.board.color_scheme.get('wall_color', self.board.color_scheme['background_color'])


class Shield(BackgroundPiece, Empty):
    name = 'Shield'
    file_name = 'shield'
    asset_folder = 'other'
    default_side = Side.NEUTRAL


class Void(BackgroundPiece, Empty, Immune):
    name = 'Void'
    file_name = 'void'
    asset_folder = 'other'
    default_side = Side.NEUTRAL


class NoSidePiece(UtilityPiece, Empty):
    name = '(No-Side Piece)'

    def __init__(self, board, **kwargs):
        kwargs['side'] = self.default_side
        super().__init__(board, **kwargs)

    def of(self, side: Side) -> Piece:
        side = self.default_side
        return super().of(side)


class NoPiece(NoSidePiece, Empty):
    name = '(Nothing)'


class Obstacle(NoSidePiece, BackgroundPiece):
    name = '(Obstacle)'
    asset_folder = 'other'
    default_side = Side.NEUTRAL


class Block(Obstacle):
    name = 'Block'
    file_name = 'block'


class Wall(Obstacle, Immune):
    name = 'Wall'
    file_name = 'wall'


class Border(Obstacle, Immune):
    name = 'Border'
    file_name = 'square'
    asset_folder = 'util'
