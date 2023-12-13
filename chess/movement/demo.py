from __future__ import annotations

from enum import Enum
from itertools import product
from random import choice, randint
from typing import Type, TYPE_CHECKING

from chess.movement.movement import BaseMovement, RiderMovement
from chess.movement.util import AnyDirection, ClashResolution, merge, sym

if TYPE_CHECKING:
    from chess.board import Board


class PieceType(Enum):
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

    def __str__(self):
        return self.name.lower()


class Directions(list[AnyDirection], Enum):
    NONE = []
    PAWN = [(1, 0, 1)]
    PAWN2 = [(1, 0, 2)]
    KNIGHT = sym([(1, 2, 1), (2, 1, 1)])
    BISHOP = sym([(1, 1)])
    ROOK = sym([(1, 0)])
    QUEEN = BISHOP + ROOK
    ARCHBISHOP = BISHOP + KNIGHT
    CHANCELLOR = ROOK + KNIGHT
    AMAZON = QUEEN + KNIGHT
    CAMEL = sym([(1, 3, 1), (3, 1, 1)])
    ZEBRA = sym([(2, 3, 1), (3, 2, 1)])
    WAZIR = sym([(1, 0, 1)])
    FERZ = sym([(1, 1, 1)])
    DABBABA = sym([(2, 0, 1)])
    ALFIL = sym([(2, 2, 1)])
    ODDIN = WAZIR + KNIGHT
    EVANS = FERZ + DABBABA + ALFIL
    SQUIRE = ODDIN + EVANS
    RHOMB = sym([(1, 0, 2), (1, 1, 1)])
    GOLD_SHOGI = sym([(1, 0, 1)]) + [(1, 1, 1), (1, -1, 1)]
    SILVER_SHOGI = sym([(1, 1, 1)]) + [(1, 0, 1)]
    KNIGHT_SHOGI = [(2, 1, 1), (2, -1, 1)]
    LANCE_SHOGI = [(1, 0)]
    ROOK_SHOGI = ROOK + FERZ
    BISHOP_SHOGI = BISHOP + WAZIR
    NIGHTRIDER = sym([(1, 2), (2, 1)])
    CAMELRIDER = sym([(1, 3), (3, 1)])


def balance_pawn(directions: list[AnyDirection]) -> list[AnyDirection]:
    result = []
    for direction in directions:
        max_distance = randint(1, 2)
        if direction[0] > 1 or direction[1] > 1:
            direction = (*direction[:2], 1)
        elif len(direction) == 2 or direction[2] > 2:
            direction = (*direction[:2], max_distance)
        rows, cols, times = direction
        inversion = rows, -cols, times
        result = merge(result, [direction], ClashResolution.SHRINK)
        result = merge(result, [inversion], ClashResolution.SHRINK)
    has_forward_movement = False
    for direction in result:
        if direction[0] > 0:
            has_forward_movement = True
            break
    if not has_forward_movement:
        result = merge(result, choice([
            Directions.PAWN,
            Directions.PAWN2
        ]), ClashResolution.SHRINK)
    return result


def rng_directions() -> list[list[AnyDirection]]:
    bases = [
        Directions.NONE,
        Directions.PAWN,
        Directions.PAWN2,
        Directions.KNIGHT,
        Directions.BISHOP,
        Directions.ROOK,
        Directions.QUEEN,
        Directions.WAZIR,
        Directions.FERZ,
        Directions.DABBABA,
        Directions.ALFIL,
        # Directions.NIGHTRIDER,
        # Directions.CAMELRIDER,
    ]
    modifiers = [
        Directions.NONE,
        Directions.NONE,
        Directions.NONE,
        Directions.PAWN,
        Directions.PAWN2,
        Directions.KNIGHT,
        Directions.WAZIR,
        Directions.FERZ,
        Directions.CAMEL,
        Directions.ZEBRA,
        Directions.LANCE_SHOGI,
        [(1, 0), (-1, 0)],
        [(0, 1), (0, -1)],
        [(1, 0, 1), (-1, 0, 1)],
        [(0, 1, 1), (0, -1, 1)],
        [(1, 1, 1), (1, -1, 1)],
        [(-1, 1, 1), (-1, -1, 1)],
    ]
    return [merge(pair[0], pair[1], ClashResolution.FORMER) for pair in product(bases, modifiers) if pair != ([], [])]


def gen_movement[M: BaseMovement](board: Board, base_type: Type[M], params: list[AnyDirection]):
    return type('', (base_type, object), {})(board, params)


def gen_movements[M: BaseMovement](board: Board, settings: list[tuple[Type[M], list[AnyDirection]]]):
    return [gen_movement(board, setting[0], setting[1]) for setting in settings]


# movement_settings = [(RiderMovement, direction.value) for direction in Directions if direction.value != []]
movement_settings = [(RiderMovement, direction) for direction in rng_directions() if direction != []]


def get_movements(board: Board):
    return gen_movements(board, movement_settings)