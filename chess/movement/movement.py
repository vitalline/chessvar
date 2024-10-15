from __future__ import annotations

from copy import copy, deepcopy
from math import ceil, floor
from typing import TYPE_CHECKING

from chess.movement.move import Move
from chess.movement.util import AnyDirection, Direction, Position, add, sub, mul, ddiv
from chess.pieces.util import Immune
from chess.util import Unset

if TYPE_CHECKING:
    from chess.board import Board
    from chess.pieces.piece import Piece


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

    def set_moves(self, count: int):
        self.total_moves = count

    def __copy_args__(self):
        return self.board,

    def __copy__(self):
        clone = self.__class__(*self.__copy_args__())
        clone.total_moves = self.total_moves
        return clone

    def __deepcopy__(self, memo):
        return self.__copy__()


class BaseDirectionalMovement(BaseMovement):
    def __init__(self, board: Board, directions: list[AnyDirection] | None = None):
        super().__init__(board)
        self.directions = directions or []
        self.steps = 0

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
                yield Move(pos_from, self.transform(pos_from), type(self))
                direction_id += 1
                continue
            self.steps = 0  # note that calls to moves() will restart the step count from 0 once for each direction
            steps = 0  # because of this, we need to also store the step count for the current direction separately
            # we set self.steps to this value on update and after each yield to make sure the step count is correct
            self.initialize_direction(direction, pos_from, piece)
            current_pos = pos_from
            move = Move(pos_from, self.transform(current_pos), type(self))
            while self.board.on_board(self.transform(current_pos)):
                if self.stop_condition(move, direction, piece, theoretical):
                    direction_id += 1
                    break
                current_pos = add(current_pos, direction[:2])
                move = Move(pos_from, self.transform(current_pos), type(self))
                steps += 1
                self.steps = steps
                self.advance_direction(move, direction, pos_from, piece)
                if self.skip_condition(move, direction, piece, theoretical):
                    continue
                if not theoretical and move.pos_to in self.board.castling_ep_markers:
                    yield Move(move.pos_from, self.board.castling_ep_target.board_pos, RoyalEnPassantMovement)
                yield move
                self.steps = steps  # this is a hacky way to make sure the step count stays correct after the yield
                # this is because the step count will be reset to 0 if self.moves() is called before the next yield
            else:
                direction_id += 1

    def __copy_args__(self):
        return self.board, copy(self.directions)


class RiderMovement(BaseDirectionalMovement):
    def skip_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        if len(direction) < 4:
            return False
        if not direction[3]:
            return False
        if 0 < self.steps < direction[3]:
            return True
        return False

    def stop_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        next_pos_to = self.transform(add(move.pos_from, mul(direction[:2], self.steps + 1)))
        return (
            self.board.not_on_board(next_pos_to)
            or move.pos_from == next_pos_to
            or len(direction) > 2 and direction[2] and self.steps >= direction[2]
            or not theoretical and (
                (piece.blocked_by((next_piece := self.board.get_piece(next_pos_to))) and piece != next_piece)
                or (piece.captures(self.board.get_piece(move.pos_to)) and move.pos_from != move.pos_to)
            )
            or theoretical and (
                isinstance((next_piece := self.board.get_piece(next_pos_to)), Immune) and next_piece.movement is None
            )
        )


