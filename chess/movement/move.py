from __future__ import annotations

from typing import TYPE_CHECKING, Type

from chess.movement.util import Position, to_alpha
from chess.util import Default, Unset

if TYPE_CHECKING:
    from chess.movement.movement import BaseMovement
    from chess.pieces.pieces import Piece


class Move(object):
    def __init__(
            self,
            pos_from: Position | None = None,
            pos_to: Position | None = None,
            movement_type: Type[BaseMovement] | None = None,
            piece: Piece | None = None,
            captured_piece: Piece | None = None,
            swapped_piece: Piece | None = None,
            promotion: Piece | frozenset | None = None,
            chained_move: Move | frozenset | None = None,
            is_edit: bool = False
    ):
        self.pos_from = pos_from
        self.pos_to = pos_to
        self.movement_type = movement_type
        self.piece = piece
        self.captured_piece = captured_piece
        self.swapped_piece = swapped_piece
        self.promotion = promotion
        self.chained_move = chained_move
        self.is_edit = is_edit

    def set(
            self,
            pos_from: Position | None = None,
            pos_to: Position | None = None,
            movement_type: Type[BaseMovement] | None = None,
            piece: Piece | None = None,
            captured_piece: Piece | None = None,
            swapped_piece: Piece | None = None,
            promotion: Piece | frozenset | None = None,
            chained_move: Move | frozenset | None = None,
            is_edit: bool | None = None
    ) -> Move:
        self.pos_from = pos_from or self.pos_from
        self.pos_to = pos_to or self.pos_to
        self.piece = piece or self.piece
        self.movement_type = movement_type or self.movement_type
        self.captured_piece = captured_piece or self.captured_piece
        self.swapped_piece = swapped_piece or self.swapped_piece
        self.promotion = (
            promotion if promotion is not None and promotion is not Default
            else None if promotion is Default else self.promotion
        )
        self.chained_move = (
            chained_move if chained_move is not None and chained_move is not Default
            else None if chained_move is Default else self.chained_move
        )
        self.is_edit = is_edit if is_edit is not None else self.is_edit
        return self

    def matches(self, other: Move) -> bool:
        return (
            not not other
            and self.pos_from == other.pos_from
            and self.pos_to == other.pos_to
            and self.movement_type == other.movement_type
            and type(self.piece) is type(other.piece)
            and type(self.captured_piece) is type(other.captured_piece)
            and type(self.swapped_piece) is type(other.swapped_piece)
            and type(self.promotion) is type(other.promotion)
            and (not self.promotion or self.promotion.is_hidden == other.promotion.is_hidden)
            and (
                self.chained_move.matches(other.chained_move)
                if isinstance(self.chained_move, Move) else
                self.chained_move == other.chained_move
            )
            and self.is_edit == other.is_edit
        )

    def __copy__(self):
        return Move(
            self.pos_from,
            self.pos_to,
            self.movement_type,
            self.piece,
            self.captured_piece,
            self.swapped_piece,
            self.promotion,
            self.chained_move,
            self.is_edit
        )

    def __deepcopy__(self, memo):
        return Move(
            self.pos_from,
            self.pos_to,
            self.movement_type,
            self.piece.__copy__() if isinstance(self.piece, Piece) else self.piece,
            self.captured_piece.__copy__() if isinstance(self.captured_piece, Piece) else self.captured_piece,
            self.swapped_piece.__copy__() if isinstance(self.swapped_piece, Piece) else self.swapped_piece,
            self.promotion.__copy__() if isinstance(self.promotion, Piece) else self.promotion,
            self.chained_move.__deepcopy__(memo) if isinstance(self.chained_move, Move) else self.chained_move,
            self.is_edit
        )

    def __str__(self) -> str:
        board = self.piece.board
        moved = self.pos_from != self.pos_to
        if self.pos_from is not None and self.pos_to is not None and moved:
            if self.is_edit:
                string = f"on {to_alpha(self.pos_from)} is moved to {to_alpha(self.pos_to)}"
            else:
                string = f"on {to_alpha(self.pos_from)} goes to {to_alpha(self.pos_to)}"
        elif self.pos_from is None or (self.piece and self.piece.is_empty() and not moved):
            if self.promotion is Unset:
                string = f"wants something to appear on {to_alpha(self.pos_to)}"
            else:
                string = f"appears on {to_alpha(self.pos_to)}"
        elif self.pos_to is None:
            string = f"disappears from {to_alpha(self.pos_from)}"
        elif not moved:
            string = f"decides to stay on {to_alpha(self.pos_from)}"
        else:
            string = "does something very mysterious"
        if self.piece:
            side = self.piece.side
            if self.piece.is_empty() and not (self.promotion and not moved):
                side = board.get_promotion_side(self.piece)
                string = f"{side} {string}"
            elif self.piece.is_empty() and not board.should_hide_pieces:
                side = self.promotion.side
                string = f"{side} {self.promotion.name} {string}"
            elif self.piece.is_empty():
                side = self.promotion.side
                if not self.promotion.is_hidden:
                    string = f"{side} {self.promotion.name} {string}"
                else:
                    string = f"{side} ??? {string}"
            elif not self.piece.is_hidden:
                string = f"{side} {self.piece.name} {string}"
            else:
                string = f"{side} ??? {string}"
        else:
            string = f"Piece {string}"
        if self.captured_piece:
            if self.captured_piece.is_hidden:
                string += f", takes {self.captured_piece.side} ???"
            else:
                string += f", takes {self.captured_piece.side} {self.captured_piece.name}"
            if self.captured_piece.board_pos != self.pos_to:
                string += f" on {to_alpha(self.captured_piece.board_pos)}"
        if self.swapped_piece:
            if self.swapped_piece.is_hidden:
                string += f", swaps with {self.swapped_piece.side} ???"
            else:
                string += f", swaps with {self.swapped_piece.side} {self.swapped_piece.name}"
        if self.pos_from is not None and not (self.piece and self.piece.is_empty() and not moved) and self.piece:
            if self.promotion is Unset:
                string += f", tries to promote"
            elif self.promotion:
                if self.promotion.is_hidden:
                    string += ", promotes to ???"
                else:
                    string += f", promotes to {self.promotion.name}"
        return string
