from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING

from chess.movement.move import Move
from chess.movement.util import AnyDirection, ClashResolution, Direction, Position, add, merge, mul, sub

if TYPE_CHECKING:
    from chess.board import Board
    from chess.pieces.pieces import Side


class BaseMovement(object):
    def __init__(self, board: Board):
        self.board = board
        self.total_moves = 0

    def moves(self, pos_from: Position, side: Side, theoretical: bool = False):
        return ()

    def update(self, move: Move, side: Side):
        self.total_moves += 1
        self.board.update(move)

    def undo(self, move: Move, side: Side):
        self.total_moves -= 1

    def reload(self, move: Move, side: Side):
        self.undo(move, side)
        self.update(move, side)


class BaseDirectionalMovement(BaseMovement):
    def __init__(self, board: Board, directions: list[AnyDirection]):
        super().__init__(board)
        self.directions = directions

    def skip_condition(self, move: Move, direction: AnyDirection, side: Side) -> bool:
        return False

    def stop_condition(self, move: Move, direction: AnyDirection, side: Side, theoretical: bool = False) -> bool:
        return False

    def transform(self, pos: Position) -> Position:
        return pos

    def moves(self, pos_from: Position, side: Side, theoretical: bool = False):
        if self.board.not_on_board(pos_from):
            return
        side = side if side is not None else self.board.get_side(pos_from)
        direction_id = 0
        while direction_id < len(self.directions):
            direction = side.direction(self.directions[direction_id])
            current_pos = pos_from
            distance = 0
            move = Move(pos_from, self.transform(current_pos), self)
            while not self.board.not_on_board(self.transform(current_pos)):
                if self.stop_condition(move, direction, side, theoretical):
                    direction_id += 1
                    break
                current_pos = add(current_pos, direction)
                distance += 1
                if self.board.not_on_board(self.transform(current_pos)):
                    direction_id += 1
                    break
                move = Move(pos_from, self.transform(current_pos), self)
                if self.skip_condition(move, direction, side):
                    continue
                yield move
            else:
                direction_id += 1


class RiderMovement(BaseDirectionalMovement):
    def __init__(self, board: Board, directions: list[AnyDirection]):
        super().__init__(board, directions)

    def skip_condition(self, move: Move, direction: AnyDirection, side: Side) -> bool:
        if len(direction) < 4:
            return False
        if not direction[3]:
            return False
        for i in range(1, direction[3]):
            if move.pos_to == self.transform(add(move.pos_from, mul(direction[:2], i))):
                return True
        return False

    def stop_condition(self, move: Move, direction: AnyDirection, side: Side, theoretical: bool = False) -> bool:
        next_pos_to = self.transform(add(move.pos_to, direction[:2]))
        return (
                self.board.not_on_board(next_pos_to)
                or move.pos_from == next_pos_to
                or len(direction) > 2 and direction[2] and (
                        move.pos_to == self.transform(add(move.pos_from, mul(direction[:2], direction[2])))
                )
                or not theoretical and (
                    side == self.board.get_side(next_pos_to)
                    or side == self.board.get_side(move.pos_to).opponent() and not self.board.not_a_piece(move.pos_to)
                )
        )


class CylindricalRiderMovement(RiderMovement):
    def __init__(self, board: Board, directions: list[AnyDirection]):
        super().__init__(board, directions)

    def transform(self, pos: Position) -> Position:
        return pos[0], pos[1] % self.board.board_width


class FirstMoveRiderMovement(RiderMovement):
    def __init__(self, board: Board, directions: list[AnyDirection], first_move_directions: list[AnyDirection]):
        super().__init__(board, directions)
        self.base_directions = directions
        self.first_move_directions = first_move_directions
        self.directions = merge(self.directions, self.first_move_directions, ClashResolution.EXPAND)

    def update(self, move: Move, side: Side):
        if not self.total_moves:
            self.directions = self.base_directions
        super().update(move, side)

    def undo(self, move: Move, side: Side):
        super().undo(move, side)
        if not self.total_moves:
            self.directions = merge(self.directions, self.first_move_directions, ClashResolution.EXPAND)


