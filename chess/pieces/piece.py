from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING

from arcade import Color, Sprite, load_texture

from chess.movement import types
from chess.pieces.side import Side
from chess.pieces.types import Immune, Double
from chess.util import Default, get_texture_path

if TYPE_CHECKING:
    from chess.board import Board
    from chess.movement.move import Move
    from chess.movement.util import Position


# Movements that do not move the piece, instead interacting with the game in other, more mysterious ways. Intrigued yet?
passive_movements = (
    types.RangedMovement,
    types.AutoCaptureMovement,
)


is_active = lambda move: (
    move and not move.is_edit and move.pos_from and move.pos_to and
    (move.pos_from != move.pos_to or move.movement_type and not issubclass(move.movement_type, passive_movements))
)


class Piece(Sprite):
    name = '(Piece)'
    file_name = 'none'
    asset_folder = 'util'

    def __init__(
        self,
        board: Board,
        movement: types.BaseMovement | None = None,
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
        self.is_hidden = None
        self.texture_folder = self.asset_folder
        self.texture_side = self.side
        self.texture_name = self.file_name
        super().__init__(
            get_texture_path(self.texture_path),
            flipped_horizontally=self.flipped_horizontally,
            flipped_vertically=self.flipped_vertically,
        )
        if self.board_pos is not None:
            self.position = self.board.get_screen_position(self.board_pos)

    def is_empty(self):
        return not self.side

    @classmethod
    def is_colorbound(cls):
        return getattr(cls, 'colorbound', False)

    def move(self, move: Move):
        self.board.move(move)

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
                                        promoted_from = piece.promoted_from or self.promoted_from
                                        if not self.is_empty():
                                            promoted_from = promoted_from or type(self)
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
            and self.is_hidden == other.is_hidden
            and (
                self.movement == other.movement and self.movement is None
                or other.movement is not None and self.movement.total_moves == other.movement.total_moves
            )
        )

    def fits(self, match: str) -> bool:
        if match == '*':
            return True
        if match == self.name:
            return True
        match_start = match[0] == '*'
        match_end = match[-1] == '*'
        match = match.strip('*')
        match_middle = '*' in match
        if match_middle:
            keys = match.split('*')
            indexes = [self.name.find(key) for key in keys]
            if all(index >= 0 for index in indexes) and indexes == sorted(indexes):
                return True
        if match_start and match_end and match in self.name:
            return True
        if match_start and self.name.endswith(match):
            return True
        if match_end and self.name.startswith(match):
            return True

    def blocked_by(self, what: Piece):
        if not what:
            return False
        if what == self:
            return False
        match self.side:
            case Side.ANY:
                return False
            case Side.NONE:
                return True
            case _:
                return (
                    self.side is what.side and not isinstance(self, Double)
                    or isinstance(what, Immune)
                )

    def captures(self, what: Piece):
        if not what:
            return False
        match self.side:
            case Side.ANY:
                return True
            case Side.NONE:
                return False
            case _:
                return (
                    what.side is not Side.NONE
                    and (self.side is not what.side or isinstance(self, Double))
                    and not isinstance(what, Immune)
                )

    @property
    def texture_path(self) -> str:
        return f"assets/{self.texture_folder}/{self.texture_side.file_prefix()}{self.texture_name}.png"

    def reload(
        self,
        asset_folder: str = None,
        side: Side = None,
        file_name: str = None,
        is_hidden: bool = None,
        flipped_horizontally: bool = None,
        flipped_vertically: bool = None,
    ):
        if is_hidden is not None:
            self.is_hidden = None if is_hidden is Default else is_hidden
        self.texture_folder = asset_folder or self.texture_folder
        self.texture_side = side or self.texture_side
        self.texture_name = file_name or self.texture_name
        texture_path = get_texture_path(self.texture_path)
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
