from __future__ import annotations

from typing import TYPE_CHECKING, Type

from chess.movement.util import Position, to_alpha

if TYPE_CHECKING:
    from chess.movement.movement import BaseMovement
    from chess.pieces.pieces import Piece


class Move(object):
    def __init__(
            self,
            pos_from: Position,
            pos_to: Position,
            movement: BaseMovement | None = None,
            piece: Piece | None = None,
            captured_piece: Piece | None = None,
            promotion: Type[Piece] | None = None,
    ):
        self.pos_from = pos_from
        self.pos_to = pos_to
        self.movement = movement
        self.piece = piece
        self.captured_piece = captured_piece
        self.promotion = promotion

    def set(
            self,
            movement: BaseMovement | None = None,
            piece: Piece | None = None,
            captured_piece: Piece | None = None,
            promotion: Type[Piece] | None = None,
    ) -> Move:
        self.piece = piece or self.piece
        self.movement = movement or self.movement
        self.captured_piece = captured_piece or self.captured_piece
        self.promotion = promotion or self.promotion
        return self

    def __str__(self) -> str:
        string = f"{to_alpha(self.pos_from)} {'->'} {to_alpha(self.pos_to)}"
        if self.piece:
            string = f"{self.piece.side.name()} {self.piece.name} {string}"
        if self.captured_piece:
            string += f", takes {self.captured_piece.side.name()} {self.captured_piece.name}"
        if self.promotion:
            string += f", promotes to {self.promotion.__name__}"
        return string
