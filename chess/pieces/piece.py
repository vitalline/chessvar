from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING

from arcade import Color, Sprite, load_texture

from chess.movement.base import BaseMovement
from chess.movement.types import is_active
from chess.movement.util import Position, to_algebraic
from chess.pieces.side import Side
from chess.pieces.types import Double, Enemy, Empty, Immune
from chess.util import CUSTOM_PREFIX, Default, get_texture_path

if TYPE_CHECKING:
    from chess.board import Board


class Piece(Sprite):
    name = '(Piece)'
    file_name = 'none'
    asset_folder = 'util'
    type_str = None
    group_str = None

    def __init__(
        self,
        board: Board,
        movement: BaseMovement | None = None,
        pos: Position | None = None,
        side: Side = Side.NONE,
        **kwargs
    ):
        self.board = board
        self.movement = movement
        self.board_pos = pos
        self.side = side
        self.promoted_from = None
        self.flipped_horizontally = False
        self.flipped_vertically = False
        self.should_hide = None
        self.is_hidden = None
        self.texture_folder = self.asset_folder
        self.texture_side = self.side
        self.texture_name = self.file_name
        super().__init__(
            get_texture_path(self.texture_path()),
            flipped_horizontally=self.flipped_horizontally,
            flipped_vertically=self.flipped_vertically,
        )
        if self.board_pos is not None:
            self.position = self.board.get_screen_position(self.board_pos)

    def moves(self, theoretical: bool = False):
        if self.movement:
            for move in self.movement.moves(self.board_pos, self, theoretical):
                chained_move = move
                while chained_move and is_active(chained_move.chained_move):
                    chained_move = chained_move.chained_move
                if is_active(chained_move):
                    if self.side in self.board.promotions:
                        side_promotions = self.board.promotions[self.side]
                        if type(self) in side_promotions:
                            promotion_squares = side_promotions[type(self)]
                            promotion_found = False
                            for square in (chained_move.pos_to, chained_move.pos_from):
                                if square in promotion_squares:
                                    promotions = promotion_squares[square]
                                    if not promotions:
                                        break
                                    promotion_found = True
                                    for piece in promotions:
                                        if isinstance(piece, Piece):
                                            piece = piece.of(piece.side or self.side).on(square)
                                        else:
                                            piece = piece(
                                                board=self.board,
                                                board_pos=square,
                                                side=self.side,
                                            )
                                        promoted_from = piece.promoted_from or self.promoted_from or type(self)
                                        if type(piece) != promoted_from:
                                            piece.promoted_from = promoted_from
                                        copy_move = copy(move)
                                        chained_copy = copy_move
                                        while chained_copy and is_active(chained_copy.chained_move):
                                            chained_copy.set(chained_move=copy(chained_copy.chained_move))
                                            chained_copy = chained_copy.chained_move
                                        chained_copy.set(promotion=piece)
                                        yield copy_move
                                    break
                            if promotion_found:
                                continue
                yield move
        return ()

    def __str__(self):
        return f"{self.side} {'???' if self.is_hidden else self.name}".strip()

    def __repr__(self):
        string = f"{self.side} {self.name}"
        if self.board_pos:
            string = f"{self.board_pos} {string} at {to_algebraic(self.board_pos)}"
        suffixes = []
        if self.movement and self.movement.total_moves:
            suffixes.append(f"Moves: {self.movement.total_moves}")
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

    def of(self, side: Side) -> Piece:
        clone = type(self)(
            board=self.board,
            pos=self.board_pos,
            side=side,
        )
        clone.movement = copy(self.movement)
        clone.promoted_from = self.promoted_from
        clone.scale = self.scale
        clone.should_hide = self.should_hide
        clone.is_hidden = self.is_hidden
        return clone

    def on(self, pos: Position | None) -> Piece:
        clone = copy(self)
        clone.board_pos = pos
        if pos is not None:
            clone.position = self.board.get_screen_position(pos)
        return clone

    def matches(self, other: Piece) -> bool:
        return (
            type(self) is type(other)
            and self.side == other.side
            and bool(self.should_hide) == bool(other.should_hide)
            and (
                self.movement == other.movement and self.movement is None
                or other.movement is not None and self.movement.total_moves == other.movement.total_moves
            )
        )

    def friendly_of(self, what: Piece):
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

    def friendly_to(self, what: Piece):
        return what and what.friendly_of(self)

    def blocked_by(self, what: Piece):
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

    def blocks(self, what: Piece):
        return what and what.blocked_by(self)

    def captures(self, what: Piece):
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

    def captured_by(self, what: Piece):
        return what and what.captures(self)

    def skips(self, what: Piece):
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

    def skipped_by(self, what: Piece):
        return what and what.skips(self)

    @classmethod
    def is_colorbound(cls):
        return getattr(cls, 'colorbound', False)

    @classmethod
    def type(cls) -> str:
        if cls.type_str is None:
            if cls.__name__.startswith(CUSTOM_PREFIX):
                cls.type_str = cls.__name__.removeprefix(CUSTOM_PREFIX)
            else:
                cls.type_str = f"{cls.__module__.rsplit('.', 1)[-1]}.{cls.__name__}"
        return cls.type_str

    @classmethod
    def group(cls) -> str:
        return cls.group_str

    def texture_path(self) -> str:
        return f"assets/{self.texture_folder}/{self.texture_side.file_prefix()}{self.texture_name}.png"

    def reload(
        self,
        asset_folder: str = None,
        side: Side = None,
        file_name: str = None,
        is_hidden: bool = None,
        should_hide: bool = None,
        flipped_horizontally: bool = None,
        flipped_vertically: bool = None,
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
        texture_path = get_texture_path(self.texture_path())
        if flipped_horizontally is None:
            flipped_horizontally = self.flipped_horizontally
        else:
            self.flipped_horizontally = flipped_horizontally
        if flipped_vertically is None:
            flipped_vertically = self.flipped_vertically
        else:
            self.flipped_vertically = flipped_vertically
        if self.texture.name != texture_path:
            color = self.color
            new_texture = load_texture(
                texture_path,
                flipped_horizontally=flipped_horizontally,
                flipped_vertically=flipped_vertically,
            )
            self.texture = new_texture
            self.color = color

    def set_color(self, color: Color, force_color: bool = False):
        if not self.name:
            return
        side = Side.WHITE if force_color else Side.NONE  # if forcing color, make piece white so that it can be colored
        if not side:  # if not forcing color, determine side based on color
            if max(color) != min(color):  # if color is not grayscale
                side = Side.WHITE  # make piece white so that it can be colored
            if max(color) == min(color):  # if color is grayscale
                side = self.side  # make piece match the side
        self.color = color
        if side != self.texture_side:  # if side was defined and does not match the current texture
            self.reload(side=side)
