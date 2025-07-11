from __future__ import annotations

from collections.abc import Callable, Collection
from itertools import zip_longest
from typing import TYPE_CHECKING

from chess.movement.util import Position, to_algebraic as toa
from chess.pieces.side import Side
from chess.util import Default, TypeOr, Unset

if TYPE_CHECKING:
    from chess.movement.base import BaseMovement
    from chess.pieces.piece import AbstractPiece as Piece


class Move(object):
    def __init__(
        self,
        pos_from: Position | None = None,
        pos_to: Position | None = None,
        movement_type: type[BaseMovement] | None = None,
        piece: Piece | None = None,
        captured: list[Piece] | Piece | None = None,
        swapped_piece: Piece | None = None,
        placed_piece: type[Piece] | None = None,
        promotion: Piece | frozenset | None = None,
        chained_move: Move | frozenset | None = None,
        marks: str = '',
        tag: str | None = None,
        is_edit: int = 0,
        is_legal: bool = True
    ):
        if captured and not isinstance(captured, list):
            captured = [captured]
        self.pos_from = pos_from
        self.pos_to = pos_to
        self.movement_type = movement_type
        self.piece = piece
        self.captured = sorted(captured or [], key=lambda x: (x.board_pos or ()))
        self.swapped_piece = swapped_piece
        self.placed_piece = placed_piece
        self.promotion = promotion
        self.chained_move = chained_move
        self.marks = marks
        self.tag = tag
        self.is_edit = is_edit
        self.is_legal = is_legal

    def mark(self, marks: str) -> Move:
        self.marks = self.marks.strip(marks) + marks
        return self

    def unmark(self, marks: str) -> Move:
        self.marks = self.marks.strip(marks)
        return self

    def type_str(self) -> str | None:
        return self.movement_type.type_str() if self.movement_type else None

    def set(
        self,
        pos_from: Position | None = None,
        pos_to: Position | None = None,
        movement_type: type[BaseMovement] | None = None,
        piece: Piece | None = None,
        captured: list[Piece] | Piece | None = None,
        swapped_piece: Piece | None = None,
        placed_piece: type[Piece] | None = None,
        promotion: Piece | frozenset | type(Default) | None = None,
        chained_move: Move | frozenset | type(Default) | None = None,
        marks: str | None = None,
        tag: str | None = None,
        is_edit: int | None = None,
        is_legal: bool | None = None
    ) -> Move:
        self.pos_from = pos_from or self.pos_from
        self.pos_to = pos_to or self.pos_to
        self.piece = piece or self.piece
        self.movement_type = movement_type or self.movement_type
        if captured is not None:
            if not isinstance(captured, Collection):
                captured = [captured, *self.captured]
            self.captured = sorted(captured or [], key=lambda x: (x.board_pos or ()))
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
        self.marks = marks or self.marks
        self.tag = tag or self.tag
        self.is_edit = is_edit if is_edit is not None else self.is_edit
        if is_legal is not None:
            self.is_legal = is_legal and (self.is_legal or self.is_legal is None)
        return self

    def matches(self, other: Move) -> bool:
        return (
            not not other
            and self.pos_from == other.pos_from
            and self.pos_to == other.pos_to
            and self.movement_type == other.movement_type
            and type(self.piece) is type(other.piece)
            and (not self.piece or self.piece.matches(other.piece))
            and (not self.captured) == (not other.captured)
            and (not self.captured or all(
                type(x) is type(y) and (not x or x.matches(y)) for x, y in zip_longest(self.captured, other.captured)
            ))
            and type(self.swapped_piece) is type(other.swapped_piece)
            and (not self.swapped_piece or self.piece.matches(other.swapped_piece))
            and self.placed_piece is other.placed_piece
            and (not self.promotion or self.promotion.matches(other.promotion))
            and (
                self.chained_move.matches(other.chained_move)
                if isinstance(self.chained_move, Move) else
                self.chained_move == other.chained_move
            )
            # marks check most likely unnecessary
            and self.tag == other.tag
            and self.is_edit == other.is_edit
        )

    def __copy__(self):
        return Move(
            self.pos_from,
            self.pos_to,
            self.movement_type,
            self.piece,
            self.captured.copy(),
            self.swapped_piece,
            self.placed_piece,
            self.promotion,
            self.chained_move,
            self.marks,
            self.tag,
            self.is_edit,
            self.is_legal
        )

    def __deepcopy__(self, memo):
        return Move(
            self.pos_from,
            self.pos_to,
            self.movement_type,
            self.piece.__copy__() if self.piece else self.piece,
            [x.__copy__() for x in self.captured],
            self.swapped_piece.__copy__() if self.swapped_piece else self.swapped_piece,
            self.placed_piece,
            self.promotion.__copy__() if self.promotion else self.promotion,
            self.chained_move.__deepcopy__(memo) if self.chained_move else self.chained_move,
            self.marks,
            self.tag,
            self.is_edit,
            self.is_legal
        )

    def __repr__(self):
        string = {0: '', 1: '[E] '}.get(self.is_edit, f'[E{self.is_edit}] ')
        string += f"{self.piece} @ " if self.piece else ''
        string += toa(self.pos_from) if self.pos_from else '*'
        if self.pos_from == self.pos_to:
            string += ' S'
        elif not self.swapped_piece and (not self.captured or self.pos_to not in {x.board_pos for x in self.captured}):
            string += ' -> '
            string += toa(self.pos_to) if self.pos_to else '*'
        for capture in self.captured:
            string += f" x {capture}"
            if capture.board_pos:
                string += f" @ {toa(capture.board_pos)}"
        if self.swapped_piece:
            string += f" <-> {self.swapped_piece} @ {toa(self.pos_to)}"
        if self.placed_piece:
            string += f" v {self.placed_piece}"
        if self.promotion is not None:
            string += ' ^'
            if self.promotion:
                if self.promotion.side and not (self.piece and self.promotion.side == self.piece.side):
                    string += f" {self.promotion.side}"
                if not (self.piece and self.piece.name == self.promotion.name):
                    string += f" {self.promotion.name}"
            else:
                string += ' ?'
        if self.chained_move is not None:
            string += ' &'
        if self.tag:
            string += f" #{self.tag}"
        if self.movement_type:
            string += f" ${self.type_str()}"
        return string

    def __str__(self):
        return self.to_string()

    def to_string(self, piece_name_func: Callable[[TypeOr[Piece]], str] | None = None) -> str:
        if piece_name_func is None:
            piece_name_func = lambda x: str(x)
        name = piece_name_func
        moved = self.pos_from != self.pos_to
        comma = ','
        if self.pos_from is not None and self.pos_to is not None and moved and not self.swapped_piece:
            if self.is_edit:
                string = f"on {toa(self.pos_from)} is moved to {toa(self.pos_to)}"
            else:
                string = f"on {toa(self.pos_from)} goes to {toa(self.pos_to)}"
        elif self.pos_from is None or (self.piece and self.piece.side is Side.NONE and not moved):
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
                name(type(self.piece)) != name(type(self.promotion))
                or self.promotion.side not in {self.piece.side, Side.NONE}
            )
            if not self.captured and self.swapped_piece is None and not promoted:
                string = f"stays on {toa(self.pos_from)}"
            else:
                string = f"on {toa(self.pos_from)}"
                comma = ''
        else:
            string = "does something very mysterious"
        if self.piece:
            if self.piece.side is Side.NONE and not (self.promotion and (self.pos_from is None or not moved)):
                board = self.piece.board
                side = board.get_promotion_side(self.piece) if self.is_edit == 1 else board.turn_side
                string = f"{side} {string}"
            elif self.piece.side is Side.NONE:
                string = f"{name(self.promotion)} {string}"
            else:
                string = f"{name(self.piece)} {string}"
        else:
            string = f"Piece {string}"
        if self.captured:
            string += f"{comma} takes"
            comma = ''
            for i in range(min(len(self.captured), 2)):
                add_end = len(self.captured) == 1 or not i
                add_side = len(self.captured) == 1 or i
                for capture in self.captured:
                    is_end = capture.board_pos == self.pos_to
                    if is_end and not add_end or not is_end and not add_side:
                        continue
                    string += f"{comma} {name(capture)}"
                    if not is_end:
                        string += f" on {toa(capture.board_pos)}"
                    comma = ','
        if self.swapped_piece:
            if self.is_edit == 1:
                string += f"{comma} is swapped"
            else:
                string += f"{comma} swaps"
            string = f"{string} with {name(self.swapped_piece)} on {toa(self.pos_to)}"
            comma = ','
        if self.pos_from is not None and self.piece and not (self.piece.side is Side.NONE and not moved):
            if self.promotion is Unset:
                if self.is_edit == 1:
                    string += f"{comma} is promoted"
                else:
                    string += f"{comma} tries to promote"
            elif self.promotion and (
                name(type(self.piece)) != name(type(self.promotion))
                or self.promotion.side not in {self.piece.side, Side.NONE}
            ):
                if self.is_edit == 1:
                    promotes = "is promoted"
                else:
                    promotes = "promotes"
                if self.promotion.is_hidden:
                    string += f"{comma} {promotes} to ???"
                elif self.promotion and self.promotion.side not in {self.piece.side, Side.NONE}:
                    string += f"{comma} {promotes} to {name(self.promotion)}"
                else:
                    string += f"{comma} {promotes} to {name(type(self.promotion))}"
        return string
