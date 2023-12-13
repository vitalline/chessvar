from collections.abc import Callable
from itertools import zip_longest


Direction = tuple[int, int]
RepeatDirection = tuple[int, int, int]
RepeatFromDirection = tuple[int, int, int, int]
AnyDirection = Direction | RepeatDirection | RepeatFromDirection
Position = Direction


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
    result = []
    for i, j in zip_longest(a, b, fillvalue=None):
        if i is None and j is not None:
            result.append(j)
        if i is not None and j is None:
            result.append(i)
        if i is not None and j is not None:
            result.append(min(i, j))
    return tuple(result)


def clash_max(a: tuple, b: tuple) -> tuple:
    result = []
    for i, j in zip_longest(a, b, fillvalue=None):
        if i is None or j is None:
            break
        if i is not None and j is not None:
            result.append(max(i, j))
    return tuple(result)


def merge(a: list[AnyDirection], b: list[AnyDirection], clash: Callable[[tuple, tuple], tuple]) -> list[AnyDirection]:
    data = {}
    for i in a + b:
        if i[:2] not in data:
            data[i[:2]] = i[2:]
        else:
            data[i[:2]] = clash(i[2:], data[i[:2]])
    result = [(k[0], k[1], *v) for k, v in data.items()]
    return result


def to_alpha(pos: Position) -> str:
    return chr(pos[1] + 97) + str(pos[0] + 1)


def from_alpha(pos: str) -> Position:
    return int(pos[1:]) - 1, ord(pos[0]) - 97
