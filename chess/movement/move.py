from __future__ import annotations

from typing import TYPE_CHECKING, Type

from chess.movement.util import Position, to_alpha

if TYPE_CHECKING:
    from chess.movement.movement import BaseMovement
    from chess.pieces.pieces import Piece


class Move(object):
    def __init__(
            self,
            pos_from: Position | None = None,
            pos_to: Position | None = None,
            movement: BaseMovement | None = None,
            piece: Piece | None = None,
            captured_piece: Piece | None = None,
            swapped_piece: Piece | None = None,
            promotion: Type[Piece] | None = None,
            chained_move: Move | None = None,
            is_edit: bool = False
    ):
        self.pos_from = pos_from
        self.pos_to = pos_to
        self.movement = movement
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
            movement: BaseMovement | None = None,
            piece: Piece | None = None,
            captured_piece: Piece | None = None,
            swapped_piece: Piece | None = None,
            promotion: Type[Piece] | None = None,
            chained_move: Move | bool | None = None,
            is_edit: bool | None = None
    ) -> Move:
        self.pos_from = pos_from or self.pos_from
        self.pos_to = pos_to or self.pos_to
        self.piece = piece or self.piece
        self.movement = movement or self.movement
        self.captured_piece = captured_piece or self.captured_piece
        self.swapped_piece = swapped_piece or self.swapped_piece
        self.promotion = promotion or self.promotion
        self.chained_move = chained_move if chained_move is not None else self.chained_move
        self.is_edit = is_edit if is_edit is not None else self.is_edit
        return self

    def __copy__(self):
        return Move(
            self.pos_from,
            self.pos_to,
            self.movement,
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
            self.movement.__copy__() if isinstance(self.movement, BaseMovement) else self.movement,
            self.piece.__copy__() if isinstance(self.piece, Piece) else self.piece,
            self.captured_piece.__copy__() if isinstance(self.captured_piece, Piece) else self.captured_piece,
            self.swapped_piece.__copy__() if isinstance(self.swapped_piece, Piece) else self.swapped_piece,
            self.promotion,
            self.chained_move.__copy__() if isinstance(self.chained_move, Move) else self.chained_move,
            self.is_edit
        )

    def __eq__(self, other: Move) -> bool:
        return (
            not not other
            and self.pos_from == other.pos_from
            and self.pos_to == other.pos_to
            and self.movement == other.movement
            and self.piece == other.piece
            and self.captured_piece == other.captured_piece
            and self.swapped_piece == other.swapped_piece
            and self.promotion == other.promotion
            and self.chained_move == other.chained_move
            and self.is_edit == other.is_edit
        )

    def __str__(self) -> str:
        if self.pos_from is not None and self.pos_to is not None and self.pos_from != self.pos_to:
            if self.is_edit:
                string = f"on {to_alpha(self.pos_from)} is moved to {to_alpha(self.pos_to)}"
            else:
                string = f"on {to_alpha(self.pos_from)} goes to {to_alpha(self.pos_to)}"
        elif self.pos_from is None or (self.piece and self.piece.is_empty() and self.pos_from == self.pos_to):
            string = f"appears on {to_alpha(self.pos_to)}"
        elif self.pos_to is None:
            string = f"disappears from {to_alpha(self.pos_from)}"
        elif self.pos_from == self.pos_to:
            string = f"decides to stay on {to_alpha(self.pos_from)}"
        else:
            string = 'does something very mysterious'
        if self.piece:
            if self.piece.is_empty() and not (self.promotion and self.pos_from == self.pos_to):
                string = f"{self.piece.side.name()} {string}"
            elif self.piece.is_empty() and self.promotion and self.pos_from == self.pos_to:
                string = f"{self.piece.side.name()} {self.promotion.name} {string}"
            else:
                string = f"{self.piece.side.name()} {self.piece.name} {string}"
        else:
            string = f"Piece {string}"
        if self.captured_piece:
            string += f", takes {self.captured_piece.side.name()} {self.captured_piece.name}"
            if self.captured_piece.board_pos != self.pos_to:
                string += f" on {to_alpha(self.captured_piece.board_pos)}"
        if self.swapped_piece:
            string += f", swaps with {self.swapped_piece.side.name()} {self.swapped_piece.name}"
        if self.promotion and self.pos_from is not None and not (
            self.piece and self.piece.is_empty() and self.pos_from == self.pos_to
        ):
            string += f", promotes to {self.promotion.name}"
        return string
