from __future__ import annotations

from copy import copy
from enum import Enum
from os.path import isfile
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

    def __bool__(self):
        return self is not Side.NONE

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

    def __str__(self):
        match self:
            case Side.WHITE:
                return "White"
            case Side.BLACK:
                return "Black"
            case _:
                return ""

    def key(self):
        match self:
            case Side.WHITE:
                return "white_"
            case Side.BLACK:
                return "black_"
            case _:
                return ""

    def file_prefix(self):
        match self:
            case Side.WHITE:
                return "0."
            case Side.BLACK:
                return "1."
            case _:
                return ""


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
            flipped_horizontally: bool = False,
            flipped_vertically: bool = False,
            is_hidden: bool = False
    ):
        self.board = board
        self.board_pos = board_pos
        self.side = side
        self.movement = movement if movement is not None else BaseMovement(board)
        self.flipped_horizontally = flipped_horizontally
        self.flipped_vertically = flipped_vertically
        self.is_hidden = is_hidden
        super().__init__(
            self.texture_path(),
            flipped_horizontally=self.flipped_horizontally,
            flipped_vertically=self.flipped_vertically,
        )
        if self.board_pos is not None:
            self.position = self.board.get_screen_position(self.board_pos)

    def is_empty(self):
        return not self.side

    def move(self, move: Move):
        self.board.move(move)

    def moves(self, theoretical: bool = False):
        yield from self.movement.moves(self.board_pos, self, theoretical)

    def __copy__(self):
        clone = type(self)(self.board, self.board_pos, self.side)
        clone.movement = copy(self.movement)
        clone.scale = self.scale
        clone.flipped_horizontally = self.flipped_horizontally
        clone.flipped_vertically = self.flipped_vertically
        clone.is_hidden = self.is_hidden
        return clone

    def texture_path(
        self, asset_folder: str = None, side: Side = None, file_name: str = None, force_color: bool = False
    ):
        if side is None:
            side = Side.WHITE if force_color else self.side
        if asset_folder is None:
            asset_folder = self.asset_folder
        if file_name is None:
            file_name = self.file_name
        path = f"assets/{asset_folder}/{side.file_prefix()}{file_name}.png"
        fallback_path = f"assets/{asset_folder}/{file_name}.png"
        return path if isfile(path) else fallback_path

    def reload(
            self,
            asset_folder: str = None,
            side: Side = None,
            file_name: str = None,
            hidden: bool = None,
            flipped_horizontally: bool = None,
            flipped_vertically: bool = None
    ):
        if hidden is not None:
            self.is_hidden = hidden
        texture_path = self.texture_path(
            asset_folder=asset_folder, side=side, file_name=file_name, force_color=(max(self.color) != min(self.color))
        )
        if flipped_horizontally is None:
            flipped_horizontally = self.flipped_horizontally if not hidden else False
        if flipped_vertically is None:
            flipped_vertically = self.flipped_vertically if not hidden else False
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
        side = Side.WHITE if force_color else Side.NONE
        if not side:
            if max(color) != min(color):  # if color is not grayscale
                if max(self.color) == min(self.color):  # but was grayscale
                    side = Side.WHITE  # make piece white so that it can be colored
            if max(color) == min(color):  # if color is grayscale
                if max(self.color) != min(self.color):  # but was not grayscale
                    side = self.side  # make piece match the side
        self.color = color
        if side:  # if side was defined and does not match the current texture
            self.reload(side=side)


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
            if move.is_edit:
                return
            if not self.promotions:
                return
            promotion_piece = self.board.promotion_piece
            if move.promotion and move.promotion is not True:
                self.board.promotion_piece = True
                self.board.replace(self, move.promotion)
                self.board.load_pieces()
                self.board.update_auto_ranged_pieces(move, move.piece.side.opponent())
                self.board.promotion_piece = promotion_piece
                return
            if len(self.promotions) == 1:
                self.board.promotion_piece = True
                move.set(promotion=self.promotions[0])
                self.board.replace(self, self.promotions[0])
                self.board.load_pieces()
                self.board.update_auto_ranged_pieces(move, move.piece.side.opponent())
                self.board.promotion_piece = promotion_piece
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
