from __future__ import annotations

from copy import copy
from itertools import chain
from math import ceil, floor
from typing import TYPE_CHECKING

from chess.movement.base import BaseMovement
from chess.movement.move import Move
from chess.movement.util import ANY, AnyDirection, Direction, Position
from chess.movement.util import add, sub, mul, ddiv, is_algebraic, from_algebraic_map
from chess.pieces.types import Immune, Slow, Delayed, Delayed1
from chess.util import Unpacked, Unset, sign, repack, unpack

if TYPE_CHECKING:
    from chess.board import Board
    from chess.pieces.piece import AbstractPiece as Piece


class RiderMovement(BaseMovement):
    default_mark = 'n'

    def __init__(
        self, board: Board,
        directions: Unpacked[AnyDirection] | None = None,
        boundless: int = 0, loop: int = 0
    ):
        super().__init__(board)
        self.directions = repack(directions or [], list)
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
        board_offset = self.board.notation_offset[1], self.board.notation_offset[0]
        board_bounds = [[x + board_offset[i] for x in (0, board_size[i])] for i in range(2)]
        if self.boundless:
            self.bounds = [board_bounds[i][:] for i in range(2)]
        else:
            bounds = [self.board.border_rows, self.board.border_cols]
            bounds = [[board_bounds[i][0]] + bounds[i] + [board_bounds[i][-1]] for i in range(2)]
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
                yield from self.chain(move, piece, theoretical)
                self.steps = steps  # this is a hacky way to make sure the step count stays correct after the yield
                # this is because the step count will be reset to 0 if self.moves() is called before the next yield
                self.data = data  # same thing for self.data, because it's also updated by successive moves() calls
                self.bounds = bounds  # and same for self.bounds... notice the pattern yet? good. now don't forget.
            else:
                direction_id += 1

    def chain(self, move: Move, piece: Piece, theoretical: bool = False):
        if not theoretical:
            royal_ep_markers = self.board.royal_ep_markers.get(piece.side.opponent(), {})
            if move.pos_to in royal_ep_markers:
                for chained_move in (
                    Move(
                        pos_from=move.pos_to, pos_to=royal_ep_markers[move.pos_to],
                        movement_type=RoyalEnPassantMovement, piece=piece,
                        captured=self.board.get_piece(royal_ep_markers[move.pos_to]),
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
                # the "move.pos_from != move.pos_to" check for the captured piece is necessary for InverseMovement since
                # without it, the hypothetical "opposing piece" used to simulate the movement would try to capture ours!
            ))
        )

    def __copy_args__(self):
        return self.board, unpack(self.directions), self.boundless, self.loop


