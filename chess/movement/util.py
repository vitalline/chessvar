from enum import Enum
from itertools import zip_longest


Direction = tuple[int, int]
RepeatDirection = tuple[int, int, int]
RepeatFromDirection = tuple[int, int, int, int]
AnyDirection = Direction | RepeatDirection | RepeatFromDirection
Position = Direction


class ClashResolution(Enum):
    NONE = 0
    EXPAND = 1
    SHRINK = -1
    FORMER = 2
    LATTER = -2


def add(pos: Position, dpos: Direction) -> Position:
    return pos[0] + dpos[0], pos[1] + dpos[1]


def sub(pos: Position, dpos: Direction) -> Position:
    return pos[0] - dpos[0], pos[1] - dpos[1]


def mul(pos: Direction, factor: int) -> Direction:
    return pos[0] * factor, pos[1] * factor


def rot(poss: list[AnyDirection]) -> list[AnyDirection]:
    return list(set(sum([[
        (pos[0], pos[1], *pos[2:]), (pos[1], -pos[0], *pos[2:]),
        (-pos[0], -pos[1], *pos[2:]), (-pos[1], pos[0], *pos[2:])
    ] for pos in poss], [])))


def rot2(poss: list[AnyDirection]) -> list[AnyDirection]:
    return list(set(sum([[
        (pos[0], pos[1], *pos[2:]), (-pos[0], -pos[1], *pos[2:])
    ] for pos in poss], [])))


def sym(poss: list[AnyDirection]) -> list[AnyDirection]:
    return list(set(sum([[
        (pos[0], pos[1], *pos[2:]), (pos[0], -pos[1], *pos[2:]),
        (-pos[0], -pos[1], *pos[2:]), (-pos[0], pos[1], *pos[2:])
    ] for pos in poss], [])))


def symh(poss: list[AnyDirection]) -> list[AnyDirection]:
    return list(set(sum([[
        (pos[0], pos[1], *pos[2:]), (-pos[0], pos[1], *pos[2:])
    ] for pos in poss], [])))


def symv(poss: list[AnyDirection]) -> list[AnyDirection]:
    return list(set(sum([[
        (pos[0], pos[1], *pos[2:]), (pos[0], -pos[1], *pos[2:])
    ] for pos in poss], [])))


def clash_min(a: tuple, b: tuple) -> tuple:
    return tuple(min(i, j) if i and j else i or j for i, j in zip_longest(a, b, fillvalue=0))


def clash_max(a: tuple, b: tuple) -> tuple:
    return tuple(max(i, j) if i and j else 0 for i, j in zip_longest(a, b, fillvalue=0))


def equal(a: AnyDirection, b: AnyDirection) -> bool:
    return a + (0, ) * (4 - len(a)) == b + (0, ) * (4 - len(b))


def merge(a: list[AnyDirection], b: list[AnyDirection], clash_resolution: ClashResolution) -> list[AnyDirection]:
    data = {}
    for i in a + b:
        if i[:2] not in data:
            data[i[:2]] = i
        elif clash_resolution == ClashResolution.FORMER:
            continue
        elif clash_resolution == ClashResolution.LATTER:
            data[i[:2]] = i
        elif clash_resolution == ClashResolution.SHRINK:
            data[i[:2]] = i[:2] + clash_min(i[2:3], data[i[:2]][2:3]) + max(i[3:4], data[i[:2]][3:4])
        elif clash_resolution == ClashResolution.EXPAND:
            data[i[:2]] = i[:2] + clash_max(i[2:3], data[i[:2]][2:3]) + min(i[3:4], data[i[:2]][3:4])
        elif not equal(data[i[:2]], i):
            raise ValueError(f"Clash between directions {data[i[:2]]} and {i} not resolved")
    return list(data.values())


def to_alpha(pos: Position) -> str:
    return chr(pos[1] + 97) + str(pos[0] + 1)


def from_alpha(pos: str) -> Position:
    return int(pos[1:]) - 1, ord(pos[0]) - 97
