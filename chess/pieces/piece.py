from __future__ import annotations

from copy import copy
from os.path import join
from typing import TYPE_CHECKING

from arcade import Sprite, load_texture

from chess.movement.base import BaseMovement
from chess.movement.util import Position, to_algebraic
from chess.pieces.side import Side
from chess.pieces.types import Double, Enemy, Empty, Immune, Neutral
from chess.util import ALTERNATE_SUFFIX, CUSTOM_PREFIX, Color, FormatOverride, Default, get_texture_path, normalize

if TYPE_CHECKING:
    from chess.board import Board


def piece_repr(cls: type[AbstractPiece]) -> str:
    return f"<{'custom' if cls.is_custom() else 'class'} '{cls.type_str()}'>"


def piece_str(cls: type[AbstractPiece]) -> str:
    return cls.name


class PieceMeta(FormatOverride):
    def __new__(mcs, name, bases, namespace):
        return super().__new__(mcs, name, bases, namespace, repr_method=piece_repr, str_method=piece_str)


class AbstractPiece(object, metaclass=PieceMeta):
    name = '(Piece)'
    type_data = None
    group_data = None

    def __init__(
        self,
        board: Board,
        movement: BaseMovement | None = None,
        board_pos: Position | None = None,
        side: Side | None = None,
        **kwargs
    ):
        self.board = board
        self.movement = movement
        self.board_pos = board_pos
        self.side = Side.NEUTRAL if isinstance(self, Neutral) else side if side is not None else Side.NONE
        self.promoted_from = None
        self.should_hide = None
        self.is_hidden = None

    def moves(self, theoretical: bool = False):
        if self.movement:
            yield from self.movement.moves(self.board_pos, self, theoretical)

    def __str__(self):
        return f"{self.side if not isinstance(self, Neutral) else ''} {'???' if self.is_hidden else self.name}".strip()

    def __repr__(self):
        string = f"{self.side} {self.name}"
        if self.board_pos:
            string = f"{self.board.get_absolute(self.board_pos)} {string} at {to_algebraic(self.board_pos)}"
        suffixes = [f"Moves: {moves if (moves := self.total_moves) is not None else 'None'}"]
        if self.promoted_from:
            suffixes.append(f"From: {self.promoted_from}")
        if self.should_hide is not None:
            suffixes.append("Always hide" if self.should_hide else "Never hide")
        elif self.is_hidden:
            suffixes.append("Hidden")
        if suffixes:
            string += f" ({', '.join(suffixes)})"
        return f"<{string}>"

    def __copy__(self):
        return self.of(self.side)

    def __deepcopy__(self, memo):
        return self.__copy__()

    def of(self, side: Side) -> AbstractPiece:
        clone = type(self)(
            board=self.board,
            board_pos=self.board_pos,
            side=side if not isinstance(self, Neutral) else None,
        )
        clone.movement = copy(self.movement)
        clone.promoted_from = self.promoted_from
        return clone

    def on(self, board_pos: Position | None) -> AbstractPiece:
        clone = copy(self)
        clone.board_pos = board_pos
        return clone

    @property
    def total_moves(self) -> int | None:
        if self.movement:
            if self.movement.total_moves >= 0:
                return self.movement.total_moves
            return None
        return 0

    def set_moves(self, count: AbstractPiece | int | None, offset: int | None = None, force: bool = False):
        if self.movement is not None and (force or self.total_moves is None):
            if not (count is None or isinstance(count, int)):
                count = count.total_moves
            if count is None or count < 0:
                count = -1
            if offset is not None:
                if offset < 0:
                    count = max(0, count + offset)
                else:
                    count = max(0, count) + offset
            self.movement.set_moves(count)

    def matches(self, other: AbstractPiece) -> bool:
        return (
            type(self) is type(other)
            and self.side == other.side
            and bool(self.should_hide) == bool(other.should_hide)
            and self.movement == other.movement
            and (
                (self_moves := self.total_moves) == (other_moves := other.total_moves)
                or self_moves is None or other_moves is None
            )
        )

    def friendly_of(self, what: AbstractPiece):
        if not what:
            return False
        if what == self:
            return True
        if what.side is Side.NONE:
            return False
        if what.side is Side.ANY:
            return True
        if what.side is self.side:
            return not isinstance(self, Enemy)
        if what.side is self.side.opponent():
            return isinstance(self, (Double, Enemy))
        return True

    def friendly_to(self, what: AbstractPiece):
        return what and what.friendly_of(self)

    def blocked_by(self, what: AbstractPiece):
        if not what:
            return False
        if what == self:
            return False
        if isinstance(what, Immune):
            return True
        if what.side is Side.NONE:
            return False
        if what.side is Side.ANY:
            return True
        if what.side is self.side:
            return not isinstance(self, (Double, Enemy))
        if what.side is self.side.opponent():
            return isinstance(self, Enemy)
        return False

    def blocks(self, what: AbstractPiece):
        return what and what.blocked_by(self)

    def captures(self, what: AbstractPiece):
        if not what:
            return False
        if isinstance(what, Immune):
            return False
        if what.side is Side.NONE:
            return False
        if what.side is Side.ANY:
            return True
        if what.side is self.side:
            return isinstance(self, (Double, Enemy))
        if what.side is self.side.opponent():
            return not isinstance(self, Enemy)
        return True

    def captured_by(self, what: AbstractPiece):
        return what and what.captures(self)

    def skips(self, what: AbstractPiece):
        if not what:
            return False
        if not issubclass(type(what), Empty):
            return False
        if what.side is Side.NONE:
            return True
        if what.side is Side.ANY:
            return False
        if what.side is self.side:
            return not isinstance(self, Enemy)
        if what.side is self.side.opponent():
            return isinstance(self, (Double, Enemy))
        return True

    def skipped_by(self, what: AbstractPiece):
        return what and what.skips(self)

    @classmethod
    def is_colorbound(cls):
        return getattr(cls, 'colorbound', False)

    @classmethod
    def is_custom(cls):
        return cls.__name__.startswith(CUSTOM_PREFIX)

    @classmethod
    def type_str(cls) -> str | None:
        if cls.type_data is None:
            if cls.is_custom():
                cls.type_data = cls.__name__.removeprefix(CUSTOM_PREFIX)
            else:
                cls.type_data = f"{cls.__module__.rsplit('.', 1)[-1]}.{cls.__name__}"
        return cls.type_data

    @classmethod
    def group_str(cls) -> str | None:
        return cls.group_data


