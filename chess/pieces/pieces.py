from __future__ import annotations

from enum import Enum
import typing

from cocos.sprite import Sprite

from chess.movement.move import Move
from chess.movement.util import AnyPosition, Position

if typing.TYPE_CHECKING:
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

    def direction(self, dpos: AnyPosition) -> AnyPosition:
        match self:
            case Side.WHITE:
                return dpos
            case Side.BLACK:
                return -dpos[0], dpos[1], *dpos[2:]
            case _:
                return 0, 0

    def name(self):
        match self:
            case Side.WHITE:
                return "White "
            case Side.BLACK:
                return "Black "
            case _:
                return ""

    def file_name(self):
        match self:
            case Side.WHITE:
                return "white"
            case Side.BLACK:
                return "black"
            case _:
                return "none"


class Piece(Sprite):
    def __init__(
            self,
            board: Board,
            board_pos: Position | None = None,
            side: Side = Side.NONE,
            name: str = '',
            file_name: str = '',
            asset_folder: str = 'util',
            movement: BaseMovement | None = None
    ):
        self.board = board
        self.board_pos = board_pos
        self.side = side
        self.name = name
        self.file_name = file_name or name.lower()
        self.asset_folder = asset_folder
        self.movement = movement if movement is not None else BaseMovement(board)
        super().__init__(f"assets/{self.asset_folder}/{self.file_name}.png")
        if self.board_pos is not None:
            self.position = self.board.get_screen_position(self.board_pos)

    def is_empty(self):
        return self.side == Side.NONE or not self.name

    def move(self, move: Move):
        self.board.move(move)

    def moves(self, pos: typing.Tuple[int, int]):  # convenience method
        return self.movement.moves(pos)


class PromotablePiece(Piece):
    def __init__(
            self,
            board: Board,
            board_pos: Position | None = None,
            side: Side = Side.NONE,
            name: str = '',
            file_name: str = '',
            asset_folder: str = 'util',
            movement: BaseMovement | None = None,
            promotions: list[typing.Type[Piece]] | None = None,
            promotion_tiles: set[Position] | None = None
    ):
        super().__init__(board, board_pos, side, name, file_name, asset_folder, movement)
        self.promotions = promotions or []
        self.promotion_tiles = promotion_tiles or set()

    def move(self, move: Move):
        super().move(move)
        if self.board_pos in self.promotion_tiles:
            self.board.start_promotion(self)


class QuasiRoyalPiece(Piece):
    def __init__(
            self,
            board: Board,
            board_pos: Position | None = None,
            side: Side = Side.NONE,
            name: str = '',
            file_name: str = '',
            asset_folder: str = 'util',
            movement: BaseMovement | None = None
    ):
        super().__init__(board, board_pos, side, name, file_name, asset_folder, movement)


class RoyalPiece(QuasiRoyalPiece):
    def __init__(
            self,
            board: Board,
            board_pos: Position | None = None,
            side: Side = Side.NONE,
            name: str = '',
            file_name: str = '',
            asset_folder: str = 'util',
            movement: BaseMovement | None = None
    ):
        super().__init__(board, board_pos, side, name, file_name, asset_folder, movement)
