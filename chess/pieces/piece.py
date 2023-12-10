from __future__ import annotations

from enum import Enum
import typing

from cocos.sprite import Sprite

from chess.movement.util import AnyPosition

if typing.TYPE_CHECKING:
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

    def direction(self, dpos: AnyPosition) -> AnyPosition:
        if self == Side.WHITE:
            return dpos
        elif self == Side.BLACK:
            return -dpos[0], dpos[1], *dpos[2:]
        else:
            return 0, 0


class Piece(Sprite):
    def __init__(self,
                 board: Board,
                 side: Side = Side.NONE,
                 name: str = '',
                 movement: typing.Optional[BaseMovement] = None):
        if side == Side.NONE or not name:
            super().__init__("assets/util/none.png")
        else:
            super().__init__(f"assets/pieces/{side.name.lower()}_{name.lower()}.png")
        self.board = board
        self.side = side
        self.name = name
        self.movement = movement if movement is not None else BaseMovement(board)

    def is_empty(self):
        return self.side == Side.NONE or not self.name

    def moves(self, pos: typing.Tuple[int, int]):  # convenience method
        return self.movement.moves(pos)