class CastlingMovement(BaseMovement):
    def __init__(
            self,
            board: Board,
            direction: Direction,
            other_piece: Direction,
            other_direction: Direction,
            gap: list[Direction] | None = None
    ):
        super().__init__(board)
        self.direction = direction
        self.other_piece = other_piece
        self.other_direction = other_direction
        self.gap = gap or []

    def moves(self, pos_from: Position, side: Side, theoretical: bool = False):
        if self.total_moves:
            return ()
        side = side if side is not None else self.board.get_side(pos_from)
        other_piece_pos = add(pos_from, side.direction(self.other_piece))
        if self.board.not_on_board(other_piece_pos):
            return ()
        other_piece = self.board.get_piece(other_piece_pos)
        if other_piece.is_empty():
            return ()
        if other_piece.side != side:
            return ()
        if other_piece.movement.total_moves:
            return ()
        if not theoretical:
            for offset in self.gap:
                pos = add(pos_from, offset)
                if not self.board.not_a_piece(pos):
                    return ()
                if pos in self.board.castling_threats:
                    return ()
        return (Move(pos_from, add(pos_from, side.direction(self.direction)), self),)

    def update(self, move: Move, side: Side):
        if sub(move.pos_to, move.pos_from) == side.direction(self.direction):
            other_piece_pos = add(move.pos_from, side.direction(self.other_piece))
            other_piece_pos_to = add(other_piece_pos, side.direction(self.other_direction))
            self.board.move(Move(other_piece_pos, other_piece_pos_to, self, self.board.get_piece(other_piece_pos)))
        super().update(move, side)

    def undo(self, move: Move, side: Side):
        super().undo(move, side)
        if sub(move.pos_to, move.pos_from) == side.direction(self.direction):
            other_piece_pos = add(move.pos_from, side.direction(self.other_piece))
            other_piece_pos_to = add(other_piece_pos, side.direction(self.other_direction))
            self.board.undo(Move(other_piece_pos, other_piece_pos_to, self, self.board.get_piece(other_piece_pos_to)))


class EnPassantTargetMovement(FirstMoveRiderMovement):
    def __init__(
            self,
            board: Board,
            directions: list[AnyDirection],
            first_move_directions: list[AnyDirection],
            en_passant_directions: list[AnyDirection]
    ):
        super().__init__(board, directions, first_move_directions)
        self.en_passant_directions = en_passant_directions

    def update(self, move: Move, side: Side):
        if not self.total_moves:
            for direction in self.en_passant_directions:
                en_passant_square = add(move.pos_from, move.piece.side.direction(direction))
                if self.board.not_a_piece(en_passant_square):
                    self.board.mark_en_passant(move.pos_to, en_passant_square)
        super().update(move, side)

    def undo(self, move: Move, side: Side):
        super().undo(move, side)
        self.board.clear_en_passant()


class EnPassantMovement(RiderMovement):
    def __init__(self, board: Board, directions: list[AnyDirection]):
        super().__init__(board, directions)


class ChainMovement(BaseMovement):
    def __init__(self, board: Board, movements: list[BaseDirectionalMovement], start_index: int = 0):
        super().__init__(board)
        self.start_index = start_index
        self.movements = movements
        for movement in self.movements:
            movement.board = board  # just in case.

    def moves(self, pos_from: Position, side: Side, theoretical: bool = False, index: int = 0):
        if index >= len(self.movements):
            return
        directions = self.movements[index].directions
        for direction in directions:
            self.movements[index].directions = [direction]
            move = None
            for move in self.movements[index].moves(pos_from, side, theoretical):
                if self.start_index <= index:
                    yield copy(move)
            if (
                    move is not None and len(direction) > 2 and direction[2] and
                    move.pos_to == add(pos_from, side.direction(mul(direction[:2], direction[2])))
                    and (theoretical or self.board.get_piece(move.pos_to).is_empty())
            ):
                for move in self.moves(move.pos_to, side, theoretical, index + 1):
                    yield copy(move).set(pos_from=pos_from)
        self.movements[index].directions = directions

    def update(self, move: Move, side: Side):
        for movement in self.movements:
            movement.update(move, side)
        super().update(move, side)

    def undo(self, move: Move, side: Side):
        super().undo(move, side)
        for movement in self.movements:
            movement.undo(move, side)

    def reload(self, move: Move, side: Side):
        super().undo(move, side)
        for movement in self.movements:
            movement.reload(move, side)
        super().update(move, side)


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
            movement.board = board  # again, just in case.

    def moves(self, pos_from: Position, side: Side, theoretical: bool = False):
        side = side if side is not None else self.board.get_side(pos_from)
        for movement in self.move_or_capture + self.move:
            for move in movement.moves(pos_from, side, theoretical):
                if theoretical or self.board.not_a_piece(move.pos_to):
                    yield copy(move)
        for movement in self.move_or_capture + self.capture:
            for move in movement.moves(pos_from, side, theoretical):
                if theoretical or self.board.get_side(move.pos_to) == side.opponent():
                    yield copy(move)

    def update(self, move: Move, side: Side):
        for movement in self.move_or_capture + self.move + self.capture:
            movement.update(move, side)
        super().update(move, side)

    def undo(self, move: Move, side: Side):
        super().undo(move, side)
        for movement in self.move_or_capture + self.move + self.capture:
            movement.undo(move, side)

    def reload(self, move: Move, side: Side):
        super().undo(move, side)
        for movement in self.move_or_capture + self.move + self.capture:
            movement.reload(move, side)
        super().update(move, side)
