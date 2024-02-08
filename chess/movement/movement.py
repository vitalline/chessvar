from __future__ import annotations

from copy import copy, deepcopy
from math import ceil
from random import randrange
from typing import TYPE_CHECKING

from chess.movement.move import Move
from chess.movement.util import AnyDirection, Direction, Position, add, sub, mul, ddiv

if TYPE_CHECKING:
    from chess.board import Board
    from chess.pieces.pieces import Piece


class BaseMovement(object):
    def __init__(self, board: Board):
        self.board = board
        self.total_moves = 0

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        return ()

    def update(self, move: Move, piece: Piece):
        self.total_moves += 1
        self.board.update_board(move)

    def undo(self, move: Move, piece: Piece):
        self.total_moves -= 1

    def reload(self, move: Move, piece: Piece):
        self.undo(move, piece)
        self.update(move, piece)

    def __copy_args__(self):
        return self.board,

    def __copy__(self):
        clone = self.__class__(*self.__copy_args__())
        clone.total_moves = self.total_moves
        return clone

    def __deepcopy__(self, memo):
        return self.__copy__()


class BaseDirectionalMovement(BaseMovement):
    def __init__(self, board: Board, directions: list[AnyDirection]):
        super().__init__(board)
        self.directions = directions

    def initialize_direction(self, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        pass

    def advance_direction(self, move: Move, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        pass

    def skip_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        return False

    def stop_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        return False

    def transform(self, pos: Position) -> Position:
        return pos

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        if self.board.not_on_board(pos_from):
            return ()
        direction_id = 0
        while direction_id < len(self.directions):
            direction = piece.side.direction(self.directions[direction_id])
            if direction[:2] == (0, 0):
                yield Move(pos_from, self.transform(pos_from), self)
                direction_id += 1
                continue
            self.initialize_direction(direction, pos_from, piece)
            current_pos = pos_from
            distance = 0
            move = Move(pos_from, self.transform(current_pos), self)
            while not self.board.not_on_board(self.transform(current_pos)):
                if self.stop_condition(move, direction, piece, theoretical):
                    direction_id += 1
                    break
                current_pos = add(current_pos, direction[:2])
                distance += 1
                move = Move(pos_from, self.transform(current_pos), self)
                self.advance_direction(move, direction, pos_from, piece)
                if self.skip_condition(move, direction, piece, theoretical):
                    continue
                yield move
            else:
                direction_id += 1

    def __copy_args__(self):
        return self.board, copy(self.directions)


class RiderMovement(BaseDirectionalMovement):
    def __init__(self, board: Board, directions: list[AnyDirection]):
        super().__init__(board, directions)

    def skip_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        if len(direction) < 4:
            return False
        if not direction[3]:
            return False
        offset = sub(move.pos_to, move.pos_from)
        steps = ddiv(offset, direction[:2])
        if 0 < steps < direction[3]:
            return True
        return False

    def stop_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        next_pos_to = self.transform(add(move.pos_to, direction[:2]))
        return (
            self.board.not_on_board(next_pos_to)
            or move.pos_from == next_pos_to
            or len(direction) > 2 and direction[2] and (
                move.pos_to == self.transform(add(move.pos_from, mul(direction[:2], direction[2])))
            )
            or not theoretical and (
                (piece.side == (next_piece := self.board.get_piece(next_pos_to)).side and piece != next_piece)
                or (piece.side == self.board.get_side(move.pos_to).opponent() and move.pos_from != move.pos_to)
            )
        )


class HalflingRiderMovement(RiderMovement):

    def __init__(self, board: Board, directions: list[AnyDirection], shift: int = 0):
        super().__init__(board, directions)
        self.board_size = self.board.board_height, self.board.board_width
        self.current_distance = 0
        self.max_distance = 0
        self.shift = shift

    def distance_to_edge(self, position: int, direction: int, size: int) -> int:
        if direction == 0:
            return size
        return (((size - position - 1) if direction > 0 else position) - self.shift) // abs(direction)

    def initialize_direction(self, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        self.current_distance = 0
        self.max_distance = min(ceil(
            self.distance_to_edge(pos_from[i], direction[i], self.board_size[i]) / 2
        ) for i in range(2))

    def advance_direction(self, move: Move, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        self.current_distance += 1

    def stop_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        return self.current_distance >= self.max_distance or super().stop_condition(move, direction, piece, theoretical)

    def __copy_args__(self):
        return self.board, copy(self.directions), self.shift


class CannonRiderMovement(RiderMovement):
    def __init__(self, board: Board, directions: list[AnyDirection]):
        super().__init__(board, directions)
        self.jumped = None

    def initialize_direction(self, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        self.jumped = -1

    def advance_direction(self, move: Move, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        if self.jumped == -1:
            if not self.board.not_a_piece(self.transform(move.pos_to)):
                self.jumped = 0
        elif self.jumped == 0:
            self.jumped = 1

    def skip_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        return super().skip_condition(move, direction, piece, theoretical) if self.jumped == 1 else not theoretical

    def stop_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        if self.jumped == 0 and not theoretical:
            next_pos_to = self.transform(add(move.pos_to, direction[:2]))
            if piece.side == (next_piece := self.board.get_piece(next_pos_to)).side and piece != next_piece:
                return True
        return super().stop_condition(move, direction, piece, theoretical or self.jumped != 1)


class SpaciousRiderMovement(RiderMovement):
    def __init__(self, board: Board, directions: list[AnyDirection]):
        super().__init__(board, directions)

    def spacious_transform(self, pos: Position) -> Position:
        # return pos[0] % self.board.board_height, pos[1] % self.board.board_width
        return pos  # as much as i like the idea of a toroidal movement condition, it's just not practical for this game

    def skip_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        next_pos_to = self.transform(add(move.pos_to, direction[:2]))
        check_space = self.spacious_transform(next_pos_to)
        check_state = check_space == self.spacious_transform(move.pos_from) or self.board.not_a_piece(check_space)
        return not check_state or super().skip_condition(move, direction, piece, theoretical)


class CylindricalRiderMovement(RiderMovement):
    def __init__(self, board: Board, directions: list[AnyDirection]):
        super().__init__(board, directions)

    def transform(self, pos: Position) -> Position:
        return pos[0], pos[1] % self.board.board_width


class RangedCaptureRiderMovement(RiderMovement):
    def __init__(self, board: Board, directions: list[AnyDirection]):
        super().__init__(board, directions)

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            if not theoretical:
                captured_piece = self.board.get_piece(move.pos_to)
                if not captured_piece.is_empty():
                    move.captured_piece = captured_piece
                    move.pos_to = move.pos_from
            yield move

    def skip_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        if move.captured_piece:
            pos_to = move.captured_piece.board_pos
            move.pos_to = pos_to
            result = super().skip_condition(move, direction, piece, theoretical)
            move.pos_to = move.pos_from
            return result
        return super().skip_condition(move, direction, piece, theoretical)

    def stop_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        if move.captured_piece:
            pos_to = move.captured_piece.board_pos
            move.pos_to = pos_to
            result = super().stop_condition(move, direction, piece, theoretical)
            move.pos_to = move.pos_from
            return result
        return super().stop_condition(move, direction, piece, theoretical)


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

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        if self.total_moves:
            return ()
        other_piece_pos = add(pos_from, piece.side.direction(self.other_piece))
        if self.board.not_on_board(other_piece_pos):
            return ()
        other_piece = self.board.get_piece(other_piece_pos)
        if other_piece.is_empty():
            return ()
        if other_piece.side != piece.side:
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
        self_move = Move(pos_from, add(pos_from, piece.side.direction(self.direction)), self)
        other_piece_pos_to = add(other_piece_pos, piece.side.direction(self.other_direction))
        other_move = Move(other_piece_pos, other_piece_pos_to, self, other_piece)
        return self_move.set(chained_move=other_move),

    def __copy_args__(self):
        return self.board, self.direction, self.other_piece, self.other_direction, copy(self.gap)


class EnPassantTargetRiderMovement(RiderMovement):
    def __init__(self, board: Board, directions: list[AnyDirection]):
        super().__init__(board, directions)

    def update(self, move: Move, piece: Piece):
        for direction in self.directions:
            direction = piece.side.direction(direction)
            offset = sub(move.pos_to, move.pos_from)
            steps = ddiv(offset, direction[:2])
            if len(direction) > 2 and direction[2] > 0:
                steps = min(steps, direction[2])
            if steps < 2:
                continue
            positions = [add(move.pos_from, mul(direction[:2], i)) for i in range(1, steps)]
            is_clear = True
            for pos in positions:
                if not self.board.not_a_piece(pos):
                    is_clear = False
                    break
            if is_clear:
                for pos in positions:
                    self.board.mark_en_passant(move.pos_to, pos)
        super().update(move, piece)

    def undo(self, move: Move, piece: Piece):
        super().undo(move, piece)
        self.board.clear_en_passant()


class EnPassantRiderMovement(RiderMovement):
    def __init__(self, board: Board, directions: list[AnyDirection]):
        super().__init__(board, directions)

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            if not theoretical:
                if move.pos_to in self.board.en_passant_markers:
                    move.captured_piece = self.board.en_passant_target
            yield move


class BaseMultiMovement(BaseMovement):
    def __init__(self, board: Board, movements: list[BaseMovement]):
        super().__init__(board)
        self.movements = movements
        for movement in self.movements:
            movement.board = board  # just in case.

    def update(self, move: Move, piece: Piece):
        for movement in self.movements:
            movement.update(move, piece)
        super().update(move, piece)

    def undo(self, move: Move, piece: Piece):
        super().undo(move, piece)
        for movement in self.movements:
            movement.undo(move, piece)

    def reload(self, move: Move, piece: Piece):
        super().undo(move, piece)
        for movement in self.movements:
            movement.reload(move, piece)
        super().update(move, piece)

    def __copy_args__(self):
        return self.board, deepcopy(self.movements)


class FirstMoveMovement(BaseMultiMovement):
    def __init__(
            self,
            board: Board,
            movements: list[BaseMovement] | None = None,
            first_move_movements: list[BaseMovement] | None = None
    ):
        self.base_movements = movements or []
        self.first_move_movements = first_move_movements or []
        super().__init__(board, self.base_movements + self.first_move_movements)

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        movements = self.movements if not self.total_moves else self.base_movements
        for movement in movements:
            for move in movement.moves(pos_from, piece, theoretical):
                yield copy(move)

    def __copy_args__(self):
        return self.board, copy(self.movements), copy(self.first_move_movements)


class BentMovement(BaseMultiMovement):
    def __init__(self, board: Board, movements: list[BaseDirectionalMovement], start_index: int = 0):
        super().__init__(board, movements)
        self.start_index = start_index

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False, index: int = 0):
        if index >= len(self.movements):
            return ()
        movement = self.movements[index]
        if isinstance(movement, BaseDirectionalMovement):
            directions = movement.directions
            for direction in directions:
                movement.directions = [direction]
                move = None
                for move in movement.moves(pos_from, piece, theoretical):
                    if self.start_index <= index:
                        yield copy(move)
                if (
                        move is not None and len(direction) > 2 and direction[2] and
                        move.pos_to == add(pos_from, piece.side.direction(mul(direction[:2], direction[2])))
                        and (theoretical or self.board.get_piece(move.pos_to).is_empty())
                ):
                    for bent_move in self.moves(move.pos_to, piece, theoretical, index + 1):
                        yield copy(bent_move).set(pos_from=pos_from)
            movement.directions = directions
        else:
            return ()

    def __copy_args__(self):
        return self.board, deepcopy(self.movements), self.start_index


class ChainMovement(BaseMultiMovement):
    def __init__(self, board: Board, movements: list[BaseMovement]):
        super().__init__(board, movements)

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False, index: int = 0):
        if index >= len(self.movements):
            return ()
        if index == len(self.movements) - 1:
            for move in self.movements[index].moves(pos_from, piece, theoretical):
                yield copy(move).set(chained_move=False)
            return ()
        if theoretical:
            for move in self.movements[index].moves(pos_from, piece, theoretical):
                for chained_move in self.moves(move.pos_to, piece, theoretical, index + 1):
                    yield copy(move).set(pos_to=chained_move.pos_to)
        else:
            for move in self.movements[index].moves(pos_from, piece, theoretical):
                self.board.update_move(move)  # this is most likely SUPER inefficient but i've spent about a day on this
                self.board.move(move)  # and i'm not about to spend another day trying to figure out how to make it FAST
                chain_options = []  # also what this does is it makes sure the board state is updated after each chained
                for chained_move in self.moves(move.pos_to, piece, theoretical, index + 1):  # move so that the next can
                    chain_options.append(copy(move).set(chained_move=chained_move))  # account for change of board state
                self.board.undo(move)  # also let's not forget to undo the move before something unexpected could happen
                yield from chain_options  # yielding from cache might be a weird thing to do but it works and i'm tired.


class MultiMovement(BaseMultiMovement):
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
        super().__init__(board, self.move_or_capture + self.move + self.capture)

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        if theoretical:
            for movement in self.movements:
                for move in movement.moves(pos_from, piece, theoretical):
                    yield copy(move)
        else:
            for movement in self.move_or_capture + self.move:
                for move in movement.moves(pos_from, piece, theoretical):
                    to_piece = self.board.get_piece(move.pos_to)
                    if to_piece.is_empty() or piece == to_piece:
                        yield copy(move)
            for movement in self.move_or_capture + self.capture:
                for move in movement.moves(pos_from, piece, theoretical):
                    captured_piece = move.captured_piece or self.board.get_piece(move.pos_to)
                    if captured_piece.side == piece.side.opponent():
                        yield copy(move)

    def __copy_args__(self):
        return self.board, deepcopy(self.move_or_capture), deepcopy(self.move), deepcopy(self.capture)


class ColorMovement(BaseMultiMovement):
    def __init__(
            self,
            board: Board,
            light: list[BaseMovement] | None = None,
            dark: list[BaseMovement] | None = None
    ):
        self.light = light or []
        self.dark = dark or []
        super().__init__(board, self.light + self.dark)

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        if self.board.is_light_square(pos_from):
            for movement in self.light:
                for move in movement.moves(pos_from, piece, theoretical):
                    yield copy(move)
        if self.board.is_dark_square(pos_from):
            for movement in self.dark:
                for move in movement.moves(pos_from, piece, theoretical):
                    yield copy(move)


class ProbabilisticMovement(BaseMultiMovement):
    def __init__(self, board: Board, movements: list[BaseMovement]):
        super().__init__(board, movements)

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        movements = []
        if theoretical:
            movements = self.movements
        else:
            try:
                current_ply = self.board.ply_count + self.board.ply_simulation - 1
                current_roll = self.board.roll_history[current_ply][pos_from]
                movements = [self.movements[current_roll]]
            except IndexError:
                movements = self.movements
            except KeyError:
                pass
        for movement in movements:
            for move in movement.moves(pos_from, piece, theoretical):
                yield copy(move)

    def roll(self):
        return randrange(len(self.movements))
