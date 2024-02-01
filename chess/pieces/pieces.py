from __future__ import annotations

from copy import copy
from enum import Enum
from typing import TYPE_CHECKING, Type

from arcade import Color, Sprite, load_texture

from chess.movement.move import Move
from chess.movement.util import AnyDirection, Position

if TYPE_CHECKING:
    from chess.board import Board

from chess.movement.movement import BaseMovement


class Side(Enum):
    NONE = 0
    WHITE = 1
    BLACK = 2
    ANY = -1

    def opponent(self):
        match self:
            case Side.WHITE:
                return Side.BLACK
            case Side.BLACK:
                return Side.WHITE
            case _:
                return self

    def direction(self, dpos: AnyDirection | int | None = None) -> AnyDirection | int:
        match self:
            case Side.WHITE:
                return 1 if dpos is None else dpos if type(dpos) is int else dpos
            case Side.BLACK:
                return -1 if dpos is None else -dpos if type(dpos) is int else (-dpos[0], *dpos[1:])
            case _:
                return 0 if dpos is None else 0 if type(dpos) is int else (0, 0)

    def name(self):
        match self:
            case Side.WHITE:
                return "White"
            case Side.BLACK:
                return "Black"
            case _:
                return ""

    def file_name(self):
        match self:
            case Side.WHITE:
                return "0."
            case Side.BLACK:
                return "1."
            case _:
                return ""


class Piece(Sprite):
    name = ''
    file_name = ''
    asset_folder = 'util'

    def __init__(
            self,
            board: Board,
            board_pos: Position | None = None,
            side: Side = Side.NONE,
            movement: BaseMovement | None = None,
            flipped_horizontally: bool = False,
            flipped_vertically: bool = False
    ):
        self.board = board
        self.board_pos = board_pos
        self.side = side
        self.movement = movement if movement is not None else BaseMovement(board)
        self.flipped_horizontally = flipped_horizontally
        self.flipped_vertically = flipped_vertically
        super().__init__(
            f"assets/{self.asset_folder}/{self.side.file_name()}{self.file_name}.png",
            flipped_horizontally=self.flipped_horizontally,
            flipped_vertically=self.flipped_vertically,
        )
        if self.board_pos is not None:
            self.position = self.board.get_screen_position(self.board_pos)

    def is_empty(self):
        return self.side == Side.NONE or not self.name

    def move(self, move: Move):
        self.board.move(move)

    def moves(self, theoretical: bool = False):
        yield from self.movement.moves(self.board_pos, self, theoretical)

    def __copy__(self):
        clone = type(self)(self.board, self.board_pos, self.side)
        clone.movement = copy(self.movement)
        clone.scale = self.scale
        clone.flipped_horizontally = self.flipped_horizontally
        return clone

    def set_color(self, color: Color, force_color: bool = False):
        if not self.name:
            return
        side = Side.WHITE if force_color else Side.NONE
        if side == Side.NONE:
            if max(color) != min(color):  # if color is not grayscale
                if max(self.color) == min(self.color):  # but was grayscale
                    side = Side.WHITE  # make piece white so that it can be colored
            if max(color) == min(color):  # if color is grayscale
                if max(self.color) != min(self.color):  # but was not grayscale
                    side = self.side  # make piece match the side
        new_texture = None
        if side != Side.NONE:  # if side was defined and does not match the current texture
            if self.texture.name != f"assets/{self.asset_folder}/{side.file_name()}{self.file_name}.png":
                new_texture = load_texture(  # make piece match the side
                    f"assets/{self.asset_folder}/{side.file_name()}{self.file_name}.png",
                    flipped_horizontally=self.flipped_horizontally,
                    flipped_vertically=self.flipped_vertically,
                )
        if new_texture is not None:
            self.texture = new_texture
        self.color = color


class PromotablePiece(Piece):
    def __init__(
            self,
            board: Board,
            board_pos: Position | None = None,
            side: Side = Side.NONE,
            movement: BaseMovement | None = None,
            promotions: list[Type[Piece]] | None = None,
            promotion_squares: set[Position] | None = None
    ):
        super().__init__(board, board_pos, side, movement)
        self.promotions = promotions or []
        self.promotion_squares = promotion_squares or set()

    def move(self, move: Move):
        super().move(move)
        if self.board_pos in self.promotion_squares:
            if not self.promotions:
                return
            if move.promotion is not None:
                self.board.replace(self, move.promotion)
                return
            if len(self.promotions) == 1:
                move.set(promotion=self.promotions[0])
                self.board.replace(self, self.promotions[0])
                return
            self.board.start_promotion(self, self.promotions)

    def moves(self, theoretical: bool = False):
        for move in super().moves(theoretical):
            if self.promotions and move.pos_to in self.promotion_squares:
                for promotion in self.promotions:
                    yield copy(move).set(promotion=promotion)
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
            movement: BaseMovement | None = None
    ):
        super().__init__(board, board_pos, side, movement)


class RoyalPiece(QuasiRoyalPiece):
    def __init__(
            self,
            board: Board,
            board_pos: Position | None = None,
            side: Side = Side.NONE,
            movement: BaseMovement | None = None
    ):
        super().__init__(board, board_pos, side, movement)
