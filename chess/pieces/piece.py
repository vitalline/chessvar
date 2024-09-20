from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING, Type

from arcade import Color, Sprite, load_texture

from chess.pieces.side import Side
from chess.util import Default, get_texture_path

if TYPE_CHECKING:
    from chess.board import Board
    from chess.movement.move import Move
    from chess.movement.movement import BaseMovement
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
            yield from self.movement.moves(self.board_pos, self, theoretical)
        return ()

    def __str__(self):
        return f"{self.side} {'???' if self.is_hidden else self.name}".strip()

    def __copy__(self):
        clone = type(self)(
            board=self.board,
            board_pos=self.board_pos,
            side=self.side,
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
            self.scale = self.board.square_size / self.texture.width

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


class PromotablePiece(Piece):
    def __init__(
        self,
        board: Board,
        board_pos: Position | None = None,
        side: Side = Side.NONE,
        movement: BaseMovement | None = None,
        promotions: list[Type[Piece]] | None = None,
        promotion_squares: set[Position] | None = None,
        **kwargs
    ):
        super().__init__(board, board_pos, side, movement, **kwargs)
        self.promotions = promotions or []
        self.promotion_squares = promotion_squares or set()

    def move(self, move: Move):
        super().move(move)
        if self.board_pos in self.promotion_squares:
            if move.is_edit:
                return
            if not self.promotions:
                return
            promotion_piece = self.board.promotion_piece
            if move.promotion:
                self.board.promotion_piece = True
                self.board.replace(self, move.promotion)
                self.board.update_promotion_auto_captures(move)
                self.board.promotion_piece = promotion_piece
                return
            if len(self.promotions) == 1:
                self.board.promotion_piece = True
                move.set(promotion=self.promotions[0](
                    board=self.board,
                    board_pos=self.board_pos,
                    side=self.side,
                    promotions=self.board.promotions.get(self.side),
                    promotion_squares=self.board.promotion_squares.get(self.side),
                ))
                self.board.replace(self, move.promotion)
                self.board.update_promotion_auto_captures(move)
                self.board.promotion_piece = promotion_piece
                return
            self.board.start_promotion(self, self.promotions)

    def moves(self, theoretical: bool = False):
        for move in super().moves(theoretical):
            if self.promotions and move.pos_to in self.promotion_squares:
                for promotion in self.promotions:
                    yield copy(move).set(promotion=promotion(
                        board=self.board,
                        board_pos=self.board_pos,
                        side=self.side,
                        promotions=self.board.promotions.get(self.side),
                        promotion_squares=self.board.promotion_squares.get(self.side),
                    ))
            else:
                yield move

    def __copy__(self):
        clone = super().__copy__()
        clone.promotions = copy(self.promotions)
        clone.promotion_squares = copy(self.promotion_squares)
        return clone


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