class HalflingRiderMovement(RiderMovement):
    default_mark = 'h'

    def __init__(
        self, board: Board,
        directions: Unpacked[AnyDirection] | None = None,
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
        directions: Unpacked[AnyDirection] | None = None,
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
                move.set(captured=self.data['capture'])
            yield move


class ProximityRiderMovement(RiderMovement):
    default_mark = 'z'

    def __init__(
        self, board: Board,
        directions: Unpacked[AnyDirection] | None = None,
        distance: int = 0, boundless: int = 0, loop: int = 0
    ):
        super().__init__(board, directions, boundless, loop)
        self.distance = distance

    def initialize_direction(self, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        self.data['capture'] = None
        if self.distance < 0:
            capture_pos = self.transform(add(pos_from, mul(direction[:2], self.distance)))
            capture = self.board.get_piece(capture_pos)
            if piece.captures(capture):
                self.data['capture'] = capture

    def advance_direction(self, move: Move, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        if self.distance > 0:
            capture_pos = self.transform(add(move.pos_to, mul(direction[:2], self.distance)))
            capture = self.board.get_piece(capture_pos)
            if piece.captures(capture):
                self.data['capture'] = capture

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            if not theoretical and self.data['capture']:
                move.set(captured=self.data['capture'])
            yield move

    def __copy_args__(self):
        return self.board, unpack(self.directions), self.distance, self.boundless, self.loop


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
                captured_piece = self.board.get_piece(move.pos_to)
                if captured_piece.side:
                    move.set(
                        pos_to=pos_from,
                        captured=captured_piece,
                        movement_type=RangedMovement,
                    )
            yield move


class RangedCaptureRiderMovement(RangedMovement, RiderMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            if not move.captured:
                move.movement_type = RiderMovement
            yield move

    def skip_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        if move.captured:
            move.pos_to = self.transform(add(move.pos_from, mul(direction[:2], self.steps)))
            result = super().skip_condition(move, direction, piece, theoretical)
            move.pos_to = move.pos_from
            return result
        return super().skip_condition(move, direction, piece, theoretical)

    def stop_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        if move.captured:
            move.pos_to = self.transform(add(move.pos_from, mul(direction[:2], self.steps)))
            result = super().stop_condition(move, direction, piece, theoretical)
            move.pos_to = move.pos_from
            return result
        return super().stop_condition(move, direction, piece, theoretical)


class AutoCaptureMovement(BaseMovement):
    # NB: The auto-capture implementation assumes that all pieces that utilize it can never be blocked by another piece.
    # This is true for the only army that utilizes this movement type, but it may not work correctly in other scenarios.

    default_mark = 't'

    def generate_captures(self, move: Move, piece: Piece) -> Move:
        if not move.is_edit:
            for capture in super().moves(move.pos_to, piece):
                captured_piece = self.board.get_piece(capture.pos_to)
                if piece.captures(captured_piece):
                    move.set(
                        captured=captured_piece,
                        movement_type=AutoCaptureMovement
                    )
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
        movement_gap: Unpacked[Direction] | None = None,
        en_passant_gap: Unpacked[Direction] | None = None,
    ):
        super().__init__(board)
        self.direction = direction
        self.other_piece = other_piece
        self.other_direction = other_direction
        self.movement_gap = repack(movement_gap or [], list)
        self.en_passant_gap = repack(en_passant_gap or [], list)

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
        if issubclass(move.movement_type or type, type(self)):
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
                    marker_set.add(type(self))
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
        if issubclass(move.movement_type or type, type(self)):
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
                if move.pos_to in marker_dict:
                    move.set(
                        captured=self.board.get_piece(marker_dict[move.pos_to]),
                        movement_type=type(self),
                    )
                    move.mark('f')
            yield move


class AbsoluteMovement(RiderMovement):
    def __init__(self, board: Board, areas: Unpacked[str] | None = None, stay: int = 0):
        super().__init__(board)
        self.areas = repack(areas or [], list)
        self.stay = stay

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for pos_to in from_algebraic_map(
            self.areas, self.board.board_width, self.board.board_height,
            *self.board.notation_offset, self.board.areas.get(piece.side) or {}
        ):
            pos_to = self.transform(pos_to)
            if self.stay or pos_to != pos_from:
                to_piece = self.board.get_piece(pos_to)
                if piece.blocked_by(to_piece):
                    continue
                move = Move(pos_from=pos_from, pos_to=pos_to, movement_type=type(self)).mark(self.default_mark)
                yield from self.chain(move, piece, theoretical)

    def __copy_args__(self):
        return self.board, unpack(self.areas), self.stay


class FreeMovement(AbsoluteMovement):
    def __init__(self, board: Board, stay: int = 0):
        super().__init__(board, '*', stay)

    def __copy_args__(self):
        return self.board, self.stay


class ChangingMovement(BaseMovement):
    # ABC for movements that may change their behavior based on certain conditions. Does not return any moves by itself.
    # NB: Movement classes that return all theoretical moves, regardless of conditions, needn't inherit from this class.
    pass


class BaseMultiMovement(BaseMovement):
    def __init__(self, board: Board, movements: Unpacked[BaseMovement] | None = None):
        super().__init__(board)
        self.movements = repack(movements or [], list)
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


class IndexMovement(BaseMultiMovement, ChangingMovement):
    def __init__(
        self,
        board: Board,
        movement_index: tuple[Unpacked[BaseMovement]] | None = None,
        iteration_type: int = 0,
        iteration_div: int = 0,
        iteration_sub: int = 0,
        cycle_mode: int = 0,
    ):
        self.movement_index = tuple(repack(movements or [], list) for movements in (movement_index or []))
        self.iteration_type = iteration_type  # 0: [i:i+1], 1: [i:], -1: [:i+1]
        self.iteration_div = iteration_div    # d: shift i every d moves
        self.iteration_sub = iteration_sub    # s: do not shift i for the first s moves
        self.cycle_mode = cycle_mode          # 0: stop at the last i, 1: loop back to 0, -1: invert iteration direction
        super().__init__(board, list(chain.from_iterable(self.movement_index)))

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
        range_index = (
            0 if self.iteration_type < 0 else index,
            len(self.movements) if self.iteration_type > 0 else index + 1,
        )
        for i, movement in enumerate(self.movements):
            if self.cycle_mode == 0 and i == len(self.movements) - 1:
                mark = ''
            for move in movement.moves(pos_from, piece, theoretical):
                if range_index[0] <= i < range_index[1]:
                    if mark:
                        yield copy(move).unmark('n').mark(mark)
                    else:
                        yield copy(move)
                elif theoretical and (self.cycle_mode or mark and i >= range_index[1]):
                    yield copy(move).set(is_legal=False).unmark('n').mark(mark + '!')

    def __copy_args__(self):
        return (
            self.board, tuple(unpack(movements) for movements in self.movement_index),
            self.iteration_type, self.iteration_div, self.iteration_sub, self.cycle_mode
        )


class PlyMovement(IndexMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False, index: int | None = None):
        if index is None:
            index = self.board.ply_count
            count = self.board.get_turn_index()
            start_count = count
            while self.board.turn_order[count][0] != piece.side:
                index += 1
                count = self.board.get_turn_index(index, 0)
                if count == start_count:
                    return ()
            index -= 1
        yield from super().moves(pos_from, piece, theoretical, index)


class RepeatBentMovement(BaseMultiMovement):
    def __init__(
        self,
        board: Board,
        movements: Unpacked[RiderMovement] | None = None,
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
                        if issubclass(move.movement_type, RangedMovement) and move.captured:
                            pos_to = movement.transform(add(move.pos_from, mul(direction[:2], movement.steps)))
                        if pos_to == pos_from:
                            stop = True
                    move.movement_type = type(self)
                    if not stop or self.loop:
                        dir_indexes = self.dir_indexes[:]  # oh hey, remember when this very thing was in RiderMovement?
                        if self.start_index <= index and self.skip_count <= true_index:
                            yield copy(move)
                        else:
                            yield copy(move).set(is_legal=False).unmark('n').mark('a')
                        self.dir_indexes = dir_indexes  # yeah, that's still a thing.
                    if stop:
                        break
                if (
                    not stop and move is not None and len(direction) > 2 and direction[2] and
                    move.pos_to == add(pos_from, piece.side.direction(mul(direction[:2], direction[2])))
                    and (theoretical or not self.board.get_piece(move.pos_to).side)
                ):
                    for bent_move in self.moves(move.pos_to, piece, theoretical, true_index + 1):
                        dir_indexes = self.dir_indexes[:]  # i'm not even going to bother explaining this one
                        yield copy(bent_move).set(pos_from=pos_from, captured=move.captured + bent_move.captured)
                        self.dir_indexes = dir_indexes  # you can probably guess what this does by now, moving on
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
        movements: Unpacked[RiderMovement] | None = None,
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
        movements: Unpacked[RiderMovement] | None = None,
        start_index: int = 0,
        loop: int = 0,
    ):
        super().__init__(
            board, movements,
            start_index=start_index,
            step_count=len(repack(movements, list)) if movements else 0,
            loop=loop,
        )

    def __copy_args__(self):
        return self.board, unpack(self.movements), self.start_index, self.loop


class SpinMovement(RepeatBentMovement):
    def __init__(
        self,
        board: Board,
        movements: Unpacked[RiderMovement] | None = None,
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
                    for move in super().moves(pos_from, piece, theoretical, index):
                        movements = self.movements[:]
                        yield move
                        self.movements = movements
                if self.reverse != 0:
                    self.movements = (self.movement_cycle[i:] + self.movement_cycle[:i])[::-1]
                    for move in super().moves(pos_from, piece, theoretical, index):
                        movements = self.movements[:]
                        yield move
                        self.movements = movements
        else:
            for move in super().moves(pos_from, piece, theoretical, index):
                movements = self.movements[:]
                yield move
                self.movements = movements

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
                    self.board.move(chained_move, False)
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
                    self.board.undo(chained_move, False)
                yield from chain_options


class MultiMovement(BaseMultiMovement):
    def __init__(
        self,
        board: Board,
        both: Unpacked[BaseMovement] | None = None,
        move: Unpacked[BaseMovement] | None = None,
        capture: Unpacked[BaseMovement] | None = None,
    ):
        self.both = repack(both or [], list)
        self.move = repack(move or [], list)
        self.capture = repack(capture or [], list)
        super().__init__(board, [*self.both, *self.move, *self.capture])

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
            for movement in self.both:
                for move in movement.moves(pos_from, piece, theoretical):
                    yield copy(move)
            for movement in self.move:
                for move in movement.moves(pos_from, piece, theoretical):
                    chained_move = move
                    while chained_move:
                        is_legal = True
                        captures = chained_move.captures or [self.board.get_piece(chained_move.pos_to)]
                        for capture in captures:
                            if piece.captures(capture) and piece != capture:
                                is_legal = False
                                break
                        if not is_legal:
                            break
                        chained_move = chained_move.chained_move
                    else:
                        yield copy(move).unmark('n').mark('m')
            for movement in self.capture:
                for move in movement.moves(pos_from, piece, theoretical):
                    chained_move = move
                    while chained_move:
                        is_legal = False
                        captures = chained_move.captures or [self.board.get_piece(chained_move.pos_to)]
                        for capture in captures:
                            if piece.captures(capture):
                                is_legal = True
                                break
                        if is_legal:
                            yield copy(move).unmark('n').mark('c')
                            break
                        chained_move = chained_move.chained_move

    def __copy_args__(self):
        return self.board, unpack(self.both), unpack(self.move), unpack(self.capture)


class RangedMultiMovement(MultiMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            move = copy(move)
            if not theoretical:
                captured_piece = self.board.get_piece(move.pos_to)
                if captured_piece.side:
                    move.set(
                        pos_to=pos_from,
                        captured=captured_piece,
                        movement_type=RangedMovement,
                    ).unmark('n').mark('g')
            yield move


class InverseMovement(BaseMultiMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        inverse_piece = piece.of(piece.side.opponent())
        for movement in self.movements:
            for move in movement.moves(pos_from, inverse_piece, theoretical):
                move.set(piece=piece, movement_type=type(self))
                if move.pos_from == move.pos_to:
                    move.pos_to = None
                yield move


class CloneMovement(BaseMultiMovement):
    def __init__(
        self,
        board: Board,
        movements: Unpacked[BaseMovement] | None = None,
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
            is_capture = move.captured or not self.board.not_a_piece(move.pos_to)
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
        light: Unpacked[BaseMovement] | None = None,
        dark: Unpacked[BaseMovement] | None = None
    ):
        self.light = repack(light or [], list)
        self.dark = repack(dark or [], list)
        super().__init__(board, [*self.light, *self.dark])

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
        left: Unpacked[BaseMovement] | None = None,
        right: Unpacked[BaseMovement] | None = None,
        bottom: Unpacked[BaseMovement] | None = None,
        top: Unpacked[BaseMovement] | None = None
    ):
        self.left = repack(left or [], list)
        self.right = repack(right or [], list)
        self.bottom = repack(bottom or [], list)
        self.top = repack(top or [], list)
        super().__init__(board, [*self.left, *self.right, *self.bottom, *self.top])

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        if (legal := pos_from[1] < ceil(self.board.board_width / 2) - self.board.notation_offset[0]) or theoretical:
            for movement in self.left:
                for move in movement.moves(pos_from, piece, theoretical):
                    move.movement_type = type(self)
                    yield copy(move).set(is_legal=legal).unmark('n').mark('[')
        if (legal := pos_from[1] >= floor(self.board.board_width / 2) - self.board.notation_offset[0]) or theoretical:
            for movement in self.right:
                for move in movement.moves(pos_from, piece, theoretical):
                    move.movement_type = type(self)
                    yield copy(move).set(is_legal=legal).unmark('n').mark(']')
        position = pos_from[0] * piece.side.direction()
        if (
            legal := position <
            ceil(self.board.board_height / 2) * piece.side.direction() - self.board.notation_offset[1]
        ) or theoretical:
            for movement in self.bottom:
                for move in movement.moves(pos_from, piece, theoretical):
                    move.movement_type = type(self)
                    yield copy(move).set(is_legal=legal).unmark('n').mark('(')
        if (
            legal := position >=
            floor(self.board.board_height / 2) * piece.side.direction() - self.board.notation_offset[1]
        ) or theoretical:
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
    def __init__(self, board: Board, movements: dict[str, Unpacked[BaseMovement]] | None = None):
        if movements is None:
            movements = {}
        self.movement_dict = {key: repack(value, list) for key, value in movements.items()}
        super().__init__(board, list(chain.from_iterable(self.movement_dict.values())))

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
                        elif self.board.fits(value, to_piece) != invert:
                            legal = True
                        yield copy(move).set(is_legal=legal).unmark('n').mark(mark)


class RelayMovement(BaseChoiceMovement):
    def __init__(
        self, board: Board,
        movements: dict[str,
            tuple[Unpacked[BaseMovement]] | tuple[Unpacked[BaseMovement], Unpacked[BaseMovement]]
        ] | None = None,
        check_enemy: int = 0
    ):
        if movements is None:
            movements = {}
        movement_dict = {
            key: (repack(packed[0], list), repack(packed[1], list))
            if len(packed := value if isinstance(value, (list, tuple)) else [value]) > 1
            else (repack(packed[0], list), repack(copy(packed[0]), list))
            for key, value in movements.items()
        }
        super().__init__(board, {key: list(chain.from_iterable(value)) for key, value in movement_dict.items()})
        self.movement_dict = movement_dict
        self.check_enemy = check_enemy

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        relay_target_dict = self.board.relay_targets.get(piece.side, {})
        relay_source_dict = self.board.relay_sources.get(piece.side, {})
        tester = copy(piece)
        tester.blocked_by = lambda p: False
        tester.captures = lambda p: p.side
        for key in self.movement_dict:
            value, invert = (key[1:], True) if key.startswith('!') else (key, False)
            relays, movements = self.movement_dict[key]
            is_relayed = False
            if not key:
                mark = None
                is_relayed = True
            else:
                mark = 'r!' if invert else 'r'
                if key not in relay_target_dict or pos_from not in relay_target_dict[key]:
                    relay_target_dict.setdefault(key, {})[pos_from] = set()
                    for relay in relays:
                        for move in relay.moves(pos_from, tester, theoretical):
                            relay_target_dict[key][pos_from].add(move.pos_to)
                            relay_source_dict.setdefault(move.pos_to, set()).add((key, pos_from))
                if key in relay_target_dict and pos_from in relay_target_dict[key]:
                    for pos in relay_target_dict[key][pos_from]:
                        relay_piece = self.board.get_piece(pos)
                        if (piece.friendly_to(relay_piece) != self.check_enemy) and self.board.fits(value, relay_piece):
                            is_relayed = True
                            break
            if not theoretical and is_relayed == invert:
                continue
            for movement in movements:
                for move in movement.moves(pos_from, piece, theoretical):
                    yield copy(move) if not mark else copy(move).set(is_legal=is_relayed).unmark('n').mark(mark)

    def __copy_args__(self):
        return self.board, {key: (unpack(value[0]), unpack(value[1])) for key, value in self.movement_dict.items()}


class CoordinateMovement(BaseChoiceMovement):
    def __init__(
        self, board: Board,
        movements: dict[str,
            tuple[Unpacked[BaseMovement]] | tuple[Unpacked[BaseMovement], Unpacked[BaseMovement]] |
            tuple[Unpacked[str | BaseMovement], Unpacked[BaseMovement], Unpacked[BaseMovement]]
        ] | None = None
    ):
        if movements is None:
            movements = {}
        to_movement = lambda x: AbsoluteMovement(board, x) if isinstance(x, str) else x
        movement_dict = {
            key: ([to_movement(x) for x in repack(packed[0], list)], repack(packed[1], list), repack(packed[2], list))
            if ((length := len(packed := value if isinstance(value, (list, tuple)) else [value])) > 2)
            else ([FreeMovement(board)], repack(packed[0], list), repack(packed[1], list))
            if length > 1 else ([FreeMovement(board)], repack(packed[0], list), repack(copy(packed[0]), list))
            for key, value in movements.items()
        }
        super().__init__(board, {key: list(chain.from_iterable(value)) for key, value in movement_dict.items()})
        self.movement_dict = movement_dict

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        relay_target_dict = self.board.relay_targets.get(piece.side, {})
        relay_source_dict = self.board.relay_sources.get(piece.side, {})
        tester = copy(piece)
        tester.blocked_by = lambda p: False
        tester.captures = lambda p: p.side
        for key in self.movement_dict:
            value, invert = (key[1:], True) if key.startswith('!') else (key, False)
            partner_lookups, movements, partner_movements = self.movement_dict[key]
            partners = []
            if not key:
                mark = None
                partners = [piece]  # self-partnership galore! jokes aside, this simply means the piece has normal moves
            else:
                mark = 'q'
                if key not in relay_target_dict or pos_from not in relay_target_dict[key]:
                    relay_target_dict.setdefault(key, {})[pos_from] = set()
                    for lookup in partner_lookups:
                        for move in lookup.moves(pos_from, tester, theoretical):
                            relay_target_dict[key][pos_from].add(move.pos_to)
                            relay_source_dict.setdefault(move.pos_to, set()).add((key, pos_from))
                if key in relay_target_dict and pos_from in relay_target_dict[key]:
                    for pos in relay_target_dict[key][pos_from]:
                        partner = self.board.get_piece(pos)
                        if piece.friendly_to(partner) and self.board.fits(value, partner):
                            partners.append(partner)
            if not theoretical and bool(partners) == invert:
                continue
            partner_poss = set()
            def partner_moves():
                for new_partner in partners:
                    for partner_movement in partner_movements:
                        for partner_move in partner_movement.moves(new_partner.board_pos, new_partner, False):
                            partner_poss.add(partner_move.pos_to)
                            yield partner_move.pos_to
            pos_generator = () if mark is None else partner_moves()
            for movement in movements:
                for move in movement.moves(pos_from, piece, theoretical):
                    is_legal = mark is None
                    if not is_legal:
                        if move.pos_to in partner_poss:
                            is_legal = True
                        else:
                            for pos in pos_generator:
                                if move.pos_to == pos:
                                    is_legal = True
                                    break
                    new_move = copy(move) if not mark else copy(move).set(is_legal=is_legal)
                    if mark is not None:
                        new_move.unmark('n').mark(mark)
                    yield new_move

    def __copy_args__(self):
        return self.board, {
            key: (unpack(value[0]), unpack(value[1]), unpack(value[2])) for key, value in self.movement_dict.items()
        }


class BaseAreaMovement(BaseChoiceMovement):
    def lookup(self, key: str, invert: bool, piece: Piece) -> bool | None:
        # Determine if the given condition (or its inversion) covers every square on the board (or none thereof).
        # Returns True if every square is covered, and False if no squares are covered. If neither, returns None.
        if key == ANY:
            return not invert
        is_area = not is_algebraic(key)
        side_area = self.board.areas.get(piece.side, {}).get(key)
        shared_area = self.board.custom_areas.get(key)
        if is_area and not (side_area or shared_area):
            return invert
        return None


class AreaMovement(BaseAreaMovement, BaseChoiceMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for key in self.movement_dict:
            value, invert = (key[1:], True) if key.startswith('!') else (key, False)
            mark = 'e!' if invert else 'e'
            lookup = self.lookup(value, invert, piece)
            if lookup is False:
                continue
            if (legal := self.board.in_area(value, pos_from, piece.side) != invert) or theoretical:
                for movement in self.movement_dict[key]:
                    for move in movement.moves(pos_from, piece, theoretical):
                        move = copy(move).set(is_legal=legal)
                        if not lookup:
                            move.unmark('n').mark(mark)
                        yield move


class BoundMovement(BaseAreaMovement, BaseChoiceMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for key in self.movement_dict:
            value, invert = (key[1:], True) if key.startswith('!') else (key, False)
            mark = 'd!' if invert else 'd'
            lookup = self.lookup(value, invert, piece)
            if lookup is False:
                continue
            for movement in self.movement_dict[key]:
                for move in movement.moves(pos_from, piece, theoretical):
                    if (legal := self.board.in_area(value, move.pos_to, piece.side) != invert) or theoretical:
                        move = copy(move).set(is_legal=legal)
                        if not lookup:
                            move.unmark('n').mark(mark)
                        yield move


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


class ImitatorMovement(BaseMovement):
    def __init__(self, board: Board, lookup_offsets: Unpacked[int] = 0, skip_promotion: int = 0, skip_drop: int = 0):
        super().__init__(board)
        self.lookup_offsets = repack(lookup_offsets or 1, list)
        self.skip_promotion = skip_promotion  # 0: promotion only (default), 1: piece only, 2: both
        self.skip_drop = skip_drop

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        movements = []
        abs_offsets, rel_offsets = set(), set()
        for offset in self.lookup_offsets:
            if not offset:
                continue
            (abs_offsets if offset < 0 else rel_offsets).add(abs(offset))
        for offsets, history in (
            (abs_offsets, self.board.move_history),
            (rel_offsets, self.board.move_history[::-1])
        ):
            offset, min_offset, max_offset = 0, min(offsets), max(offsets)
            for move in history:
                if not move:
                    offset += 1
                elif not move.is_edit:
                    offset += 1
                    if offset < min_offset or offset > max_offset:
                        continue
                    if issubclass(move.movement_type or type, DropMovement):
                        if not self.skip_drop and move.promotion:
                            movements.append(self.board.get_piece(move.pos_to).movement)
                    elif move.promotion:
                        promotion_flags = self.skip_promotion + 1
                        if promotion_flags & 1 and move.promotion:
                            movements.append(self.board.get_piece(move.pos_to).movement)
                        if promotion_flags & 2 and move.piece:
                            movements.append(move.piece.movement)
                    elif move.piece:
                        movements.append(move.piece.movement)
        for movement in movements:
            if isinstance(movement, BaseMovement):
                yield from movement.moves(pos_from, piece, theoretical)

    def __copy_args__(self):
        return self.board, unpack(self.lookup_offsets), self.skip_promotion, self.skip_drop


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
