from __future__ import annotations

from typing import TYPE_CHECKING

from chess.movement.util import Position, to_algebraic as toa
from chess.pieces.side import Side
from chess.util import Default, Unset

if TYPE_CHECKING:
    from chess.movement.base import BaseMovement
    from chess.pieces.piece import Piece


class Move(object):
    def __init__(
        self,
        pos_from: Position | None = None,
        pos_to: Position | None = None,
        movement_type: type[BaseMovement] | None = None,
        piece: Piece | None = None,
        captured_piece: Piece | None = None,
        swapped_piece: Piece | None = None,
        placed_piece: type[Piece] | None = None,
        promotion: Piece | frozenset | None = None,
        chained_move: Move | frozenset | None = None,
        tag: str | None = None,
        is_edit: int = 0
    ):
        self.pos_from = pos_from
        self.pos_to = pos_to
        self.movement_type = movement_type
        self.piece = piece
        self.captured_piece = captured_piece
        self.swapped_piece = swapped_piece
        self.placed_piece = placed_piece
        self.promotion = promotion
        self.chained_move = chained_move
        self.tag = tag
        self.is_edit = is_edit

    def set(
        self,
        pos_from: Position | None = None,
        pos_to: Position | None = None,
        movement_type: type[BaseMovement] | None = None,
        piece: Piece | None = None,
        captured_piece: Piece | None = None,
        swapped_piece: Piece | None = None,
        placed_piece: type[Piece] | None = None,
        promotion: Piece | frozenset | type(Default) | None = None,
        chained_move: Move | frozenset | type(Default) | None = None,
        tag: str | None = None,
        is_edit: int | None = None
    ) -> Move:
        self.pos_from = pos_from or self.pos_from
        self.pos_to = pos_to or self.pos_to
        self.piece = piece or self.piece
        self.movement_type = movement_type or self.movement_type
        self.captured_piece = captured_piece or self.captured_piece
        self.swapped_piece = swapped_piece or self.swapped_piece
        self.placed_piece = placed_piece or self.placed_piece
        self.promotion = (
            promotion if promotion not in {None, Default}
            else None if promotion is Default else self.promotion
        )
        self.chained_move = (
            chained_move if chained_move not in {None, Default}
            else None if chained_move is Default else self.chained_move
        )
        self.tag = tag or self.tag
        self.is_edit = is_edit if is_edit is not None else self.is_edit
        return self

    def matches(self, other: Move) -> bool:
        return (
            not not other
            and self.pos_from == other.pos_from
            and self.pos_to == other.pos_to
            # NB: "self.movement_type == other.movement_type" does not work for multiclass types loaded from a save file
            and (self.movement_type is None) == (other.movement_type is None)
            and (self.movement_type is None or self.movement_type.__name__ == other.movement_type.__name__)
            and type(self.piece) is type(other.piece)
            and type(self.captured_piece) is type(other.captured_piece)
            and type(self.swapped_piece) is type(other.swapped_piece)
            and self.placed_piece is other.placed_piece
            and (not self.promotion or self.promotion.matches(other.promotion))
            and (
                self.chained_move.matches(other.chained_move)
                if isinstance(self.chained_move, Move) else
                self.chained_move == other.chained_move
            )
            and self.tag == other.tag
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
            self.placed_piece,
            self.promotion,
            self.chained_move,
            self.tag,
            self.is_edit
        )

    def __deepcopy__(self, memo):
        return Move(
            self.pos_from,
            self.pos_to,
            self.movement_type,
            self.piece.__copy__() if self.piece else self.piece,
            self.captured_piece.__copy__() if self.captured_piece else self.captured_piece,
            self.swapped_piece.__copy__() if self.swapped_piece else self.swapped_piece,
            self.placed_piece,
            self.promotion.__copy__() if self.promotion else self.promotion,
            self.chained_move.__deepcopy__(memo) if self.chained_move else self.chained_move,
            self.tag,
            self.is_edit
        )

    def __str__(self) -> str:
        board = self.piece.board
        moved = self.pos_from != self.pos_to
        comma = ','
        if self.pos_from is not None and self.pos_to is not None and moved and not self.swapped_piece:
            if self.is_edit:
                string = f"on {toa(self.pos_from)} is moved to {toa(self.pos_to)}"
            else:
                string = f"on {toa(self.pos_from)} goes to {toa(self.pos_to)}"
        elif self.pos_from is None or (self.piece and self.piece.is_empty() and not moved):
            if self.movement_type is not None and self.movement_type.__name__ == 'DropMovement':
                if self.promotion is Unset:
                    string = f"wants to place something on {toa(self.pos_to)}"
                else:
                    string = f"is placed on {toa(self.pos_to)}"
            else:
                if self.promotion is Unset:
                    string = f"wants something to appear on {toa(self.pos_to)}"
                else:
                    string = f"appears on {toa(self.pos_to)}"
        elif self.pos_to is None:
            if self.is_edit == 1:
                string = f"disappears from {toa(self.pos_from)}"
            else:
                string = f"is taken from {toa(self.pos_from)}"
        elif not moved or self.swapped_piece:
            promoted = self.promotion is Unset or self.promotion and (
                self.piece.name != self.promotion.name
                or self.promotion.side not in {self.piece.side, Side.NONE}
            )
            if self.captured_piece is None and self.swapped_piece is None and not promoted:
                string = f"stays on {toa(self.pos_from)}"
            else:
                string = f"on {toa(self.pos_from)}"
                comma = ''
        else:
            string = "does something very mysterious"
        if self.piece:
            if self.piece.is_empty() and not (self.promotion and (self.pos_from is None or not moved)):
                side = board.get_promotion_side(self.piece) if self.is_edit == 1 else board.turn_side
                string = f"{side} {string}"
            elif self.piece.is_empty():
                string = f"{self.promotion} {string}"
            else:
                string = f"{self.piece} {string}"
        else:
            string = f"Piece {string}"
        if self.captured_piece:
            string += f"{comma} takes {self.captured_piece}"
            if self.captured_piece.board_pos != self.pos_to:
                string += f" on {toa(self.captured_piece.board_pos)}"
            comma = ','
        if self.swapped_piece:
            if self.is_edit == 1:
                string += f"{comma} is swapped"
            else:
                string += f"{comma} swaps"
            string = f"{string} with {self.swapped_piece} on {toa(self.pos_to)}"
            comma = ','
        if self.pos_from is not None and not (self.piece and self.piece.is_empty() and not moved) and self.piece:
            if self.promotion is Unset:
                if self.is_edit == 1:
                    string += f"{comma} is promoted"
                else:
                    string += f"{comma} tries to promote"
            elif self.promotion and (
                self.piece.name != self.promotion.name
                or self.promotion.side not in {self.piece.side, Side.NONE}
            ):
                if self.is_edit == 1:
                    promotes = "is promoted"
                else:
                    promotes = "promotes"
                if self.promotion.is_hidden:
                    string += f"{comma} {promotes} to ???"
                elif self.promotion and self.promotion.side not in {self.piece.side, Side.NONE}:
                    string += f"{comma} {promotes} to {self.promotion}"
                else:
                    string += f"{comma} {promotes} to {self.promotion.name}"
        return string
