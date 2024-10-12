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


def idiv(pos: Direction, factor: int) -> Direction:
    return pos[0] // factor, pos[1] // factor


def ddiv(pos: Direction, qpos: Direction) -> int:
    if qpos[0] == 0 and qpos[1] == 0:
        return 0
    if qpos[0] == 0 and qpos[1] != 0 and pos[1] % qpos[1] == 0:
        return pos[1] // qpos[1]
    if qpos[1] == 0 and qpos[0] != 0 and pos[0] % qpos[0] == 0:
        return pos[0] // qpos[0]
    if (
        qpos[0] != 0 and qpos[1] != 0 and
        pos[0] % qpos[0] == 0 and pos[1] % qpos[1] == 0 and
        pos[0] // qpos[0] == pos[1] // qpos[1]
    ):
        return pos[0] // qpos[0]
    return 0


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


UNKNOWN_COORDINATE_STRING = '\u2588' * 2
COORDINATE_ALPHABET = 'abcdefghijklmnopqrstuvwxyz'


def to_alpha(n: int) -> str:
    return '' if n == 0 else to_alpha((n - 1) // 26) + COORDINATE_ALPHABET[(n - 1) % 26]


def from_alpha(s: str) -> int:
    return 0 if not s else from_alpha(s[:-1]) * 26 + COORDINATE_ALPHABET.index(s[-1]) + 1


def to_algebraic(pos: Position | None) -> str:
    if pos is None:
        return UNKNOWN_COORDINATE_STRING
    if pos[0] == -1 and pos[1] == -1:
        return '*'  # '*' means all possible positions
    if pos[0] == -1:
        return f'{to_alpha(pos[1] + 1)}*'  # 'l*' means all positions in the l file
    if pos[1] == -1:
        return f'*{pos[0] + 1}'  # '*n' means all positions in the nth rank
    return f'{to_alpha(pos[1] + 1)}{pos[0] + 1}'  # return as (file, rank), or (x, y)


def from_algebraic(pos: str) -> Position | None:
    if str == UNKNOWN_COORDINATE_STRING:
        return None
    pos = pos.lower()
    if pos[0] == '*' and pos[-1] == '*':  # '*' (or '**') means all positions
        return -1, -1
    if pos[0] == '*':  # '*n' means all positions in the nth rank
        return int(pos[1:]) - 1, -1
    if pos[-1] == '*':  # 'l*' means all positions in the l file
        return -1, from_alpha(pos[:-1]) - 1
    split_index = next((i for i, c in enumerate(pos) if c.isdigit()), len(pos))
    return int(pos[split_index:]) - 1, from_alpha(pos[:split_index]) - 1  # return as (rank, file), or (y, x)
    # this is the opposite of the usual (x, y) coordinate system OR the usual (file, rank) algebraic notation
    # the board is represented as a list of lists, so the rank is the outer list and goes first when indexing


def to_algebraic_map(poss: list[Position], width: int, height: int) -> dict[str, list[Position]]:
    cols = {col for col in range(width)}
    rows = {row for row in range(height)}
    remain = set(poss)
    result = {}
    by_row = {row: set() for row in rows}
    for pos in poss:  # find all files listed for each rank
        by_row[pos[0]].add(pos[1])
    for row in rows:
        if by_row[row] == cols:  # if all positions for the nth rank are listed
            # add '*n' (n, -1) to the result and remove them from the remaining positions
            row_poss = [(row, col) for col in cols]
            result[(row, -1)] = row_poss
            remain.difference_update(row_poss)
    if not remain:  # if all listed positions were discarded, return the result
        if set(result) == {(row, -1) for row in rows}:  # unless all positions for every rank were listed
            # in which case, use '*' (-1, -1) to represent all possible positions
            return {to_algebraic((-1, -1)): sorted(poss)}
        return {to_algebraic(k): sorted(result[k]) for k in sorted(result)}
    by_col = {col: set() for col in cols}
    for pos in poss:  # find all ranks listed for each file
        by_col[pos[1]].add(pos[0])
    for col in cols:
        if by_col[col] == rows:  # if all positions for the l file are listed
            # add 'l*' (-1, l) to the result and remove them from the remaining positions
            col_poss = [(row, col) for row in rows]
            result[(-1, col)] = col_poss
            remain.difference_update(col_poss)
    result |= {pos: [pos] for pos in remain}  # add the remaining positions to the result
    return {to_algebraic(k): sorted(result[k]) for k in sorted(result)}


def from_algebraic_map(poss: list[str], width: int, height: int) -> dict[Position, str]:
    result = {}
    for value in poss:
        if value == UNKNOWN_COORDINATE_STRING:
            continue
        pos = from_algebraic(value)
        if pos[0] == -1 and pos[1] == -1:  # all positions
            result |= {(row, col): value for row in range(height) for col in range(width)}
        elif pos[0] == -1:  # all positions in the l file
            result |= {(row, pos[1]): value for row in range(height)}
        elif pos[1] == -1:  # all positions in the nth rank
            result |= {(pos[0], col): value for col in range(width)}
        else:  # a single position
            result[pos] = value
    return {k: result[k] for k in sorted(result)}
