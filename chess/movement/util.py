Position = tuple[int, int]
RepeatPosition = tuple[int, int, int]
AnyPosition = Position | RepeatPosition


def add(pos: Position, dpos: Position) -> Position:
    return pos[0] + dpos[0], pos[1] + dpos[1]


def sub(pos: Position, dpos: Position) -> Position:
    return pos[0] - dpos[0], pos[1] - dpos[1]


def mul(pos: Position, factor: int) -> Position:
    return pos[0] * factor, pos[1] * factor


def sym(poss: list[AnyPosition]) -> list[AnyPosition]:
    return list(set(sum([[
        (pos[0], pos[1], *pos[2:]), (pos[1], -pos[0], *pos[2:]),
        (-pos[0], -pos[1], *pos[2:]), (-pos[1], pos[0], *pos[2:])
    ] for pos in poss], [])))
