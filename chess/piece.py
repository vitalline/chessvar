from __future__ import annotations

from enum import Enum
from typing import Tuple, TYPE_CHECKING, Optional, Union

from cocos.sprite import Sprite

if TYPE_CHECKING:
    from chess.board import Board

from chess.movement.base import BaseMovement


class Side(Enum):
    NONE = 0
    WHITE = 1
    BLACK = 2
    ANY = -1

    def opponent(self):
        if self == Side.WHITE:
            return Side.BLACK
        elif self == Side.BLACK:
            return Side.WHITE
        else:
            return self

    def direction(self, dpos: Union[Tuple[int, int], Tuple[int, int, int]]):
        if self == Side.WHITE:
            return dpos
        elif self == Side.BLACK:
            return -dpos[0], dpos[1], *dpos[2:]
        else:
            return 0, 0


class Type(Enum):
    NONE = 0
    PAWN = 1
    KNIGHT = 2
    BISHOP = 3
    ROOK = 4
    QUEEN = 5
    KING = 6
    AMAZON = 7
    ARCHBISHOP = 8
    BOAT = 9
    CENTAUR = 10
    CHAMPION = 11
    CHANCELLOR = 12
    DRAGON = 13
    ELEPHANT = 14
    EMPRESS = 15
    GIRAFFE = 16
    GRASSHOPPER = 17
    MANN = 18
    NIGHTRIDER = 19
    PRINCESS = 20
    ROOK4 = 21
    UNICORN = 22
    WIZARD = 23
    ZEBRA = 24


class Piece(Sprite):
    def __init__(self, board: Board,
                 side: Side = Side.NONE,
                 piece_type: Type = Type.NONE,
                 movement: Optional[BaseMovement] = None):
        if side == Side.NONE or piece_type == Type.NONE:
            super().__init__("assets/util/none.png")
        else:
            super().__init__(f"assets/pieces/{side.name.lower()}_{piece_type.name.lower()}.png")
        self.board = board
        self.side = side
        self.type = piece_type
        self.movement = movement if movement is not None else BaseMovement(board)

    def is_empty(self):
        return self.side == Side.NONE or self.type == Type.NONE

    def moves(self, pos: Tuple[int, int]):  # convenience method
        return self.movement.moves(pos)
