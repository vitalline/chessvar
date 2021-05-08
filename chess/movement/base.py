from __future__ import annotations

from enum import Enum
from typing import Type, TypeVar, TYPE_CHECKING, Optional

from chess.movement.move import Move
from chess.movement.util import *

if TYPE_CHECKING:
    from chess.board import Board


class Directions(Enum):
    NONE = []
    PAWN = [(1, 0, 1)]
    KNIGHT = sym([(1, 2, 1), (2, 1, 1)])
    BISHOP = sym([(1, 1)])
    ROOK = sym([(1, 0)])
    QUEEN = BISHOP + ROOK
    ARCHBISHOP = BISHOP + KNIGHT
    CHANCELLOR = ROOK + KNIGHT
    AMAZON = QUEEN + KNIGHT
    CAMEL = sym([(1, 3, 1), (3, 1, 1)])
    ODDIN = sym([(1, 0, 1), (1, 2, 1), (2, 1, 1)])
    EVANS = sym([(1, 1, 1), (2, 0, 1), (2, 2, 1)])
    SQUIRE = ODDIN + EVANS
    RHOMB = sym([(1, 0, 2), (1, 1, 1)])
    PAWN2 = [(1, 0, 2)]
    WAZIR = sym([(1, 0, 1)])
    FERZ = sym([(1, 1, 1)])
    GOLD_SHOGI = sym([(1, 0, 1)]) + [(1, 1, 1), (1, -1, 1)]
    SILVER_SHOGI = sym([(1, 1, 1)]) + [(1, 0, 1)]
    KNIGHT_SHOGI = [(2, 1, 1), (2, -1, 1)]
    LANCE_SHOGI = [(1, 0)]
    ROOK_SHOGI = ROOK + FERZ
    BISHOP_SHOGI = BISHOP + WAZIR


class BaseMovement(object):
    def __init__(self, board: Board):
        self.board = board

    def moves(self, pos_from: Tuple[int, int]):
        return


class BaseDirectionalMovement(BaseMovement):
    def __init__(self, board: Board, directions: Directions):
        super().__init__(board)
        self.directions = directions.value

    def skip_condition(self, move: Move, direction: Tuple[int, int, Optional[int]]) -> bool:
        return False

    def stop_condition(self, move: Move, direction: Tuple[int, int, Optional[int]]) -> bool:
        return False

    def transform(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        return pos

    def moves(self, pos_from: Tuple[int, int]):
        if self.board.not_on_board(pos_from):
            return
        direction_id = 0
        while direction_id < len(self.directions):
            direction = self.board.get_side(pos_from).direction(self.directions[direction_id])
            current_pos = pos_from
            distance = 0
            move = Move(pos_from, current_pos)
            while not self.board.not_on_board(self.transform(current_pos)):
                if self.stop_condition(move, direction):
                    direction_id += 1
                    break
                current_pos = add(current_pos, direction)
                distance += 1
                if self.board.not_on_board(self.transform(current_pos)):
                    direction_id += 1
                    break
                move = Move(pos_from, current_pos)
                if self.skip_condition(move, direction):
                    continue
                move.pos_to = self.transform(move.pos_to)
                yield move
            else:
                direction_id += 1


class RiderMovement(BaseDirectionalMovement):
    def __init__(self, board: Board, directions: Directions):
        super().__init__(board, directions)

    def stop_condition(self, move: Move, direction: Tuple[int, int, Optional[int]]) -> bool:
        return self.board.not_on_board(add(move.pos_to, direction[:2])) \
               or len(direction) > 2 and (move.pos_to == add(move.pos_from, mul(direction[:2], direction[2]))) \
               or self.board.get_side(move.pos_from) == self.board.get_side(add(move.pos_to, direction[:2])) \
               or self.board.get_side(move.pos_from) == self.board.get_side(move.pos_to).opponent()


M = TypeVar('M', bound=BaseMovement)


def gen_movement(board: Board, base_type: Type[M], params: Directions):
    return type('', (base_type, object), {})(board, params)


def gen_movements(board: Board, settings: List[Tuple[Type[M], Directions]]):
    return [gen_movement(board, setting[0], setting[1]) for setting in settings]
