from __future__ import annotations

from enum import Enum

from chess.movement.util import AnyDirection


class Side(Enum):
    NONE = 0
    WHITE = 1
    BLACK = 2
    NEUTRAL = 10
    IMMUNE = 11
    ANY = -1

    def __bool__(self):
        return self is not Side.NONE

    def opponent(self):
        match self:
            case Side.WHITE:
                return Side.BLACK
            case Side.BLACK:
                return Side.WHITE
            case _:
                return self

    def blocked_by(self, what: Side):
        match self:
            case Side.ANY:
                return False
            case Side.NONE:
                return True
            case _:
                return self is what or what in {Side.IMMUNE}

    def captures(self, what: Side):
        match self:
            case Side.ANY:
                return True
            case Side.NONE:
                return False
            case _:
                return self is not what and what not in {Side.NONE, Side.IMMUNE}

    def direction(self, dpos: AnyDirection | int | None = None) -> AnyDirection | int:
        match self:
            case Side.WHITE:
                return 1 if dpos is None else dpos if type(dpos) is int else dpos
            case Side.BLACK:
                return -1 if dpos is None else -dpos if type(dpos) is int else (-dpos[0], *dpos[1:])
            case _:
                return 0 if dpos is None else 0 if type(dpos) is int else (0, 0)

    def __str__(self):
        match self:
            case Side.NONE:
                return "Empty"
            case Side.WHITE:
                return "White"
            case Side.BLACK:
                return "Black"
            case Side.NEUTRAL:
                return "Neutral"
            case Side.IMMUNE:
                return "Indestructible"
            case Side.ANY:
                return "Universal"
            case _:
                return ""

    def key(self):
        match self:
            case Side.WHITE:
                return "white_"
            case Side.BLACK:
                return "black_"
            case _:
                return ""

    def file_prefix(self):
        match self:
            case Side.WHITE:
                return "0."
            case Side.BLACK:
                return "1."
            case _:
                return ""
