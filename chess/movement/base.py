from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from chess.util import MOVEMENT_SUFFIXES

if TYPE_CHECKING:
    from chess.board import Board
    from chess.movement.move import Move
    from chess.movement.util import Position
    from chess.pieces.piece import AbstractPiece as Piece


class BaseMovement(object):
    def __init__(self, board: Board):
        self.board = board
        self.total_moves = 0

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        return ()

    def update(self, move: Move, piece: Piece):
        self.total_moves += 1

    def undo(self, move: Move, piece: Piece):
        self.total_moves -= 1

    def reload(self, move: Move, piece: Piece):
        self.undo(move, piece)
        self.update(move, piece)

    def set_moves(self, count: int):
        self.total_moves = count

    @classmethod
    def type_str(cls) -> str:
        name = cls.__name__
        for suffix in MOVEMENT_SUFFIXES:
            if name.endswith(suffix, 1):
                name = name[:-len(suffix)]
        return name

    def __copy_args__(self):
        return self.board,

    def __copy__(self):
        clone = self.__class__(*self.__copy_args__())
        clone.total_moves = self.total_moves
        return clone

    def __deepcopy__(self, memo):
        clone = self.__class__(*(deepcopy(x, memo) for x in self.__copy_args__()))
        clone.total_moves = self.total_moves
        return clone
