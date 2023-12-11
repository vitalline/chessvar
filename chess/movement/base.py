from __future__ import annotations

from typing import TYPE_CHECKING

from chess.movement.move import Move
from chess.movement.util import AnyPosition, Position, add, mul, merge, clash_max

if TYPE_CHECKING:
    from chess.board import Board


class BaseMovement(object):
    def __init__(self, board: Board):
        self.board = board

    def moves(self, pos_from: Position):
        return ()

    def update(self):
        pass


class BaseDirectionalMovement(BaseMovement):
    def __init__(self, board: Board, directions: list[AnyPosition]):
        super().__init__(board)
        self.directions = directions

    def skip_condition(self, move: Move, direction: AnyPosition) -> bool:
        return False

    def stop_condition(self, move: Move, direction: AnyPosition) -> bool:
        return False

    def transform(self, pos: Position) -> Position:
        return pos

    def moves(self, pos_from: Position):
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
    def __init__(self, board: Board, directions: list[AnyPosition]):
        super().__init__(board, directions)

    def stop_condition(self, move: Move, direction: list[AnyPosition]) -> bool:
        return self.board.not_on_board(add(move.pos_to, direction[:2])) \
               or len(direction) > 2 and (move.pos_to == add(move.pos_from, mul(direction[:2], direction[2]))) \
               or self.board.get_side(move.pos_from) == self.board.get_side(add(move.pos_to, direction[:2])) \
               or self.board.get_side(move.pos_from) == self.board.get_side(move.pos_to).opponent()


class FirstMoveRiderMovement(RiderMovement):
    def __init__(self, board: Board, directions: list[AnyPosition], first_move_directions: list[AnyPosition]):
        super().__init__(board, directions)
        self.first_move = True
        self.base_directions = directions
        self.directions = merge(self.directions, first_move_directions, clash_max)

    def update(self):
        if self.first_move:
            self.first_move = False
            self.directions = self.base_directions


class MultiMovement(BaseMovement):
    def __init__(
            self,
            board: Board,
            move_or_capture: list[BaseMovement] | None = None,
            move: list[BaseMovement] | None = None,
            capture: list[BaseMovement] | None = None
    ):
        self.move_or_capture = move_or_capture or []
        self.move = move or []
        self.capture = capture or []
        super().__init__(board)
        for movement in self.move_or_capture + self.move + self.capture:
            movement.board = board  # just in case.

    def moves(self, pos_from: Position):
        for movement in self.move_or_capture + self.move:
            for move in movement.moves(pos_from):
                if self.board.not_a_piece(move.pos_to):
                    yield move
        for movement in self.move_or_capture + self.capture:
            for move in movement.moves(pos_from):
                if self.board.get_side(move.pos_to) == self.board.get_side(pos_from).opponent():
                    yield move

    def update(self):
        for movement in self.move_or_capture + self.move + self.capture:
            movement.update()