class HalflingRiderMovement(RiderMovement):
    def __init__(self, board: Board, directions: list[AnyDirection] | None = None, shift: int = 0):
        super().__init__(board, directions)
        self.shift = shift
        self.max_steps = 0

    def steps_to_edge(self, position: int, direction: int, size: int) -> int:
        if direction == 0:
            return size
        return (((size - position - 1) if direction > 0 else position) - self.shift) // abs(direction)

    def initialize_direction(self, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        board_size = self.board.board_height, self.board.board_width
        self.max_steps = min(ceil(self.steps_to_edge(pos_from[i], direction[i], board_size[i]) / 2) for i in range(2))

    def stop_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        return self.steps >= self.max_steps or super().stop_condition(move, direction, piece, theoretical)

    def __copy_args__(self):
        return self.board, copy(self.directions), self.shift


class CannonRiderMovement(RiderMovement):
    def __init__(self, board: Board, directions: list[AnyDirection] | None = None):
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
    def spacious_transform(self, pos: Position) -> Position:
        # return pos[0] % self.board.board_height, pos[1] % self.board.board_width
        return pos  # as much as i like the idea of a toroidal movement condition, it's just not practical for this game

    def skip_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        next_pos_to = self.transform(add(move.pos_to, direction[:2]))
        check_space = self.spacious_transform(next_pos_to)
        check_state = check_space == self.spacious_transform(move.pos_from) or self.board.not_a_piece(check_space)
        return not check_state or super().skip_condition(move, direction, piece, theoretical)


class TrueSpaciousRiderMovement(SpaciousRiderMovement):
    def spacious_transform(self, pos: Position) -> Position:
        return pos[0] % self.board.board_height, pos[1] % self.board.board_width


class ToroidalRiderMovement(RiderMovement):
    # Looping movement along both axes
    def transform(self, pos: Position) -> Position:
        return pos[0] % self.board.board_height, pos[1] % self.board.board_width


class FileCylindricalRiderMovement(RiderMovement):
    # Looping movement along the file (vertical) axis
    def transform(self, pos: Position) -> Position:
        return pos[0] % self.board.board_height, pos[1]


class RankCylindricalRiderMovement(RiderMovement):
    # Looping movement along the rank (horizontal) axis
    def transform(self, pos: Position) -> Position:
        return pos[0], pos[1] % self.board.board_width


class CylindricalRiderMovement(RankCylindricalRiderMovement):
    pass  # Alias for RankCylindricalRiderMovement because cylindrical movement usually refers to the ranks being looped


class BouncingRiderMovement(RiderMovement):
    # Reflective movement along both axes
    def transform(self, pos: Position) -> Position:
        bounds = self.board.board_height - 1, self.board.board_width - 1
        pos = [bounds[i] - abs(pos[i] % (bounds[i] * 2) - bounds[i]) for i in range(2)]
        return tuple(pos)  # noqa


class FileBouncingRiderMovement(BouncingRiderMovement):
    # Reflective movement along the file (vertical) axis
    def transform(self, pos: Position) -> Position:
        return super().transform(pos)[0], pos[1]


class RankBouncingRiderMovement(BouncingRiderMovement):
    # Reflective movement along the rank (horizontal) axis
    def transform(self, pos: Position) -> Position:
        return pos[0], super().transform(pos)[1]


class RangedCaptureRiderMovement(RiderMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            move.movement_type = RiderMovement
            if not theoretical:
                captured_piece = self.board.get_piece(move.pos_to)
                if not captured_piece.is_empty():
                    move.captured_piece = captured_piece
                    move.pos_to = move.pos_from
                    move.movement_type = type(self)
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


class RangedAutoCaptureRiderMovement(RiderMovement):
    # Note: This implementation assumes that the pieces that utilize it cannot be blocked by another piece mid-movement.
    # This is true for the only army that utilizes this movement type, but it may not work correctly in other scenarios.
    def generate_captures(self, move: Move, piece: Piece) -> Move:
        if not move.is_edit:
            captures = {}
            for capture in super().moves(move.pos_to, piece):
                captured_piece = self.board.get_piece(capture.pos_to)
                if piece.captures(captured_piece):
                    captures[capture.pos_to] = copy(capture)
                    captures[capture.pos_to].set(piece=piece, pos_to=move.pos_to, captured_piece=captured_piece)
            last_chain_move = move
            while last_chain_move.chained_move and not (issubclass(
                move.chained_move.movement_type,
                AutoRangedAutoCaptureRiderMovement
            ) and move.chained_move.piece.side == piece.side):
                last_chain_move = last_chain_move.chained_move
            for capture_pos_to in sorted(captures):
                last_chain_move.chained_move = captures[capture_pos_to]
                last_chain_move = last_chain_move.chained_move
        return move

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            move.movement_type = RiderMovement
            yield move if theoretical else self.generate_captures(move, piece)


class AutoRangedAutoCaptureRiderMovement(RangedAutoCaptureRiderMovement):
    # Note: Same as RangedAutoCaptureRiderMovement, this assumes that pieces that use it cannot be blocked mid-movement.
    def mark(self, pos: Position, piece: Piece):
        for move in self.moves(pos, piece, True):
            if move.pos_to not in self.board.auto_capture_markers[piece.side]:
                self.board.auto_capture_markers[piece.side][move.pos_to] = set()
            # noinspection PyTestUnpassedFixture
            self.board.auto_capture_markers[piece.side][move.pos_to].add(pos)

    def unmark(self, pos: Position, piece: Piece):
        for move in self.moves(pos, piece, True):
            if move.pos_to in self.board.auto_capture_markers[piece.side]:
                self.board.auto_capture_markers[piece.side][move.pos_to].discard(pos)
                if not self.board.auto_capture_markers[piece.side][move.pos_to]:
                    del self.board.auto_capture_markers[piece.side][move.pos_to]

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            move.movement_type = RiderMovement
            yield move

    def update(self, move: Move, piece: Piece):
        self.unmark(move.pos_from, piece)
        self.mark(move.pos_to, piece)
        super().update(move, piece)

    def undo(self, move: Move, piece: Piece):
        super().undo(move, piece)
        self.unmark(move.pos_to, piece)
        self.mark(move.pos_from, piece)


class DropMovement(BaseMovement):
    # used to mark piece drops (Move.movement_type == DropMovement)
    pass


class CastlingMovement(BaseMovement):
    def __init__(
        self,
        board: Board,
        direction: Direction,
        other_piece: Direction,
        other_direction: Direction,
        movement_gap: list[Direction] | None = None,
        en_passant_gap: list[Direction] | None = None
    ):
        super().__init__(board)
        self.direction = direction
        self.other_piece = other_piece
        self.other_direction = other_direction
        self.movement_gap = movement_gap or []
        self.en_passant_gap = en_passant_gap or []

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        if self.total_moves:
            return ()
        pos_to = add(pos_from, piece.side.direction(self.direction))
        if self.board.not_on_board(pos_to):
            return ()
        other_piece_pos = add(pos_from, piece.side.direction(self.other_piece))
        if self.board.not_on_board(other_piece_pos):
            return ()
        other_piece_pos_to = add(other_piece_pos, piece.side.direction(self.other_direction))
        if self.board.not_on_board(other_piece_pos_to):
            return ()
        other_piece = self.board.get_piece(other_piece_pos)
        if other_piece.is_empty():
            return ()
        if other_piece.side != piece.side:
            return ()
        if other_piece.movement.total_moves:
            return ()
        if not theoretical:
            for gap_offset in self.movement_gap:
                pos = add(pos_from, gap_offset)
                if not self.board.not_a_piece(pos):
                    return ()
        self_move = Move(pos_from, pos_to, type(self))
        other_move = Move(other_piece_pos, other_piece_pos_to, type(self), other_piece)
        return self_move.set(chained_move=other_move),

    def update(self, move: Move, piece: Piece):
        direction = piece.side.direction(self.direction)
        offset = sub(move.pos_to, move.pos_from)
        if offset == direction:
            for gap_offset in self.en_passant_gap:
                pos = add(move.pos_from, gap_offset)
                self.board.mark_castling_ep(move.pos_to, pos)
        super().update(move, piece)

    def undo(self, move: Move, piece: Piece):
        super().undo(move, piece)
        self.board.clear_castling_ep()

    def __copy_args__(self):
        return (
            self.board, self.direction, self.other_piece, self.other_direction,
            copy(self.movement_gap), copy(self.en_passant_gap)
        )


class RoyalEnPassantMovement(BaseMovement):
    # used to mark en passant captures of royals that moved through check (Move.movement_type == RoyalEnPassantMovement)
    pass


class EnPassantTargetRiderMovement(RiderMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            move.movement_type = type(self) if self.steps > 1 else RiderMovement
            yield move

    def update(self, move: Move, piece: Piece):
        if move.movement_type == type(self):
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
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            move.movement_type = RiderMovement
            if not theoretical:
                if move.pos_to in self.board.en_passant_markers:
                    move.captured_piece = self.board.en_passant_target
                    move.movement_type = type(self)
            yield move


class BaseMultiMovement(BaseMovement):
    def __init__(self, board: Board, movements: list[BaseMovement] | None = None):
        super().__init__(board)
        self.movements = movements or []
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

    def set_moves(self, count: int):
        for movement in self.movements:
            movement.set_moves(count)
        super().set_moves(count)

    def __copy_args__(self):
        return self.board, deepcopy(self.movements)


class FirstMoveMovement(BaseMultiMovement):
    def __init__(
        self,
        board: Board,
        base_movements: list[BaseMovement] | None = None,
        first_move_movements: list[BaseMovement] | None = None
    ):
        self.base_movements = base_movements or []
        self.first_move_movements = first_move_movements or []
        super().__init__(board, self.base_movements + self.first_move_movements)

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        movements = self.movements if not self.total_moves else self.base_movements
        for movement in movements:
            for move in movement.moves(pos_from, piece, theoretical):
                yield copy(move)

    def __copy_args__(self):
        return self.board, copy(self.base_movements), copy(self.first_move_movements)


class BentMovement(BaseMultiMovement):
    def __init__(self, board: Board, movements: list[BaseDirectionalMovement] | None = None, start_index: int = 0):
        super().__init__(board, movements)
        self.start_index = start_index

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False, index: int = 0):
        if index >= len(self.movements):
            return ()
        movement = copy(self.movements[index])  # copy movement because changing it inside the loop completely breaks it
        if isinstance(movement, BaseDirectionalMovement):
            directions = movement.directions
            for direction in directions:
                movement.directions = [direction]
                move = None
                for move in movement.moves(pos_from, piece, theoretical):
                    move.movement_type = type(self)
                    if self.start_index <= index:
                        yield copy(move)
                if (
                    move is not None and len(direction) > 2 and direction[2] and
                    move.pos_to == add(pos_from, piece.side.direction(mul(direction[:2], direction[2])))
                    and (theoretical or self.board.get_piece(move.pos_to).is_empty())
                ):
                    for bent_move in self.moves(move.pos_to, piece, theoretical, index + 1):
                        yield copy(bent_move).set(pos_from=pos_from)
        else:
            return ()

    def __copy_args__(self):
        return self.board, deepcopy(self.movements), self.start_index


class RepeatMovement(BentMovement):
    def __init__(
        self,
        board: Board,
        movements: list[BaseDirectionalMovement] | None = None,
        start_index: int = 0,
        count: int = 0
    ):
        super().__init__(board, movements, start_index)
        self.count = count
        self.loops = 0

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False, index: int = 0):
        if index == 0:
            self.loops = 0
        if index >= len(self.movements):
            self.loops += 1
        index %= len(self.movements)
        if self.count and self.count <= index + self.loops * len(self.movements):
            return ()
        yield from super().moves(pos_from, piece, theoretical, index)

    def __copy_args__(self):
        return self.board, deepcopy(self.movements), self.start_index, self.count


class ChainMovement(BaseMultiMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False, index: int = 0):
        if index >= len(self.movements):
            return ()
        if index == len(self.movements) - 1:
            for move in self.movements[index].moves(pos_from, piece, theoretical):
                self.board.update_move(move)
                yield move
            return ()
        if theoretical:
            for move in self.movements[index].moves(pos_from, piece, theoretical):
                yield copy(move)
                for chained_move in self.moves(move.pos_to, piece, theoretical, index + 1):
                    yield copy(chained_move).set(pos_from=move.pos_from)
        else:
            for move in self.movements[index].moves(pos_from, piece, theoretical):
                if move.movement_type == RoyalEnPassantMovement:
                    yield move
                    continue
                move_chain = []
                chained_move = move
                while chained_move:
                    move_chain.append(copy(chained_move).set(chained_move=Unset))
                    chained_move = chained_move.chained_move
                for chained_move in move_chain:
                    self.board.update_move(chained_move)
                    self.board.move(chained_move)
                chain_options = []
                for last_chained_move in self.moves(move.pos_to, piece, theoretical, index + 1):
                    copy_move = copy(move_chain[0])
                    chained_copy = copy_move
                    for chained_move in move_chain[1:]:
                        chained_copy = chained_copy.set(chained_move=copy(chained_move)).chained_move
                    chained_copy.set(chained_move=copy(last_chained_move))
                    chain_options.append(copy_move)
                for chained_move in move_chain[::-1]:
                    self.board.undo(chained_move)
                yield from chain_options


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
                    if piece.captures(captured_piece):
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
                    move.movement_type = type(self)
                    yield copy(move)
        if self.board.is_dark_square(pos_from):
            for movement in self.dark:
                for move in movement.moves(pos_from, piece, theoretical):
                    move.movement_type = type(self)
                    yield copy(move)

    def __copy_args__(self):
        return self.board, deepcopy(self.light), deepcopy(self.dark)


class SideMovement(BaseMultiMovement):
    def __init__(
        self,
        board: Board,
        left: list[BaseMovement] | None = None,
        right: list[BaseMovement] | None = None,
        bottom: list[BaseMovement] | None = None,
        top: list[BaseMovement] | None = None
    ):
        self.left = left or []
        self.right = right or []
        self.bottom = bottom or []
        self.top = top or []
        super().__init__(board, self.left + self.right)

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        if pos_from[1] < ceil(self.board.board_width / 2):
            for movement in self.left:
                for move in movement.moves(pos_from, piece, theoretical):
                    move.movement_type = type(self)
                    yield copy(move)
        if pos_from[1] >= floor(self.board.board_width / 2):
            for movement in self.right:
                for move in movement.moves(pos_from, piece, theoretical):
                    move.movement_type = type(self)
                    yield copy(move)
        if pos_from[0] < ceil(self.board.board_height / 2):
            for movement in self.bottom:
                for move in movement.moves(pos_from, piece, theoretical):
                    move.movement_type = type(self)
                    yield copy(move)
        if pos_from[0] >= floor(self.board.board_height / 2):
            for movement in self.top:
                for move in movement.moves(pos_from, piece, theoretical):
                    move.movement_type = type(self)
                    yield copy(move)

    def __copy_args__(self):
        return self.board, deepcopy(self.left), deepcopy(self.right)


class ProbabilisticMovement(BaseMultiMovement):
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
                movements = self.movements
        for movement in movements:
            for move in movement.moves(pos_from, piece, theoretical):
                yield copy(move)

    def roll(self):
        return self.board.roll_rng.randrange(len(self.movements))
