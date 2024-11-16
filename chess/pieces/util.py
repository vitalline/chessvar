from chess.movement.util import to_algebraic
from chess.pieces.piece import AbstractPiece, Piece
from chess.pieces.side import Side
from chess.pieces.types import Empty, Immune


class UtilityPiece(AbstractPiece):
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
    def type_str(cls) -> str:
        return cls.__name__

    def __str__(self):
        return self.name.strip() if self.side is self.default_side else super().__str__()

    def __repr__(self):
        string = f"{self.side} {self.name}" if self.side != self.default_side else self.name
        if self.board_pos:
            string = f"{self.board.get_absolute(self.board_pos)} {string} at {to_algebraic(self.board_pos)}"
        suffixes = []
        if self.movement and self.movement.total_moves:
            suffixes.append(f"Moves: {self.movement.total_moves}")
        if self.promoted_from:
            suffixes.append(f"From: {self.promoted_from}")
        if self.should_hide is not False:
            suffixes.append("Always hide" if self.should_hide else "Can be hidden")
        elif self.is_hidden:
            suffixes.append("Hidden")
        if suffixes:
            string += f" ({', '.join(suffixes)})"
        return f"<{string}>"


class BackgroundPiece(Piece, UtilityPiece):
    name = '(Background Piece)'

    def __init__(self, board, **kwargs):
        super().__init__(board, **kwargs)
        self.set_color()

    def reload(self, *args, **kwargs):
        super().reload(*args, **kwargs)
        self.set_color()

    def set_color(self, *args, **kwargs):
        self.sprite.color = self.board.color_scheme.get('wall_color', self.board.color_scheme['background_color'])


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

    def of(self, side: Side) -> AbstractPiece:
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
