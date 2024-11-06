from __future__ import annotations

from copy import copy
from math import ceil, floor
from typing import TYPE_CHECKING

from chess.movement.base import BaseMovement
from chess.movement.move import Move
from chess.movement.util import AnyDirection, Direction, Position, add, sub, mul, ddiv
from chess.pieces.types import Immune, Slow, Delayed, Delayed1
from chess.util import UnpackedList, Unset, sign, repack, unpack

if TYPE_CHECKING:
    from chess.board import Board
    from chess.pieces.piece import Piece


class RiderMovement(BaseMovement):
    default_mark = 'n'

    def __init__(
        self, board: Board,
        directions: UnpackedList[AnyDirection] | None = None,
        boundless: int = 0, loop: int = 0
    ):
        super().__init__(board)
        self.directions = repack(directions or [])
        self.boundless = boundless
        self.loop = loop
        self.data = {}
        self.steps = 0
        self.bounds = []

    def initialize_direction(self, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        pass

    def advance_direction(self, move: Move, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        pass

    def transform(self, pos: Position) -> Position:
        return pos

    def in_bounds(self, pos: Position) -> bool:
        return all(self.bounds[i][0] <= pos[i] < self.bounds[i][1] for i in range(2))

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        if self.board.not_on_board(pos_from):
            return ()
        board_size = self.board.board_height, self.board.board_width
        if self.boundless:
            self.bounds = [[0, board_size[i]] for i in range(2)]
        else:
            bounds = [self.board.border_rows, self.board.border_cols]
            bounds = [[0] + bounds[i] + [board_size[i]] for i in range(2)]
            self.bounds = [
                [
                    max(x for x in bounds[i] if x <= pos_from[i]),
                    min(x for x in bounds[i] if x > pos_from[i])
                ] for i in range(2)
            ]
        bounds = self.bounds
        direction_id = 0
        while direction_id < len(self.directions):
            direction = piece.side.direction(self.directions[direction_id])
            if direction[:2] == (0, 0):
                yield Move(
                    pos_from=pos_from, pos_to=self.transform(pos_from), movement_type=type(self)
                ).mark(self.default_mark)
                direction_id += 1
                continue
            self.steps = 0  # note that calls to moves() will restart the step count from 0 once for each direction
            steps = 0  # because of this, we need to also store the step count for the current direction separately
            # we set self.steps to this value on update and after each yield to make sure the step count is correct
            self.data = {}  # we also do the same to self.data - note that it will be updated by init/advance calls
            self.bounds = bounds  # and, just to make sure, we also restore the boundaries to their original values
            self.initialize_direction(direction, pos_from, piece)
            data = self.data.copy()
            current_pos = pos_from
            move = Move(
                pos_from=pos_from, pos_to=self.transform(current_pos), movement_type=type(self)
            ).mark(self.default_mark)
            while self.in_bounds(self.transform(current_pos)):
                if self.stop_condition(move, direction, piece, theoretical):
                    direction_id += 1
                    break
                current_pos = add(current_pos, direction[:2])
                move = Move(
                    pos_from=pos_from, pos_to=self.transform(current_pos), movement_type=type(self)
                ).mark(self.default_mark)
                steps += 1
                self.data = data
                self.steps = steps
                self.bounds = bounds
                self.advance_direction(move, direction, pos_from, piece)
                data = self.data.copy()
                if self.skip_condition(move, direction, piece, theoretical):
                    continue
                if not theoretical:
                    royal_ep_markers = self.board.royal_ep_markers.get(piece.side.opponent(), {})
                    if move.pos_to in royal_ep_markers:
                        for chained_move in (
                            Move(
                                pos_from=move.pos_to, pos_to=royal_ep_markers[move.pos_to],
                                movement_type=RoyalEnPassantMovement, piece=piece,
                                captured_piece=self.board.get_piece(royal_ep_markers[move.pos_to]),
                            ).mark(self.default_mark),
                            Move(
                                pos_from=move.pos_to, pos_to=move.pos_to,
                                movement_type=move.movement_type, piece=piece,
                            ).mark(self.default_mark),
                        ):
                            yield copy(move).set(chained_move=chained_move)
                    else:
                        yield move
                else:
                    yield move
                self.steps = steps  # this is a hacky way to make sure the step count stays correct after the yield
                # this is because the step count will be reset to 0 if self.moves() is called before the next yield
                self.data = data  # same thing for self.data, because it's also updated by successive moves() calls
                self.bounds = bounds  # and same for self.bounds... notice the pattern yet? good. now don't forget.
            else:
                direction_id += 1

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
            not self.in_bounds(next_pos_to)
            or ((move.pos_from == move.pos_to and self.steps) if self.loop else (move.pos_from == next_pos_to))
            or len(direction) > 2 and direction[2] and self.steps >= direction[2]
            or ((
                isinstance((next_piece := self.board.get_piece(next_pos_to)), Immune)
                and not piece.skips(next_piece) and next_piece.movement is None
            ) if theoretical else (
                (piece.blocked_by(next_piece := self.board.get_piece(next_pos_to))
                and not piece.skips(next_piece)) or (move.pos_from != move.pos_to and (
                piece != (captured_piece := self.board.get_piece(move.pos_to))
                and piece.captures(captured_piece) and not piece.skips(captured_piece)))
                # the "move.pos_from != move.pos_to" check for the captured piece is necessary for Inverse and Relay, as
                # without it, the hypothetical "opposing piece" used to simulate the movement would try to capture ours!
            ))
        )

    def __copy_args__(self):
        return self.board, unpack(self.directions), self.boundless, self.loop


class HalflingRiderMovement(RiderMovement):
    default_mark = 'h'

    def __init__(
        self, board: Board,
        directions: UnpackedList[AnyDirection] | None = None,
        shift: int = 0, boundless: int = 0, loop: int = 0
    ):
        super().__init__(board, directions, boundless, loop)
        self.shift = shift

    def steps_to_edge(self, position: int, direction: int, start: int, stop: int) -> int:
        if direction == 0:
            return stop - start
        return (((stop - 1 - position) if direction > 0 else position - start) - self.shift) // abs(direction)

    def initialize_direction(self, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        self.data['max_steps'] = min(
            ceil(self.steps_to_edge(pos_from[i], direction[i], *self.bounds[i]) / 2) for i in range(2)
        )

    def stop_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        return self.steps >= self.data['max_steps'] or super().stop_condition(move, direction, piece, theoretical)

    def __copy_args__(self):
        return self.board, unpack(self.directions), self.shift, self.boundless, self.loop


class CannonRiderMovement(RiderMovement):
    default_mark = 'p'

    def __init__(
        self, board: Board,
        directions: UnpackedList[AnyDirection] | None = None,
        distance: int = 0, boundless: int = 0, loop: int = 0
    ):
        super().__init__(board, directions, boundless, loop)
        self.distance = distance

    def initialize_direction(self, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        self.data['jump'] = -1

    def advance_direction(self, move: Move, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        if self.data['jump'] < 0:
            if not self.board.not_a_piece(self.transform(move.pos_to)):
                self.data['jump'] = 0
        else:
            self.data['jump'] += 1

    def skip_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        return super().skip_condition(move, direction, piece, theoretical) if self.data['jump'] > 0 else not theoretical

    def stop_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        if self.data['jump'] < 0:
            next_pos_to = self.transform(add(move.pos_from, mul(direction[:2], self.steps + 1)))
            if not (self.loop and move.pos_from == next_pos_to) and piece.blocked_by(self.board.get_piece(next_pos_to)):
                return False
        elif self.data['jump'] == 0 and not theoretical:
            next_pos_to = self.transform(add(move.pos_from, mul(direction[:2], self.steps + 1)))
            if not (self.loop and move.pos_from == next_pos_to) and piece.blocked_by(self.board.get_piece(next_pos_to)):
                return True
        elif self.distance and self.data['jump'] >= self.distance:
            return True
        return super().stop_condition(move, direction, piece, theoretical or not self.data['jump'] > 0)

    def __copy_args__(self):
        return self.board, unpack(self.directions), self.distance, self.boundless, self.loop


class HopperRiderMovement(CannonRiderMovement):
    default_mark = 'l'

    def initialize_direction(self, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        super().initialize_direction(direction, pos_from, piece)
        self.data['capture'] = None

    def advance_direction(self, move: Move, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        super().advance_direction(move, direction, pos_from, piece)
        if self.data['jumped'] == 0:
            capture = self.board.get_piece(move.pos_to)
            if piece.captures(capture):
                self.data['capture'] = capture

    def stop_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        if self.data['jumped'] >= 0 and not theoretical:
            next_pos_to = self.transform(add(move.pos_from, mul(direction[:2], self.steps + 1)))
            if not (self.loop and move.pos_from == next_pos_to) and not self.board.not_a_piece(next_pos_to):
                return True
        return super().stop_condition(move, direction, piece, theoretical)

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            if not theoretical and self.data['capture']:
                move.captured_piece = self.data['capture']
            yield move


class SpaciousRiderMovement(RiderMovement):
    default_mark = 's'

    def spacious_transform(self, pos: Position) -> Position:
        return pos  # as much as i like the idea of a toroidal movement condition, it's just not practical for this game
        # but if you want to use the "canon" rules for spacious movement, you can use TrueSpaciousRiderMovement instead.

    def skip_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        if theoretical:
            return super().skip_condition(move, direction, piece, theoretical)
        next_pos_to = self.transform(add(move.pos_from, mul(direction[:2], self.steps + 1)))
        check_space = self.spacious_transform(next_pos_to)
        check_state = check_space == self.spacious_transform(move.pos_from) or self.board.not_a_piece(check_space)
        return not check_state or super().skip_condition(move, direction, piece, theoretical)


class TrueSpaciousRiderMovement(SpaciousRiderMovement):
    def spacious_transform(self, pos: Position) -> Position:
        new_pos = (
            (pos[i] - self.bounds[i][0]) % (self.bounds[i][1] - self.bounds[i][0]) + self.bounds[i][0] for i in range(2)
        )
        return tuple(new_pos)  # type: ignore


class BaseLoopMovement(BaseMovement):
    default_mark = 'o'


class ToroidalRiderMovement(BaseLoopMovement, RiderMovement):
    # Looping movement along both axes
    def transform(self, pos: Position) -> Position:
        new_pos = (
            (pos[i] - self.bounds[i][0]) % (self.bounds[i][1] - self.bounds[i][0]) + self.bounds[i][0] for i in range(2)
        )
        return tuple(new_pos)  # type: ignore


class FileCylindricalRiderMovement(BaseLoopMovement, RiderMovement):
    # Looping movement along the file (vertical) axis
    def transform(self, pos: Position) -> Position:
        return (pos[0] - self.bounds[0][0]) % (self.bounds[0][1] - self.bounds[0][0]) + self.bounds[0][0], pos[1]


class RankCylindricalRiderMovement(BaseLoopMovement, RiderMovement):
    # Looping movement along the rank (horizontal) axis
    def transform(self, pos: Position) -> Position:
        return pos[0], (pos[1] - self.bounds[1][0]) % (self.bounds[1][1] - self.bounds[1][0]) + self.bounds[1][0]


class CylindricalRiderMovement(RankCylindricalRiderMovement):
    pass  # Alias for RankCylindricalRiderMovement because cylindrical movement usually refers to the ranks being looped


class ReflectiveRiderMovement(RiderMovement):
    default_mark = 'k'
    # Reflective movement along both axes
    def transform(self, pos: Position) -> Position:
        size = [self.bounds[i][1] - self.bounds[i][0] - 1 for i in range(2)]
        new_pos = (
            size[i] - abs((pos[i] - self.bounds[i][0]) % (size[i] * 2) - size[i]) + self.bounds[i][0] for i in range(2)
        )
        return tuple(new_pos)  # type: ignore


class FileReflectiveRiderMovement(ReflectiveRiderMovement):
    # Reflective movement along the file (vertical) axis
    def transform(self, pos: Position) -> Position:
        return super().transform(pos)[0], pos[1]


class RankReflectiveRiderMovement(ReflectiveRiderMovement):
    # Reflective movement along the rank (horizontal) axis
    def transform(self, pos: Position) -> Position:
        return pos[0], super().transform(pos)[1]


class RangedMovement(BaseMovement):
    default_mark = 'g'

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            move = copy(move)
            if not theoretical:
                captured_piece = move.captured_piece or self.board.get_piece(move.pos_to)
                if captured_piece.side:
                    move.captured_piece = captured_piece
                    move.pos_to = move.pos_from
                    move.movement_type = RangedMovement
            yield move


class RangedCaptureRiderMovement(RangedMovement, RiderMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            if not move.captured_piece:
                move.movement_type = RiderMovement
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


class AutoCaptureMovement(BaseMovement):
    default_mark = 't'

    # Note: The auto-capture implementation assumes that none of the pieces that utilize it can be blocked mid-movement.
    # This is true for the only army that utilizes this movement type, but it may not work correctly in other scenarios.
    def generate_captures(self, move: Move, piece: Piece) -> Move:
        if not move.is_edit:
            captures = {}
            for capture in super().moves(move.pos_to, piece):
                captured_piece = self.board.get_piece(capture.pos_to)
                if piece.captures(captured_piece):
                    captures[capture.pos_to] = copy(capture).set(
                        piece=piece, pos_to=move.pos_to,
                        captured_piece=captured_piece,
                        movement_type=AutoCaptureMovement
                    )
            last_chain_move = move
            while last_chain_move.chained_move:
                last_chain_move = last_chain_move.chained_move
            for capture_pos_to in sorted(captures):
                last_chain_move.chained_move = captures[capture_pos_to]
                last_chain_move = last_chain_move.chained_move
        return move


class RangedAutoCaptureRiderMovement(AutoCaptureMovement, RiderMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            move.movement_type = RiderMovement
            yield move if theoretical else self.generate_captures(move, piece)


class AutoRangedAutoCaptureRiderMovement(RangedAutoCaptureRiderMovement, RiderMovement):
    def mark(self, pos: Position, piece: Piece):
        for move in self.moves(pos, piece, True):
            if move.pos_to not in self.board.auto_capture_markers[piece.side]:
                self.board.auto_capture_markers[piece.side][move.pos_to] = set()
            self.board.auto_capture_markers[piece.side][move.pos_to].add(pos)

    def unmark(self, pos: Position, piece: Piece):
        for move in self.moves(pos, piece, True):
            if move.pos_to in self.board.auto_capture_markers[piece.side]:
                self.board.auto_capture_markers[piece.side][move.pos_to].discard(pos)
                if not self.board.auto_capture_markers[piece.side][move.pos_to]:
                    del self.board.auto_capture_markers[piece.side][move.pos_to]

    def update(self, move: Move, piece: Piece):
        self.unmark(move.pos_from, piece)
        self.mark(move.pos_to, piece)
        super().update(move, piece)

    def undo(self, move: Move, piece: Piece):
        super().undo(move, piece)
        self.unmark(move.pos_to, piece)
        self.mark(move.pos_from, piece)


class DropMovement(BaseMovement):
    # Used to mark piece drops
    pass


class CastlingMovement(BaseMovement):
    def __init__(
        self,
        board: Board,
        direction: Direction,
        other_piece: Direction,
        other_direction: Direction,
        movement_gap: UnpackedList[Direction] | None = None,
        en_passant_gap: UnpackedList[Direction] | None = None,
    ):
        super().__init__(board)
        self.direction = direction
        self.other_piece = other_piece
        self.other_direction = other_direction
        self.movement_gap = repack(movement_gap or [])
        self.en_passant_gap = repack(en_passant_gap or [])

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
        if other_piece.side != piece.side:
            return ()
        if other_piece.movement.total_moves:
            return ()
        if not theoretical:
            for gap_offset in self.movement_gap:
                pos = add(pos_from, gap_offset)
                if not self.board.not_a_piece(pos):
                    return ()
        self_move = Move(pos_from=pos_from, pos_to=pos_to, movement_type=type(self)).mark('0')
        other_move = Move(
            pos_from=other_piece_pos, pos_to=other_piece_pos_to,
            movement_type=CastlingPartnerMovement, piece=other_piece
        ).mark('c0')  # marking the chained move too, just in case
        return self_move.set(chained_move=other_move),

    def update(self, move: Move, piece: Piece):
        if move.movement_type == type(self):
            direction = piece.side.direction(self.direction)
            offset = sub(move.pos_to, move.pos_from)
            if offset == direction:
                positions = []
                for gap_offset in self.en_passant_gap:
                    positions.append(add(move.pos_from, gap_offset))
                if positions:
                    marker_set = set(positions)
                    if isinstance(piece, Delayed):
                        marker_set.add(Delayed)
                    elif isinstance(piece, Delayed1):
                        marker_set.add(Delayed1)
                    if isinstance(piece, Slow):
                        marker_set.add(Slow)
                    marker_set.add('skip')
                    self.board.royal_ep_targets.get(piece.side, {})[move.pos_to] = marker_set
                    for pos in positions:
                        self.board.royal_ep_markers.get(piece.side, {})[pos] = move.pos_to
        super().update(move, piece)

    def __copy_args__(self):
        return (
            self.board, self.direction, self.other_piece, self.other_direction,
            unpack(self.movement_gap), unpack(self.en_passant_gap)
        )


class CastlingPartnerMovement(BaseMovement):
    # Used to mark the second part of a CastlingMovement move chain
    pass


class RoyalEnPassantMovement(BaseMovement):
    # Used to mark en passant captures of royals that moved through check
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
                if positions:
                    marker_set = set(positions)
                    if isinstance(piece, Delayed):
                        marker_set.add(Delayed)
                    elif isinstance(piece, Delayed1):
                        marker_set.add(Delayed1)
                    if isinstance(piece, Slow):
                        marker_set.add(Slow)
                    self.board.en_passant_targets.get(piece.side, {})[move.pos_to] = marker_set
                    for pos in positions:
                        self.board.en_passant_markers.get(piece.side, {})[pos] = move.pos_to
        super().update(move, piece)


class EnPassantRiderMovement(RiderMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            move.movement_type = RiderMovement
            if not theoretical:
                marker_dict = self.board.en_passant_markers.get(piece.side.opponent(), {})
                if not move.captured_piece and move.pos_to in marker_dict:
                    move.captured_piece = self.board.get_piece(marker_dict[move.pos_to])
                    move.movement_type = type(self)
            yield move


class BaseMultiMovement(BaseMovement):
    def __init__(self, board: Board, movements: UnpackedList[BaseMovement] | None = None):
        super().__init__(board)
        self.movements = repack(movements or [])
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
        return self.board, unpack(self.movements)


class IndexMovement(BaseMultiMovement):
    def __init__(
        self,
        board: Board,
        movement_index: tuple[UnpackedList[BaseMovement]] | None = None,
        iteration_type: int = 0,
        iteration_div: int = 0,
        iteration_sub: int = 0,
        cycle_mode: int = 0,
    ):
        self.movement_index = tuple(repack(movements or []) for movements in (movement_index or []))
        self.iteration_type = iteration_type
        self.iteration_div = iteration_div
        self.iteration_sub = iteration_sub
        self.cycle_mode = cycle_mode
        super().__init__(board, sum(self.movement_index, []))

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False, index: int | None = None):
        mark = '#'
        if index is None:
            index = self.total_moves
        index = max(0, index - self.iteration_sub) // (self.iteration_div or 1)
        if index >= len(self.movement_index):
            if self.cycle_mode > 0:
                index %= len(self.movement_index)
            elif self.cycle_mode < 0:
                index %= 2 * (len(self.movement_index) - 1)
                if index >= len(self.movement_index):
                    index = 2 * (len(self.movement_index) - 1) - index
            else:
                index = len(self.movement_index) - 1
                mark = ''
        movements = self.movements[slice(
            0 if self.iteration_type < 0 else index,
            0 if self.iteration_type > 0 else index + 1,
        )]
        for movement in movements:
            for move in movement.moves(pos_from, piece, theoretical):
                if mark:
                    yield copy(move).unmark('n').mark(mark)
                else:
                    yield copy(move)

    def __copy_args__(self):
        return (
            self.board, tuple(unpack(movements) for movements in self.movement_index),
            self.iteration_type, self.iteration_div, self.iteration_sub, self.cycle_mode
        )


class PlyMovement(IndexMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False, index: int | None = None):
        if index is None:
            index = self.board.ply_count
            count = self.board.get_turn()
            start_count = count
            while self.board.turn_order[count][0] != piece.side:
                index += 1
                count = self.board.get_turn(index, 0)
                if count == start_count:
                    return ()
            index -= 1
        yield from super().moves(pos_from, piece, theoretical, index)


class RepeatBentMovement(BaseMultiMovement):
    def __init__(
        self,
        board: Board,
        movements: UnpackedList[RiderMovement] | None = None,
        start_index: int = 0,
        step_count: int = 0,
        skip_count: int = 0,
        loop: int = 0,
        cycle_mode: int = 0,
        path_split: int = 0,
    ):
        super().__init__(board, movements)
        self.start_index = start_index
        self.step_count = step_count
        self.skip_count = skip_count
        self.loop = loop
        self.cycle_mode = cycle_mode
        self.path_split = path_split
        self.dir_indexes = [-1] * len(self.movements)

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False, index: int = 0):
        if index == 0:
            self.dir_indexes = [-1] * len(self.dir_indexes)
        if self.step_count and index >= self.step_count:
            return ()
        true_index = index
        if index >= len(self.dir_indexes):
            if self.cycle_mode > 0:
                index %= len(self.dir_indexes)
            elif self.cycle_mode < 0:
                index %= 2 * (len(self.dir_indexes) - 1)
                if index >= len(self.dir_indexes):
                    index = 2 * (len(self.dir_indexes) - 1) - index
            else:
                return ()
        movement = copy(self.movements[index])  # copy movement because changing it inside the loop will likely break it
        if isinstance(movement, RiderMovement):
            if self.path_split:
                self.dir_indexes[index] = -1
            is_new = self.dir_indexes[index] < 0
            directions = movement.directions if is_new else [movement.directions[self.dir_indexes[index]]]
            stop = False
            for direction in directions:
                if is_new:
                    for i in range(index + 1, len(self.dir_indexes)):
                        self.dir_indexes[i] = -1
                    self.dir_indexes[index] += 1
                movement.directions = [direction]
                move = None
                for move in movement.moves(pos_from, piece, theoretical):
                    if any(direction[:2]):
                        pos_to = move.pos_to
                        if issubclass(move.movement_type, RangedMovement) and move.captured_piece:
                            pos_to = move.captured_piece.board_pos
                        if pos_to == pos_from:
                            stop = True
                    move.movement_type = type(self)
                    if not stop or self.loop:
                        if self.start_index <= index and self.skip_count <= true_index:
                            yield copy(move)
                        else:
                            yield copy(move).set(is_legal=False).unmark('n').mark('a')
                    if stop:
                        break
                if (
                    not stop and move is not None and len(direction) > 2 and direction[2] and
                    move.pos_to == add(pos_from, piece.side.direction(mul(direction[:2], direction[2])))
                    and (theoretical or not self.board.get_piece(move.pos_to).side)
                ):
                    for bent_move in self.moves(move.pos_to, piece, theoretical, true_index + 1):
                        yield copy(bent_move).set(pos_from=pos_from)
        else:
            return ()

    def __copy_args__(self):
        return (
            self.board, unpack(self.movements),
            self.start_index, self.step_count, self.skip_count,
            self.loop, self.cycle_mode, self.path_split
        )


class RepeatMovement(RepeatBentMovement):
    def __init__(
        self,
        board: Board,
        movements: UnpackedList[RiderMovement] | None = None,
        start_index: int = 0,
        step_count: int = 0,
        skip_count: int = 0,
        loop: int = 0,
    ):
        super().__init__(
            board, movements,
            start_index=start_index,
            step_count=step_count,
            skip_count=skip_count,
            loop=loop,
            cycle_mode=1,
            path_split=0,
        )

    def __copy_args__(self):
        return self.board, unpack(self.movements), self.start_index, self.step_count, self.skip_count, self.loop


class BentMovement(RepeatBentMovement):
    def __init__(
        self,
        board: Board,
        movements: UnpackedList[RiderMovement] | None = None,
        start_index: int = 0,
        loop: int = 0,
    ):
        super().__init__(
            board, movements,
            start_index=start_index,
            step_count=len(repack(movements)) if movements else 0,
            loop=loop,
        )

    def __copy_args__(self):
        return self.board, unpack(self.movements), self.start_index, self.loop


class SpinMovement(RepeatBentMovement):
    def __init__(
        self,
        board: Board,
        movements: UnpackedList[RiderMovement] | None = None,
        reverse: int = 0,
        start_index: int = 0,
        step_count: int = 0,
        loop: int = 0,
    ):
        super().__init__(
            board, movements,
            start_index=start_index,
            step_count=step_count,
            loop=loop,
        )
        self.reverse = sign(reverse)
        self.movement_cycle = copy(self.movements)

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False, index: int = 0):
        if index == 0:
            for i in range(len(self.movement_cycle)):
                if self.reverse >= 0:
                    self.movements = (self.movement_cycle[i:] + self.movement_cycle[:i])[::+1]
                    yield from super().moves(pos_from, piece, theoretical, index)
                if self.reverse != 0:
                    self.movements = (self.movement_cycle[i:] + self.movement_cycle[:i])[::-1]
                    yield from super().moves(pos_from, piece, theoretical, index)
        else:
            yield from super().moves(pos_from, piece, theoretical, index)

    def __copy_args__(self):
        return self.board, unpack(self.movement_cycle), self.reverse, self.start_index, self.step_count, self.loop


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
                chained_move = move
                while chained_move.chained_move:
                    chained_move = chained_move.chained_move
                    yield copy(chained_move).set(pos_from=move.pos_from)
                last_chain_move = chained_move
                if last_chain_move.movement_type == RoyalEnPassantMovement:
                    continue
                for chained_move in self.moves(last_chain_move.pos_to, piece, theoretical, index + 1):
                    yield copy(chained_move).set(pos_from=move.pos_from).unmark('n').mark('+')
        else:
            for move in self.movements[index].moves(pos_from, piece, theoretical):
                move_chain = [move]
                while move_chain[-1].chained_move:
                    move_chain.append(move_chain[-1].chained_move)
                if move_chain[-1].movement_type == RoyalEnPassantMovement:
                    yield move
                    continue
                move_chain = [copy(chained_move).set(chained_move=Unset) for chained_move in move_chain]
                last_pos = move_chain[0].pos_from
                for chained_move in move_chain:
                    self.board.update_move(chained_move)
                    self.board.move(chained_move)
                    if last_pos == chained_move.pos_from:
                        last_pos = chained_move.pos_to
                chain_options = []
                for last_chained_move in self.moves(last_pos, piece, theoretical, index + 1):
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
        both: UnpackedList[BaseMovement] | None = None,
        move: UnpackedList[BaseMovement] | None = None,
        capture: UnpackedList[BaseMovement] | None = None
    ):
        self.both = repack(both or [])
        self.move = repack(move or [])
        self.capture = repack(capture or [])
        super().__init__(board, self.both + self.move + self.capture)

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        if theoretical:
            for movement in self.both:
                for move in movement.moves(pos_from, piece, theoretical):
                    yield copy(move)
            for movement in self.move:
                for move in movement.moves(pos_from, piece, theoretical):
                    yield copy(move).unmark('n').mark('m')
            for movement in self.capture:
                for move in movement.moves(pos_from, piece, theoretical):
                    yield copy(move).unmark('n').mark('c')
        else:
            for movement in self.both + self.move:
                for move in movement.moves(pos_from, piece, theoretical):
                    chained_move = move
                    while chained_move:
                        captured_piece = chained_move.captured_piece or self.board.get_piece(chained_move.pos_to)
                        if piece.captures(captured_piece) and piece != captured_piece:
                            break
                        chained_move = chained_move.chained_move
                    else:
                        yield copy(move)
            for movement in self.both + self.capture:
                for move in movement.moves(pos_from, piece, theoretical):
                    chained_move = move
                    while chained_move:
                        captured_piece = chained_move.captured_piece or self.board.get_piece(chained_move.pos_to)
                        if piece.captures(captured_piece):
                            yield copy(move)
                            break
                        chained_move = chained_move.chained_move

    def __copy_args__(self):
        return self.board, unpack(self.both), unpack(self.move), unpack(self.capture)


class RangedMultiMovement(RangedMovement, MultiMovement):
    pass


class InverseMovement(BaseMultiMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        inverse_piece = piece.of(piece.side.opponent())
        for movement in self.movements:
            for move in movement.moves(pos_from, inverse_piece, theoretical):
                move.piece = piece
                move.movement_type = type(self)
                if move.pos_from == move.pos_to:
                    move.pos_to = None
                yield move


class CloneMovement(BaseMultiMovement):
    def __init__(
        self,
        board: Board,
        movements: UnpackedList[BaseMovement] | None = None,
        move: int = 0,
        capture: int = 0
    ):
        super().__init__(board, movements)
        double = move and capture
        if double and (move > 0) is (capture > 0):
            move = capture = 0
        if not double and (move < 0 or capture < 0):
            move, capture = -capture, -move
        self.move = sign(max(move, 0))
        self.capture = sign(max(capture, 0))
        # invariant: (move, capture) in {(0, 0), (0, 1), (1, 0)}

    def add_clone(self, spawns: dict[Position, Piece], move: Move, piece: Piece, last_pos: Position) -> None:
        if move.pos_from and move.pos_from != move.pos_to:
            is_capture = move.captured_piece or not self.board.not_a_piece(move.pos_to)
            if not (self.move or self.capture) or (self.capture if is_capture else self.move):
                move_piece = piece if move.pos_from == last_pos else (
                    move.promotion or move.piece
                    or self.board.get_piece(move.pos_from)
                )
                spawns[move.pos_from] = move_piece

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for movement in self.movements:
            for move in movement.moves(pos_from, piece, theoretical):
                if not move:
                    continue
                spawns = {}
                chained_move = move
                last_pos = pos_from
                while chained_move.chained_move:
                    self.add_clone(spawns, chained_move, piece, last_pos)
                    if last_pos == chained_move.pos_from:
                        last_pos = chained_move.pos_to
                    chained_move = chained_move.chained_move
                self.add_clone(spawns, chained_move, piece, last_pos)
                if not spawns:
                    yield move
                    continue
                for spawn_point, spawn_piece in spawns.items():
                    chained_move = chained_move.set(chained_move=Move(
                        pos_from=None, pos_to=spawn_point,
                        promotion=copy(spawn_piece),
                        movement_type=type(self),
                    )).unmark('n').mark('8').chained_move
                yield move

    def __copy_args__(self):
        return self.board, unpack(self.movements), self.move, self.capture


class ColorMovement(BaseMultiMovement):
    def __init__(
        self,
        board: Board,
        light: UnpackedList[BaseMovement] | None = None,
        dark: UnpackedList[BaseMovement] | None = None
    ):
        self.light = repack(light or [])
        self.dark = repack(dark or [])
        super().__init__(board, self.light + self.dark)

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        if (legal := self.board.is_light_square(pos_from)) or theoretical:
            for movement in self.light:
                for move in movement.moves(pos_from, piece, theoretical):
                    move.movement_type = type(self)
                    yield copy(move).set(is_legal=legal).unmark('n').mark('w')
        if (legal := self.board.is_dark_square(pos_from)) or theoretical:
            for movement in self.dark:
                for move in movement.moves(pos_from, piece, theoretical):
                    move.movement_type = type(self)
                    yield copy(move).set(is_legal=legal).unmark('n').mark('b')

    def __copy_args__(self):
        return self.board, unpack(self.light), unpack(self.dark)


class SideMovement(BaseMultiMovement):
    def __init__(
        self,
        board: Board,
        left: UnpackedList[BaseMovement] | None = None,
        right: UnpackedList[BaseMovement] | None = None,
        bottom: UnpackedList[BaseMovement] | None = None,
        top: UnpackedList[BaseMovement] | None = None
    ):
        self.left = repack(left or [])
        self.right = repack(right or [])
        self.bottom = repack(bottom or [])
        self.top = repack(top or [])
        super().__init__(board, self.left + self.right)

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        if (legal := pos_from[1] < ceil(self.board.board_width / 2)) or theoretical:
            for movement in self.left:
                for move in movement.moves(pos_from, piece, theoretical):
                    move.movement_type = type(self)
                    yield copy(move).set(is_legal=legal).unmark('n').mark('[')
        if (legal := pos_from[1] >= floor(self.board.board_width / 2)) or theoretical:
            for movement in self.right:
                for move in movement.moves(pos_from, piece, theoretical):
                    move.movement_type = type(self)
                    yield copy(move).set(is_legal=legal).unmark('n').mark(']')
        position = pos_from[0] * piece.side.direction()
        if (legal := position < ceil(self.board.board_height / 2) * piece.side.direction()) or theoretical:
            for movement in self.bottom:
                for move in movement.moves(pos_from, piece, theoretical):
                    move.movement_type = type(self)
                    yield copy(move).set(is_legal=legal).unmark('n').mark('(')
        if (legal := position >= floor(self.board.board_height / 2) * piece.side.direction()) or theoretical:
            for movement in self.top:
                for move in movement.moves(pos_from, piece, theoretical):
                    move.movement_type = type(self)
                    yield copy(move).set(is_legal=legal).unmark('n').mark(')')

    def __copy_args__(self):
        return self.board, unpack(self.left), unpack(self.right), unpack(self.bottom), unpack(self.top)


class ProbabilisticMovement(BaseMultiMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        if theoretical:
            movements = self.movements
        else:
            try:
                current_ply = self.board.ply_count + self.board.ply_simulation - 1
                current_roll = self.board.roll_history[current_ply][pos_from]
                movements = [None if i != current_roll else self.movements[i] for i in range(len(self.movements))]
            except IndexError:
                movements = self.movements
            except KeyError:
                movements = self.movements
        for i, movement in enumerate(movements):
            if movement is None:
                continue
            for move in movement.moves(pos_from, piece, theoretical):
                yield copy(move).unmark('n').mark('7' * (i + 1) + '/' + '7' * len(movements))

    def roll(self):
        return self.board.roll_rng.randrange(len(self.movements))


class RandomMovement(ProbabilisticMovement):
    pass  # Alias for ProbabilisticMovement, for clarity and convenience


class BaseChoiceMovement(BaseMultiMovement):
    def __init__(self, board: Board, movements: dict[str, UnpackedList[BaseMovement]] | None = None):
        if movements is None:
            movements = {}
        self.movement_dict = {key: repack(value) for key, value in movements.items()}
        super().__init__(board, sum(self.movement_dict.values(), []))

    def __copy_args__(self):
        return self.board, {key: unpack(value) for key, value in self.movement_dict.items()}


class ChoiceMovement(BaseChoiceMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for key in self.movement_dict:
            value, invert = (key[1:], True) if key.startswith('!') else (key, False)
            for movement in self.movement_dict[key]:
                for move in movement.moves(pos_from, piece, theoretical):
                    if key == '*':
                        yield copy(move)
                    else:
                        legal = False
                        mark = 'i!' if invert else 'i'
                        to_piece = self.board.get_piece(move.pos_to)
                        if not value:
                            if (piece == to_piece or not to_piece.side) != invert:
                                legal = True
                        elif value.isdigit() and (int(value) == to_piece.side.value) != invert:
                            legal = True
                        elif self.board.fits(value, to_piece) != invert:
                            legal = True
                        yield copy(move).set(is_legal=legal).unmark('n').mark(mark)


class RelayMovement(BaseChoiceMovement):
    def __init__(
        self, board: Board,
        movements: dict[str, tuple[UnpackedList[BaseMovement], UnpackedList[BaseMovement]]] | None = None
    ):
        if movements is None:
            movements = {}
        movement_dict = {
            key: (repack(packed[0]), repack(packed[1]))
            if len(packed := value if isinstance(value, (list, tuple)) else [value]) > 1
            else (repack(packed[0]), repack(copy(packed[0])))
            for key, value in movements.items()
        }
        super().__init__(board, {key: sum(list(value), []) for key, value in movement_dict.items()})
        self.movement_dict = movement_dict

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        relay_piece_dict = self.board.relay_pieces.get(piece.side, {})
        relay_marker_dict = self.board.relay_markers.get(piece.side, {})
        relay_tester = piece.of(piece.side.opponent())
        for key in self.movement_dict:
            value, invert = (key[1:], True) if key.startswith('!') else (key, False)
            relays, movements = self.movement_dict[key]
            is_relayed = False
            if not key:
                mark = None
                is_relayed = True
            else:
                mark = 'r!' if invert else 'r'
                if key not in relay_piece_dict or pos_from not in relay_piece_dict[key]:
                    relay_piece_dict.setdefault(key, {})[pos_from] = set()
                    for relay in relays:
                        for move in relay.moves(pos_from, relay_tester, theoretical):
                            relay_piece_dict[key][pos_from].add(move.pos_to)
                            relay_marker_dict.setdefault(move.pos_to, set()).add((key, pos_from))
                if key in relay_piece_dict and pos_from in relay_piece_dict[key]:
                    for pos in relay_piece_dict[key][pos_from]:
                        relay_piece = self.board.get_piece(pos)
                        if value.isdigit() and (int(value) == relay_piece.side.value):
                            is_relayed = True
                        elif relay_piece.side == piece.side and self.board.fits(value, relay_piece):
                            is_relayed = True
                        if is_relayed:
                            break
            if not theoretical and is_relayed == invert:
                continue
            for movement in movements:
                for move in movement.moves(pos_from, piece, theoretical):
                    yield copy(move) if not mark else copy(move).set(is_legal=is_relayed).unmark('n').mark(mark)

    def __copy_args__(self):
        return self.board, {key: (unpack(value[0]), unpack(value[1])) for key, value in self.movement_dict.items()}


class AreaMovement(BaseChoiceMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for key in self.movement_dict:
            value, invert = (key[1:], True) if key.startswith('!') else (key, False)
            mark = 'e!' if invert else 'e'
            if (legal := self.board.in_area(value, pos_from, piece.side) != invert) or theoretical:
                for movement in self.movement_dict[key]:
                    for move in movement.moves(pos_from, piece, theoretical):
                        yield copy(move).set(is_legal=legal).unmark('n').mark(mark)


class BoundMovement(BaseChoiceMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for key in self.movement_dict:
            value, invert = (key[1:], True) if key.startswith('!') else (key, False)
            mark = 'd!' if invert else 'd'
            for movement in self.movement_dict[key]:
                for move in movement.moves(pos_from, piece, theoretical):
                    if (legal := self.board.in_area(value, move.pos_to, piece.side) != invert) or theoretical:
                        yield copy(move).set(is_legal=legal).unmark('n').mark(mark)


class TagMovement(BaseChoiceMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        if theoretical:
            for movement in self.movements:
                for move in movement.moves(pos_from, piece, theoretical):
                    yield copy(move)
        else:
            for key in self.movement_dict:
                for movement in self.movement_dict[key]:
                    for move in movement.moves(pos_from, piece, theoretical):
                        yield copy(move).set(tag=key or None)


# Movements that do not move the piece, instead interacting with the game in other, more mysterious ways. Intrigued yet?
passive_movements = (
    DropMovement,
    CloneMovement,
    RangedMovement,
    AutoCaptureMovement,
)

is_active = lambda move: (
    move and not move.is_edit and move.pos_from and move.pos_to and
    (move.pos_from != move.pos_to or move.movement_type and not issubclass(move.movement_type, passive_movements))
)
