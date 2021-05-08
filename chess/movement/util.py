from typing import Tuple, List, Union


def add(pos: Tuple[int, int], dpos: Tuple[int, int]) -> Tuple[int, int]:
    return pos[0] + dpos[0], pos[1] + dpos[1]


def sub(pos: Tuple[int, int], dpos: Tuple[int, int]) -> Tuple[int, int]:
    return pos[0] - dpos[0], pos[1] - dpos[1]


def mul(pos: Tuple[int, int], factor: int) -> Tuple[int, int]:
    return pos[0] * factor, pos[1] * factor


def sym(poss: List[Union[Tuple[int, int], Tuple[int, int, int]]]) -> List[Union[Tuple[int, int], Tuple[int, int, int]]]:
    return list(set(sum([[
        (pos[0], pos[1], *pos[2:]), (pos[1], -pos[0], *pos[2:]),
        (-pos[0], -pos[1], *pos[2:]), (-pos[1], pos[0], *pos[2:])
    ] for pos in poss], [])))
