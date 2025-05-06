from collections.abc import Collection, Sequence
from enum import Enum
from itertools import zip_longest
from typing import TypeAlias

Direction: TypeAlias = tuple[int, int]
RepeatDirection: TypeAlias = tuple[int, int, int]
RepeatFromDirection: TypeAlias = tuple[int, int, int, int]
AnyDirection: TypeAlias = Direction | RepeatDirection | RepeatFromDirection
Position: TypeAlias = Direction
GenericPosition: TypeAlias = tuple[int | str, int | str]


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
    if qpos[0] == pos[0] == 0 and qpos[1] != 0 and pos[1] % qpos[1] == 0:
        return pos[1] // qpos[1]
    if qpos[1] == pos[1] == 0 and qpos[0] != 0 and pos[0] % qpos[0] == 0:
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


UNKNOWN = '\u2588' * 2
ALPHABET = 'abcdefghijklmnopqrstuvwxyz'
ANY = '*'   # all positions in the nth rank/file
LAST = '_'  # all positions in the last rank/file
NONE = ''   # no position
generics = {ANY, LAST}


def to_alpha(n: int) -> str:
    if n < 0:
        return to_alpha(-n).upper()
    return '' if n == 0 else to_alpha((n - 1) // 26) + ALPHABET[(n - 1) % 26]


def from_alpha(s: str) -> int:
    if s.isupper():
        return -from_alpha(s.lower())
    return 0 if not s else from_alpha(s[:-1]) * 26 + ALPHABET.index(s[-1]) + 1


def to_algebraic(pos: GenericPosition | None) -> str:
    if pos is None:
        return UNKNOWN
    if pos[0] in generics and pos[1] in generics:
        return pos[0] + (pos[1] if pos[0] != pos[1] else '')
    if pos[0] in generics:
        return f'{to_alpha(pos[1] + (0 if pos[1] < 0 else 1))}{pos[0]}'
    if pos[1] in generics:
        return f'{pos[1]}{pos[0] + 1}'
    return f'{to_alpha(pos[1] + (0 if pos[1] < 0 else 1))}{pos[0] + 1}'  # return as (file, rank), or (x, y)


def from_algebraic(pos: str) -> GenericPosition | None:
    if not pos:
        return None
    if pos == UNKNOWN:
        return None
    sign_alpha = lambda x: (i := from_alpha(x)) + (1 if i < 0 else 0)
    if pos[0] in generics and pos[-1] in generics:
        return pos[0], pos[-1]
    if pos[0] in generics:
        return int(pos[1:]) - 1, pos[0]
    if pos[-1] in generics:
        return pos[-1], sign_alpha(pos[:-1]) - 1
    split_index = next((i for i, c in enumerate(pos) if not c.isalpha()), len(pos))
    return int(pos[split_index:]) - 1, sign_alpha(pos[:split_index]) - 1  # return as (rank, file), or (y, x)
    # this is the opposite of the usual (x, y) coordinate system OR the usual (file, rank) algebraic notation
    # the board is represented as a list of lists, so the rank is the outer list and goes first when indexing


def is_algebraic(pos: str) -> bool:
    try:
        return from_algebraic(pos) is not None
    except ValueError:
        return False


def sort_key(pos: str | GenericPosition) -> tuple:
    sort_rank = lambda x: ('0', x)
    sort_file = lambda x: ('0' if x < 0 else '1', abs(x))
    if isinstance(pos, str):
        return '0', '', pos, '', pos
    if pos[0] in generics and pos[1] in generics:
        return '1', '', pos[0], '', pos[1]
    if pos[0] in generics:
        return '2', '', pos[0], *sort_file(pos[1])
    if pos[1] in generics:
        return '2', *sort_rank(pos[0]), '', pos[1]
    return '2', *sort_rank(pos[0]), *sort_file(pos[1])


def to_algebraic_map(
    poss: Sequence[Position],
    width: int,
    height: int,
    x_offset: int,
    y_offset: int,
    areas: dict[str, Collection[Position]],
) -> dict[str, Sequence[Position]]:
    result = {}
    # Helper function used to condense a list of positions by grouping filled areas, ranks and files together as strings
    def make_map() -> dict[str, Sequence[Position]]:  # Generate a mapping from area groups to lists of position tuples
        return {k if isinstance(k, str) else to_algebraic(k): sorted(result[k]) for k in sorted(result, key=sort_key)}
    # Step 1: Check if the position sequence contains every position on the board
    rows, cols = set(y + y_offset for y in range(height)), set(x + x_offset for x in range(width))
    remain = set(poss)
    all_squares = {(row, col) for row in rows for col in cols}
    if remain == all_squares:  # if all positions are listed
        # use '*' (ANY) to represent all possible positions
        return {ANY: sorted(poss)}
    # Step 2: Check if there exists a group of areas that, when combined, covers all positions in the sequence
    by_area = {area: set() for area in areas}  # find all areas listed for each position
    for pos in poss:
        for area in areas:
            if pos in areas[area]:
                by_area[area].add(pos)
    for area in areas:
        if by_area[area] == areas[area]:  # if all positions for the area are listed
            # add the area to the result and remove them from the remaining positions
            result[area] = sorted(areas[area])
            remain.difference_update(areas[area])
        if not remain:  # if all listed positions were discarded, return the result
            return {k: sorted(result[k]) for k in sorted(result)}
    # Step 3: Check if there exists a set of ranks and files that covers all positions in the sequence
    result = {}  # NB: we erase the previous result to avoid mixing area names and rank/file templates
    remain = set(poss)
    # a) find all files listed for each rank
    by_row = {row: set() for row, _ in poss}
    for pos in poss:
        by_row[pos[0]].add(pos[1])
    for row in by_row:
        if by_row[row] == cols:  # if all positions for the nth rank are listed
            # add '*n' (n, ANY) to the result and remove them from the remaining positions
            row_poss = [(row, col) for col in cols]
            result[(row, ANY)] = row_poss
            remain.difference_update(row_poss)
        if not remain:  # if all listed positions were discarded, return the result
            return make_map()
    # b) find all ranks listed for each file
    by_col = {col: set() for _, col in poss}
    for pos in poss:
        by_col[pos[1]].add(pos[0])
    for col in by_col:
        if by_col[col] == rows:  # if all positions for the l file are listed
            # add 'l*' (ANY, l) to the result and remove them from the remaining positions
            col_poss = [(row, col) for row in rows]
            result[(ANY, col)] = col_poss
            remain.difference_update(col_poss)
        if not remain:  # if all listed positions were discarded, return the result
            return make_map()
    # Step 4: Add the remaining positions to the result
    result |= {pos: [pos] for pos in remain}
    return make_map()


def from_algebraic_map(
    poss: Sequence[str],
    width: int,
    height: int,
    x_offset: int,
    y_offset: int,
    areas: dict[str, Collection[Position]],
) -> dict[Position, str]:
    result = {}
    for value in poss:
        if value == UNKNOWN:
            continue
        if value in areas:
            result |= {pos: value for pos in areas[value]}
            continue
        pos = from_algebraic(value)
        if pos[0] == ANY and pos[1] == ANY:  # all positions
            result |= {(row + y_offset, col + x_offset): value for row in range(height) for col in range(width)}
        elif pos[0] == ANY:  # all positions in the l file
            result |= {(row + y_offset, pos[1]): value for row in range(height)}
        elif pos[1] == ANY:  # all positions in the nth rank
            result |= {(pos[0], col + x_offset): value for col in range(width)}
        else:  # a single position
            result[pos] = value
    return {k: result[k] for k in sorted(result)}


def resolve(pos: GenericPosition, last: GenericPosition = None) -> Position:
    if last is None:
        return pos
    if LAST not in pos:
        return pos
    if pos == (LAST, LAST):
        return last
    if pos[0] == LAST and pos[1] == last[1]:
        pos = (last[0], pos[1])
    if pos[1] == LAST and pos[0] == last[0]:
        pos = (pos[0], last[1])
    return pos