class Piece(AbstractPiece):
    file_name = 'none'
    asset_folder = 'util'

    def __init__(
        self,
        board: Board,
        movement: BaseMovement | None = None,
        board_pos: Position | None = None,
        side: Side | None = None,
        **kwargs
    ):
        super().__init__(
            board=board,
            movement=movement,
            board_pos=board_pos,
            side=side,
            **kwargs
        )
        self.flipped_horizontally = False
        self.flipped_vertically = False
        self.texture_folder = self.asset_folder
        self.texture_name = self.file_name
        self.texture_side = Side.NEUTRAL if isinstance(self, Neutral) else side if side is not None else Side.NONE
        self.alternate = False
        self.sprite = Sprite(normalize(self.texture_path()))
        if self.board_pos is not None:
            self.sprite.position = self.board.get_screen_position(self.board_pos)

    def of(self, side: Side) -> AbstractPiece:
        clone = super().of(side)
        if isinstance(clone, Piece):
            clone.sprite.scale = self.sprite.scale
        clone.should_hide = self.should_hide
        clone.is_hidden = self.is_hidden
        return clone

    def on(self, board_pos: Position | None) -> AbstractPiece:
        clone = super().on(board_pos)
        if board_pos is not None and isinstance(clone, Piece):
            clone.sprite.position = self.board.get_screen_position(board_pos)
        return clone

    def texture_path(self, base_dir: str = 'assets') -> str:
        texture_basename = self.texture_side.file_prefix() + self.texture_name
        roots = [self.board.board_config['asset_path'], base_dir]
        paths = [join(self.texture_folder, texture_basename + '.png')]
        if self.alternate:
            paths = [join(self.texture_folder, texture_basename + ALTERNATE_SUFFIX + '.png')] + paths
        return get_texture_path(*(join(root, path) for root in roots for path in paths))

    def reload(
        self,
        asset_folder: str = None,
        side: Side = None,
        file_name: str = None,
        is_hidden: bool = None,
        should_hide: bool = None,
        flipped_horizontally: bool = None,
        flipped_vertically: bool = None,
        alternate: bool = False,
    ):
        if should_hide is not None:
            self.should_hide = None if should_hide is Default else should_hide
            self.is_hidden = self.should_hide
        if self.should_hide is None and is_hidden is not None:
            self.is_hidden = None if is_hidden is Default else is_hidden
        if self.should_hide is not None and self.is_hidden is not None:
            self.is_hidden = self.should_hide
        self.texture_folder = asset_folder or self.texture_folder
        self.texture_side = side or self.texture_side
        self.texture_name = file_name or self.texture_name
        self.alternate = alternate
        texture_path = normalize(self.texture_path())
        if flipped_horizontally is not None:
            self.flipped_horizontally = flipped_horizontally
        if flipped_vertically is not None:
            self.flipped_vertically = flipped_vertically
        if self.sprite.texture.file_path.resolve() != texture_path:
            color = self.sprite.color
            new_texture = load_texture(texture_path)
            self.sprite.texture = new_texture
            self.sprite.color = color
            self.set_size(new_texture.width)

    def set_size(self, size: float):
        if size <= 0:
            return
        self.sprite.scale = size / self.sprite.texture.width
        if self.flipped_horizontally:
            self.sprite.scale_x *= -1
        if self.flipped_vertically:
            self.sprite.scale_y *= -1

    def set_color(self, color: Color, force_color: bool = False):
        if not self.name:
            return
        side = Side.WHITE if force_color else Side.NONE  # if forcing color, make piece white so that it can be colored
        if not side:  # if not forcing color, determine side based on color
            if max(color) != min(color):  # if color is not grayscale
                side = Side.WHITE  # make piece white so that it can be colored
            if max(color) == min(color):  # if color is grayscale
                side = self.side  # make piece match the side
        self.sprite.color = color
        if side != self.texture_side:  # if side was defined and does not match the current texture
            self.reload(side=side)
