from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from chess.util import MOVEMENT_SUFFIXES, make_hashable

if TYPE_CHECKING:
    from chess.board import Board
    from chess.movement.move import Move
    from chess.movement.util import Position
    from chess.pieces.piece import AbstractPiece as Piece


class MovementMeta(type):
    def __eq__(cls, other):
        return cls is other or isinstance(other, type) and cls.__bases__ == other.__bases__

    def __hash__(cls):
        return hash((cls.__name__, cls.__bases__))


class BaseMovement(object, metaclass=MovementMeta):
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

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.__copy_args__() == other.__copy_args__()

    def __hash__(self):
        return hash((self.__class__, *make_hashable(self.__copy_args__()[1:])))
