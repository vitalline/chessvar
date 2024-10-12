from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING

from arcade import Color, Sprite, load_texture

from chess.pieces.side import Side
from chess.movement.movement import BaseMovement
from chess.util import Default, get_texture_path

if TYPE_CHECKING:
    from chess.board import Board
    from chess.movement.move import Move
    from chess.movement.util import Position


class Piece(Sprite):
    name = '(Piece)'
    file_name = 'none'
    asset_folder = 'util'

    def __init__(
        self,
        board: Board,
        board_pos: Position | None = None,
        side: Side = Side.NONE,
        movement: BaseMovement | None = None,
        **kwargs
    ):
        self.board = board
        self.board_pos = board_pos
        self.side = side
        self.movement = movement
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
                if self.side in self.board.promotions:
                    side_promotions = self.board.promotions[self.side]
                    if type(self) in side_promotions:
                        promotion_squares = side_promotions[type(self)]
                        if move.pos_to in promotion_squares:
                            promotions = promotion_squares[move.pos_to]
                            if promotions:
                                for promotion in promotions:
                                    if isinstance(promotion, Piece):
                                        yield copy(move).set(
                                            promotion=promotion.of(promotion.side or self.side).on(move.pos_to)
                                        )
                                    else:
                                        yield copy(move).set(promotion=promotion(
                                            board=self.board,
                                            board_pos=move.pos_to,
                                            side=self.side,
                                        ))
                                continue
                yield move
        return ()

    def __str__(self):
        return f"{self.side} {'???' if self.is_hidden else self.name}".strip()

    def __copy__(self):
        return self.of(self.side)

    def of(self, side: Side) -> Piece:
        clone = type(self)(
            board=self.board,
            board_pos=self.board_pos,
            side=side,
        )
        clone.movement = copy(self.movement)
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
                self.movement.total_moves == other.movement.total_moves
                if isinstance(self.movement, BaseMovement) else
                self.movement == other.movement
            )
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


class QuasiRoyalPiece(Piece):
    def __init__(
        self,
        board: Board,
        board_pos: Position | None = None,
        side: Side = Side.NONE,
        movement: BaseMovement | None = None,
        **kwargs
    ):
        super().__init__(board, board_pos, side, movement, **kwargs)


class RoyalPiece(QuasiRoyalPiece):
    def __init__(
        self,
        board: Board,
        board_pos: Position | None = None,
        side: Side = Side.NONE,
        movement: BaseMovement | None = None,
        **kwargs
    ):
        super().__init__(board, board_pos, side, movement, **kwargs)
