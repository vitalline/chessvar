from __future__ import annotations

from copy import copy
from itertools import chain
from math import ceil, floor
from typing import TYPE_CHECKING, Any

from chess.movement.base import BaseMovement
from chess.movement.move import Move
from chess.movement.util import ANY, AnyDirection, Direction, Position
from chess.movement.util import add, sub, mul, ddiv, is_algebraic, from_algebraic_map
from chess.pieces.types import Covered, Delayed, Delayed1, Immune, Slow
from chess.util import Unpacked, Unset, double, fits, sign, repack, unpack

if TYPE_CHECKING:
    from chess.board import Board
    from chess.pieces.piece import AbstractPiece as Piece


class ChangingLegalMovement(BaseMovement):
    # ABC for movements that change their behavior based on certain conditions, but always return all theoretical moves.
    # NB: This is only needed for movements that toggle theoretical legality based on board state (modulo moving piece).
    # If a given piece in a given position will have the same theoretical moves, its movement needn't inherit from this.
    pass


class ChangingMovement(ChangingLegalMovement):
    # ABC for movements that change their behavior based on certain conditions, and do not return all theoretical moves.
    # NB: Movement classes that return all theoretical moves, regardless of conditions, mustn't inherit from this class.
    pass


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
            return
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
            if royal_ep_targets := self.board.royal_ep_markers.get(piece.side.opponent(), {}).get(move.pos_to, set()):
                for chained_move in (
                    Move(
                        pos_from=move.pos_to, pos_to=move.pos_to,
                        movement_type=RoyalEnPassantMovement, piece=piece,
                        captured=[self.board.get_piece(pos) for pos in royal_ep_targets],
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

    def bound_stop_condition(self, move: Move, direction: AnyDirection, next_pos_to: Position) -> bool:
        # Helper function for the stop_condition() method that checks if the next position is out of bounds
        return (
            not self.in_bounds(next_pos_to)
            or ((move.pos_from == move.pos_to and self.steps) if self.loop else (move.pos_from == next_pos_to))
            or len(direction) > 2 and direction[2] and self.steps >= direction[2]
        )

    def stop_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        next_pos_to = self.transform(add(move.pos_from, mul(double(direction), self.steps + 1)))
        return (
            self.bound_stop_condition(move, direction, next_pos_to)
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
            return max(self.bounds[i][1] - self.bounds[i][0] for i in range(2))
        return (((stop - 1 - position) if direction > 0 else (position - start)) - self.shift) // abs(direction)

    def initialize_direction(self, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        self.data['max_steps'] = min(
            ceil(self.steps_to_edge(pos_from[i], direction[i], *self.bounds[i]) / 2) for i in range(2)
        )

    def stop_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        return self.steps >= self.data['max_steps'] or super().stop_condition(move, direction, piece, theoretical)

    def __copy_args__(self):
        return self.board, unpack(self.directions), self.shift, self.boundless, self.loop


class CannonRiderMovement(RiderMovement, ChangingMovement):
    default_mark = 'p'

    def __init__(
        self, board: Board,
        directions: Unpacked[AnyDirection] | None = None,
        distance: int = 0, skip_pieces: int = 0,
        boundless: int = 0, loop: int = 0
    ):
        super().__init__(board, directions, boundless, loop)
        self.distance = distance  # max distance that can be travelled after jumping over pieces
        self.skip_pieces = skip_pieces
        self.skip_pieces_max = (0 if skip_pieces < 0 else skip_pieces) + 1
        self.skip_pieces_min = 0 if skip_pieces > 0 else -skip_pieces
        # the above logic makes it so that:
        # if skip_pieces < 0, at least -skip_pieces pieces in a row must be jumped over
        # otherwise, at most skip_pieces + 1 pieces in a row can be jumped over
        # this means that by default, exactly one piece can be jumped over, which is how cannon pieces work normally
        # NB: currently it is impossible to define jumping over some but not all pieces in a row. this may change later.

    def initialize_direction(self, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        self.data['jump'] = -1
        self.data['move'] = 0

    def advance_direction(self, move: Move, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        jump_started = self.data['jump'] >= 0
        jump_ended = False
        if self.data['jump'] < abs(self.skip_pieces):
            if not self.board.not_a_piece(self.transform(move.pos_to)):
                self.data['jump'] += 1
                return
            if not jump_started:
                return
            jump_ended = True
            if not self.skip_pieces_min:
                self.data['jump'] = self.skip_pieces_max - 1  # NB: the -1 comes from the increment immediately later on
        self.data['jump'] += 1
        if self.skip_pieces_min:
            jump_ended |= jump_started and self.board.not_a_piece(self.transform(move.pos_to))
        else:
            jump_ended |= self.data['jump'] >= self.skip_pieces_max
        if jump_ended:
            self.data['move'] += 1

    def skip_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        if (self.data['jump'] >= max(self.skip_pieces_min, 1)) if theoretical else (self.data['move'] > 0):
            return super().skip_condition(move, direction, piece, theoretical)
        return True

    def stop_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        next_pos_to = self.transform(add(move.pos_from, mul(double(direction), self.steps + 1)))
        if self.data['jump'] < 0:
            if not (self.loop and move.pos_from == next_pos_to) and piece.blocked_by(self.board.get_piece(next_pos_to)):
                return self.bound_stop_condition(move, direction, next_pos_to)
        elif self.data['jump'] < self.skip_pieces_min - 1 and not theoretical:
            if not (self.loop and move.pos_from == next_pos_to):
                if not self.board.not_a_piece(next_pos_to):
                    return self.bound_stop_condition(move, direction, next_pos_to)
                return True
        elif self.data['jump'] == self.skip_pieces_max - 1 and not self.skip_pieces_min and not theoretical:
            if not (self.loop and move.pos_from == next_pos_to) and piece.blocked_by(self.board.get_piece(next_pos_to)):
                return True
        elif self.distance and self.data['move'] >= self.distance and not theoretical:
            return True
        elif theoretical:
            next_piece = self.board.get_piece(next_pos_to)
            if (
                not piece.skips(next_piece) and isinstance(next_piece, Immune)
                and isinstance(next_piece, self.board.piece_abc) and next_piece.movement is None
            ):
                return self.bound_stop_condition(move, direction, next_pos_to)
        return super().stop_condition(move, direction, piece, theoretical or not self.data['move'])

    def __copy_args__(self):
        return self.board, unpack(self.directions), self.distance, self.skip_pieces, self.boundless, self.loop


class HopperRiderMovement(CannonRiderMovement):
    default_mark = 'l'

    def initialize_direction(self, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        super().initialize_direction(direction, pos_from, piece)
        self.data['captured'] = []

    def advance_direction(self, move: Move, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        super().advance_direction(move, direction, pos_from, piece)
        if self.data['jump'] >= 0 and not self.data['move']:
            captured = self.board.get_piece(move.pos_to)
            if piece.captures(captured):
                self.data['captured'].append(captured)

    def stop_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        next_pos_to = self.transform(add(move.pos_from, mul(double(direction), self.steps + 1)))
        if not (self.loop and move.pos_from == next_pos_to):
            next_piece = self.board.get_piece(next_pos_to)
            if not theoretical:
                if self.skip_pieces_min and not self.data['move']:
                    if next_piece.side and not piece.captures(next_piece):
                        return True
                elif self.data['jump'] < self.skip_pieces_max - 1:
                    if next_piece.side and not piece.captures(next_piece):
                        return True
                else:
                    if next_piece.side:
                        return True
            elif (
                not piece.skips(next_piece) and isinstance(next_piece, Immune)
                and isinstance(next_piece, self.board.piece_abc) and next_piece.movement is None
            ):
                return True
        return super().stop_condition(move, direction, piece, theoretical)

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            if not theoretical and self.data['captured']:
                move.set(captured=self.data['captured'])
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
        self.data['captured'] = None
        if self.distance < 0:
            capture_pos = self.transform(add(pos_from, mul(double(direction), self.distance)))
            capture = self.board.get_piece(capture_pos)
            if piece.captures(capture):
                self.data['captured'] = capture

    def advance_direction(self, move: Move, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        if self.distance > 0:
            capture_pos = self.transform(add(move.pos_to, mul(double(direction), self.distance)))
            capture = self.board.get_piece(capture_pos)
            if piece.captures(capture):
                self.data['captured'] = capture

    def stop_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        if not theoretical:
            next_pos_to = self.transform(add(move.pos_from, mul(double(direction), self.steps + 1)))
            if not (self.loop and move.pos_from == next_pos_to) and not self.board.not_a_piece(next_pos_to):
                return True
        return super().stop_condition(move, direction, piece, theoretical)

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            if not theoretical and self.data['captured']:
                move.set(captured=self.data['captured'])
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
        next_pos_to = self.transform(add(move.pos_from, mul(double(direction), self.steps + 1)))
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
            move.pos_to = self.transform(add(move.pos_from, mul(double(direction), self.steps)))
            result = super().skip_condition(move, direction, piece, theoretical)
            move.pos_to = move.pos_from
            return result
        return super().skip_condition(move, direction, piece, theoretical)

    def stop_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        if move.captured:
            move.pos_to = self.transform(add(move.pos_from, mul(double(direction), self.steps)))
            result = super().stop_condition(move, direction, piece, theoretical)
            move.pos_to = move.pos_from
            return result
        return super().stop_condition(move, direction, piece, theoretical)


class AutoActMovement(BaseMovement):
    # ABC for movements that can automatically act on the board after the move is made

    def generate(self, move: Move, piece: Piece) -> Move:
        # This method should be overridden in subclasses to implement the specific action
        return move


class RangedAutoActRiderMovement(AutoActMovement, RiderMovement):
    # ABC for auto-acting movements that act on all squares they can move to

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            move.movement_type = RiderMovement
            if not theoretical:
                last_move = move
                while last_move.chained_move:
                    last_move = last_move.chained_move
                self.generate(last_move, piece)
            yield move


class AutoMarkMovement(BaseMovement):
    # ABC for movements that need to keep track of the squares that they can move to
    # Currently used to implement auto-acting movements that activate upon any move,
    # because AutoActMovement may only execute an action of the piece that had moved
    # NB: Actions generated by this movement type are not generated when determining
    # if the moving player is in check, so they won't affect whether a move is legal
    # (though, if a player leaves such a check unanswered, it does count as a loss).

    mark_type = Unset

    def mark(self, pos: Position, piece: Piece, theoretical: bool = True):
        generators = [(self.moves(pos, piece), self.board.auto_markers)]
        if theoretical:
            generators.append((self.moves(pos, piece, True), self.board.auto_markers_theoretical))
        for moves, markers in generators:
            for move in moves:
                if move.pos_to not in markers[piece.side]:
                    markers[piece.side][move.pos_to] = {}
                if self.mark_type not in markers[piece.side][move.pos_to]:
                    markers[piece.side][move.pos_to][self.mark_type] = set()
                markers[piece.side][move.pos_to][self.mark_type].add(pos)

    def unmark(self, pos: Position, piece: Piece, theoretical: bool = True):
        generators = [(self.moves(pos, piece), self.board.auto_markers)]
        if theoretical:
            generators.append((self.moves(pos, piece, True), self.board.auto_markers_theoretical))
        for moves, markers in generators:
            for move in moves:
                if move.pos_to in markers[piece.side]:
                    if self.mark_type in markers[piece.side][move.pos_to]:
                        markers[piece.side][move.pos_to][self.mark_type].discard(pos)
                        if not markers[piece.side][move.pos_to][self.mark_type]:
                            del markers[piece.side][move.pos_to][self.mark_type]
                    if not markers[piece.side][move.pos_to]:
                        del markers[piece.side][move.pos_to]

    def update(self, move: Move, piece: Piece):
        self.unmark(move.pos_from, piece)
        self.mark(move.pos_to, piece)
        super().update(move, piece)

    def undo(self, move: Move, piece: Piece):
        super().undo(move, piece)
        self.unmark(move.pos_to, piece)
        self.mark(move.pos_from, piece)


class AutoCaptureMovement(RangedAutoActRiderMovement):
    # NB: The auto-capture implementation assumes that all pieces that utilize it capture up to one piece per direction.
    # This is true for the only army that utilizes this movement type, but it may not work correctly in other scenarios.

    default_mark = 't'

    def __init__(
        self, board: Board,
        directions: Unpacked[AnyDirection] | None = None,
        targets: Unpacked[str] | None = None,
        boundless: int = 0, loop: int = 0
    ):
        super().__init__(board, directions, boundless, loop)
        self.targets = repack(targets or [], list)

    def generate(self, move: Move, piece: Piece) -> Move:
        if not move.is_edit:
            captured = []
            for capture in super().moves(move.pos_to, piece):
                captured_piece = self.board.get_piece(capture.pos_to)
                if self.targets and not self.board.fits_one(self.targets, (), captured_piece):
                    continue
                if piece.captures(captured_piece):
                    captured.append(captured_piece)
            if captured:
                last_chain_move = move
                while last_chain_move.chained_move:
                    last_chain_move = last_chain_move.chained_move
                last_chain_move.set(chained_move=Move(
                    pos_from=move.pos_to, pos_to=move.pos_to,
                    piece=piece, captured=captured,
                    movement_type=AutoCaptureMovement
                ))
        return move

    def __copy_args__(self):
        return self.board, unpack(self.directions), unpack(self.targets), self.boundless, self.loop


class RangedAutoCaptureRiderMovement(AutoCaptureMovement):
    pass  # Alias for AutoCaptureMovement


class RangedAutoRiderMovement(RangedAutoCaptureRiderMovement):
    pass  # Alias for RangedAutoCaptureRiderMovement


class AutoRangedAutoCaptureRiderMovement(AutoMarkMovement, AutoCaptureMovement):
    mark_type = AutoCaptureMovement


class AutoRangedRiderMovement(AutoRangedAutoCaptureRiderMovement):
    pass  # Alias for AutoRangedAutoCaptureRiderMovement


class ConvertMovement(RangedAutoActRiderMovement):
    default_mark = 'y'

    def __init__(
        self, board: Board,
        directions: Unpacked[AnyDirection] | None = None,
        targets: Unpacked[str] | None = None,
        partial_range: int = 0,
        boundless: int = 0, loop: int = 0
    ):
        super().__init__(board, directions, boundless, loop)
        self.targets = repack(targets or [], list)
        self.partial_range = partial_range

    def generate(self, move: Move, piece: Piece) -> Move:
        if not move.is_edit:
            conversions = {}
            for convert in super().moves(move.pos_to, piece):
                converted_piece = self.board.get_piece(convert.pos_to)
                if not converted_piece.side and not self.partial_range:
                    conversions = {}
                    break
                if piece.friendly_of(converted_piece):
                    continue
                if self.targets and not self.board.fits_one(self.targets, (), converted_piece):
                    if self.partial_range:
                        continue
                    conversions = {}
                    break
                if piece.captures(converted_piece):
                    new_piece = converted_piece.of(piece.side)
                    new_piece.set_moves(None)
                    conversions[convert.pos_to] = Move(
                        pos_from=convert.pos_to, pos_to=convert.pos_to,
                        piece=converted_piece, promotion=new_piece,
                        movement_type=ConvertMovement,
                    )
            if conversions:
                last_chain_move = move
                while last_chain_move.chained_move:
                    last_chain_move = last_chain_move.chained_move
                for convert_pos_to in sorted(conversions):
                    last_chain_move.set(chained_move=conversions[convert_pos_to])
                    last_chain_move = last_chain_move.chained_move
        return move

    def __copy_args__(self):
        return self.board, unpack(self.directions), unpack(self.targets), self.partial_range, self.boundless, self.loop


class RangedConvertRiderMovement(ConvertMovement):
    pass  # Alias for ConvertMovement


class RangeConvertRiderMovement(RangedConvertRiderMovement):
    pass  # Alias for RangedConvertRiderMovement


class AutoRangedConvertRiderMovement(AutoMarkMovement, ConvertMovement):
    mark_type = ConvertMovement

    def __init__(
        self, board: Board,
        directions: Unpacked[AnyDirection] | None = None,
        targets: Unpacked[str] | None = None,
        # NB: non-partial range support for auto-conversion is not implemented
        boundless: int = 0, loop: int = 0
    ):
        super().__init__(board, directions, targets, 1, boundless, loop)

    def __copy_args__(self):
        return self.board, unpack(self.directions), unpack(self.targets), self.boundless, self.loop


class AutoConvertRiderMovement(AutoRangedConvertRiderMovement):
    pass  # Alias for AutoRangedConvertRiderMovement


class ReversiRiderMovement(ConvertMovement):
    def __init__(
        self, board: Board,
        directions: Unpacked[AnyDirection] | None = None,
        targets: Unpacked[str] | None = None,
        # NB: partial range support for reversi-style conversion is not implemented
        boundless: int = 0, loop: int = 0
    ):
        super().__init__(board, directions, targets, 0, boundless, loop)

    def reversi_initialize(self, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        self.data['state'] = 0

    def reversi_advance(self, move: Move, direction: AnyDirection, pos_from: Position, piece: Piece) -> None:
        if self.data['state'] == 0:
            new_piece = self.board.get_piece(self.transform(move.pos_to))
            if not new_piece.side:
                self.data['state'] = -1
            elif piece.friendly_to(new_piece):
                if len(direction) > 3 and self.steps < direction[3]:
                    self.data['state'] = -1
                else:
                    self.data['state'] = 1
            elif self.targets and not self.board.fits_one(self.targets, (), new_piece):
                self.data['state'] = -1
            elif not piece.captures(new_piece):
                self.data['state'] = -1

    def reversi_skip(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        return not theoretical and self.data['state'] <= 0

    def reversi_stop(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        if not theoretical and self.data['state'] != 0:
            return True
        next_pos_to = self.transform(add(move.pos_from, mul(double(direction), self.steps + 1)))
        return self.bound_stop_condition(move, direction, next_pos_to)

    def generate(self, move: Move, piece: Piece) -> Move:
        if not move.is_edit:
            self.initialize_direction, old_initialize = self.reversi_initialize, self.initialize_direction
            self.advance_direction, old_advance = self.reversi_advance, self.advance_direction
            self.skip_condition, old_skip = self.reversi_skip, self.skip_condition
            self.stop_condition, old_stop = self.reversi_stop, self.stop_condition
            old_directions = self.directions
            conversions = {}
            for direction in old_directions:
                self.directions = [direction]
                direction = piece.side.direction(direction)
                for convert in super().moves(move.pos_to, piece):
                    offset = sub(convert.pos_to, move.pos_to)
                    for distance in range(1, ddiv(offset, direction)):
                        convert_pos = add(move.pos_to, mul(direction, distance))
                        converted_piece = self.board.get_piece(convert_pos)
                        if piece.friendly_of(converted_piece):
                            continue
                        if piece.captures(converted_piece):
                            new_piece = converted_piece.of(piece.side)
                            new_piece.set_moves(None)
                            conversions[convert_pos] = Move(
                                pos_from=convert_pos, pos_to=convert_pos,
                                piece=converted_piece, promotion=new_piece,
                                movement_type=ConvertMovement,
                            )
            self.directions = old_directions
            self.initialize_direction = old_initialize
            self.advance_direction = old_advance
            self.skip_condition = old_skip
            self.stop_condition = old_stop
            if conversions:
                last_chain_move = move
                while last_chain_move.chained_move:
                    last_chain_move = last_chain_move.chained_move
                for convert_pos_to in sorted(conversions):
                    last_chain_move.set(chained_move=conversions[convert_pos_to])
                    last_chain_move = last_chain_move.chained_move
        return move

    def __copy_args__(self):
        return self.board, unpack(self.directions), unpack(self.targets), self.boundless, self.loop


class SwapRiderMovement(RiderMovement):
    default_mark = '-'

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            if not theoretical:
                swapped_piece = self.board.get_piece(move.pos_to)
                if not (swapped_piece.side and swapped_piece.movement):
                    continue
                move.set(swapped_piece=swapped_piece.on(move.pos_to), captured=[])
            yield move

    def stop_condition(self, move: Move, direction: AnyDirection, piece: Piece, theoretical: bool = False) -> bool:
        if not theoretical and not self.board.not_a_piece(move.pos_to):
            return True
        return super().stop_condition(move, direction, piece, theoretical)


class DropMovement(BaseMovement):
    # Used to mark piece drops
    pass


class TargetMovement(BaseMovement):
    # ABC used to simplify marking squares where en passant captures are possible

    def add_markers(self, piece: Piece, target_pos: Position, marker_poss: list[Position], royal: Unpacked[Any] = ()):
        if not marker_poss:
            return
        target_dict, marker_dict = tuple(data_dict.get(piece.side, {}) for data_dict in {
            True: (self.board.royal_ep_targets, self.board.royal_ep_markers),
        }.get(bool(royal), (self.board.en_passant_targets, self.board.en_passant_markers)))
        data_set = set(repack(royal))
        if isinstance(piece, Covered):
            data_set.add(Covered)
        if isinstance(piece, Delayed):
            data_set.add(Delayed)
        elif isinstance(piece, Delayed1):
            data_set.add(Delayed1)
        if isinstance(piece, Slow):
            data_set.add(Slow)
        target_dict[target_pos] = {pos: data_set.copy() for pos in marker_poss}
        for pos in marker_poss:
            marker_dict.setdefault(pos, set()).add(target_pos)


class CastlingMovement(TargetMovement):
    def __init__(
        self,
        board: Board,
        direction: Direction,
        other_piece: Direction,
        other_direction: Direction,
        movement_gap: Unpacked[Direction] | None = None,
        en_passant_gap: Unpacked[Direction] | None = None,
        other_movement_gap: Unpacked[Direction] | None = None,
        other_en_passant_gap: Unpacked[Direction] | None = None,
        move_threshold: Unpacked[int] = 0,
    ):
        super().__init__(board)
        self.direction = direction
        self.other_piece = other_piece
        self.other_direction = other_direction
        self.movement_gap = repack(movement_gap or [], list)
        self.en_passant_gap = repack(en_passant_gap or [], list)
        self.other_movement_gap = repack(other_movement_gap or [], list)
        self.other_en_passant_gap = repack(other_en_passant_gap or [], list)
        self.move_threshold = repack(move_threshold or 0, list)

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        if piece.total_moves > self.move_threshold[0] >= 0:
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
        if not other_piece.side:
            return ()
        if other_piece.total_moves > self.move_threshold[-1] >= 0:
            return ()
        if not theoretical:
            for gap_offset in self.movement_gap:
                pos = add(pos_from, piece.side.direction(gap_offset))
                if not piece.skips(self.board.get_piece(pos)):
                    return ()
            for gap_offset in self.other_movement_gap:
                pos = add(other_piece_pos, piece.side.direction(gap_offset))
                if not other_piece.skips(self.board.get_piece(pos)):
                    return ()
        self_move = Move(pos_from=pos_from, pos_to=pos_to, movement_type=type(self)).mark('0')
        if pos_to == other_piece_pos:
            self_move.set(swapped_piece=other_piece)
            other_piece_pos = pos_from
        other_move = Move(
            pos_from=other_piece_pos, pos_to=other_piece_pos_to, movement_type=CastlingPartnerMovement,
            piece=other_piece if not self_move.swapped_piece else other_piece.on(other_piece_pos),
        ).mark('c0')  # marking the chained move too, just in case
        return self_move.set(chained_move=other_move),

    def update(self, move: Move, piece: Piece):
        if move.pos_from and move.pos_to:
            direction = piece.side.direction(self.direction)
            offset = sub(move.pos_to, move.pos_from)
            if offset == direction:
                positions = []
                for gap_offset in self.en_passant_gap:
                    positions.append(add(move.pos_from, gap_offset))
                self.add_markers(piece, move.pos_to, positions, royal=type(self))
                other_pos_from = add(move.pos_from, piece.side.direction(self.other_piece))
                other_piece_pos = other_pos_from
                if move.pos_to == other_pos_from:
                    other_piece_pos = move.pos_from
                if (
                    move.chained_move and move.chained_move.pos_from and move.chained_move.pos_to
                    and move.chained_move.pos_from == other_piece_pos and move.chained_move.pos_to != other_pos_from
                ):
                    other_direction = piece.side.direction(self.other_direction)
                    other_offset = sub(move.chained_move.pos_to, other_pos_from)
                    if other_offset == other_direction:
                        positions = []
                        for gap_offset in self.other_en_passant_gap:
                            positions.append(add(other_pos_from, gap_offset))
                        self.add_markers(move.chained_move.piece, move.chained_move.pos_to, positions, royal=type(self))
        super().update(move, piece)

    def __copy_args__(self):
        return (
            self.board, self.direction, self.other_piece, self.other_direction,
            unpack(self.movement_gap), unpack(self.en_passant_gap),
            unpack(self.other_movement_gap), unpack(self.other_en_passant_gap),
            (self.move_threshold if self.move_threshold[0] != self.move_threshold[-1] else self.move_threshold[0]),
        )


class CastlingPartnerMovement(BaseMovement):
    # Used to mark the second part of a CastlingMovement move chain
    pass


class RoyalEnPassantMovement(BaseMovement):
    # Used to mark en passant captures of royals that moved through check
    pass


class EnPassantTargetRiderMovement(RiderMovement, TargetMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            move.movement_type = RiderMovement
            yield move

    def update(self, move: Move, piece: Piece):
        if move.pos_from and move.pos_to:
            for direction in self.directions:
                direction = piece.side.direction(direction)
                offset = sub(move.pos_to, move.pos_from)
                steps = ddiv(offset, direction[:2])
                if steps < 2:
                    continue
                if len(direction) > 2 and steps > direction[2]:
                    continue
                positions = [add(move.pos_from, mul(direction[:2], i)) for i in range(1, steps)]
                self.add_markers(piece, move.pos_to, positions)
        super().update(move, piece)


class EnPassantRiderMovement(RiderMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            move.movement_type = RiderMovement
            if not theoretical:
                if ep_targets := self.board.en_passant_markers.get(piece.side.opponent(), {}).get(move.pos_to, set()):
                    move.set(
                        captured=move.captured + [self.board.get_piece(pos) for pos in ep_targets],
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
        super().__init__(board, ANY, stay)

    def __copy_args__(self):
        return self.board, self.stay


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
            index = max(0, self.total_moves)
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
                    return
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
            return
        true_index = index
        if index >= len(self.dir_indexes):
            if self.cycle_mode > 0:
                index %= len(self.dir_indexes)
            elif self.cycle_mode < 0:
                index %= 2 * (len(self.dir_indexes) - 1)
                if index >= len(self.dir_indexes):
                    index = 2 * (len(self.dir_indexes) - 1) - index
            else:
                return
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
                            pos_to = movement.transform(add(move.pos_from, mul(double(direction), movement.steps)))
                        if pos_to == pos_from:
                            stop = True
                    move.movement_type = type(self)
                    if not stop or self.loop:
                        dir_indexes = self.dir_indexes[:]  # oh hey, remember when this very thing was in RiderMovement?
                        if self.start_index <= index and self.skip_count <= true_index:
                            yield copy(move)
                        elif theoretical:
                            yield copy(move).set(is_legal=False).unmark('n').mark('a')
                        self.dir_indexes = dir_indexes  # yeah, that's still a thing.
                    if stop:
                        break
                if (
                    not stop and move is not None and (len(direction) < 3 or direction[2] and
                    move.pos_to == add(pos_from, piece.side.direction(mul(double(direction), direction[2]))))
                    and (theoretical or not self.board.get_piece(move.pos_to).side)
                ):
                    for bent_move in self.moves(move.pos_to, piece, theoretical, true_index + 1):
                        dir_indexes = self.dir_indexes[:]  # i'm not even going to bother explaining this one
                        yield copy(bent_move).set(pos_from=pos_from, captured=move.captured + bent_move.captured)
                        self.dir_indexes = dir_indexes  # you can probably guess what this does by now, moving on
        else:
            return

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


class SplitMovement(RepeatBentMovement):
    def __init__(
        self,
        board: Board,
        movements: Unpacked[RiderMovement] | None = None,
        step_count: int = 0,
        skip_count: int = 0,
        loop: int = 0,
    ):
        super().__init__(
            board, movements,
            step_count=step_count,
            skip_count=skip_count,
            loop=loop,
            cycle_mode=1,
            path_split=1,
        )
        self.movement_list = copy(self.movements)
        self.dir_indexes = [-1]

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False, index: int = 0):
        for true_index in range(len(self.movement_list)):
            self.movements = [self.movement_list[true_index]]
            for move in super().moves(pos_from, piece, theoretical, index):
                movements = self.movements[:]
                yield move
                self.movements = movements

    def __copy_args__(self):
        return self.board, unpack(self.movement_list), self.step_count, self.skip_count, self.loop


class StageMovement(BaseMultiMovement):
    def raise_pieces(self, pieces: list[Piece]):
        for piece in pieces:
            blank = type(self.board.no_piece)(board=self.board, board_pos=piece.board_pos)
            abs_pos = self.board.get_absolute(piece.board_pos)
            self.board.pieces[abs_pos[0]][abs_pos[1]] = blank

    def lower_pieces(self, pieces: list[Piece]):
        for piece in pieces:
            abs_pos = self.board.get_absolute(piece.board_pos)
            self.board.pieces[abs_pos[0]][abs_pos[1]] = piece

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False, index: int = 0):
        if index >= len(self.movements):
            return
        if index == len(self.movements) - 1:
            for move in self.movements[index].moves(pos_from, piece, theoretical):
                self.board.update_move(move)
                yield move
            return
        if theoretical:
            for movement in self.movements:
                yield from movement.moves(pos_from, piece, theoretical)
        else:
            for move in chain([None], self.movements[index].moves(pos_from, piece, theoretical)):
                if move is None:
                    yield from self.moves(pos_from, piece, theoretical, index + 1)
                    continue
                self.board.update_move(move)
                self.raise_pieces(move.captured)
                next_move_exists = False
                for next_move in self.moves(pos_from, piece, theoretical, index + 1):
                    if next_move.pos_from == move.pos_from and next_move.pos_to == move.pos_to:
                        next_move_exists = True
                        combined_move = copy(next_move).set(
                            captured=move.captured + next_move.captured,
                            chained_move=move.chained_move or next_move.chained_move,
                        )
                        self.lower_pieces(move.captured)
                        self.board.update_move(combined_move)
                        yield combined_move
                        self.raise_pieces(move.captured)
                self.lower_pieces(move.captured)
                if not next_move_exists:
                    yield move


class BaseChainMovement(BaseMovement):
    # ABC for movements that need to simulate a chain of moves during their move generation

    @staticmethod
    def expand(move: Move | None) -> list[Move]:
        if not move:
            return []
        move_chain = [move]
        while move_chain[-1].chained_move:
            move_chain.append(move_chain[-1].chained_move)
        move_chain = [copy(chained_move).set(chained_move=Unset) for chained_move in move_chain]
        return move_chain

    @staticmethod
    def contract(move_chain: list[Move]) -> Move | None:
        if not move_chain:
            return None
        move = copy(move_chain[0])
        last_move = move
        for chained_move in move_chain[1:]:
            last_move = last_move.set(chained_move=copy(chained_move)).chained_move
        last_move.chained_move = None
        return move

    def advance(self, move_chain: list[Move], in_promotion: bool = False) -> Position | None:
        if not move_chain:
            return None
        last_pos = move_chain[0].pos_from
        for i, chained_move in enumerate(move_chain):
            if i or not in_promotion:
                self.board.update_move(chained_move)
                self.board.move(chained_move, False)
            if last_pos == chained_move.pos_from:
                last_pos = chained_move.pos_to
        return last_pos

    def rollback(self, move_chain: list[Move], in_promotion: bool = False):
        for i, chained_move in list(enumerate(move_chain))[::-1]:
            if i or not in_promotion:
                self.board.undo(chained_move, False)


class ChainMovement(BaseMultiMovement, BaseChainMovement):
    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False, index: int = 0):
        if index >= len(self.movements):
            return
        if index == len(self.movements) - 1:
            for move in self.movements[index].moves(pos_from, piece, theoretical):
                self.board.update_move(move)
                yield move
            return
        if theoretical:
            for move in self.movements[index].moves(pos_from, piece, theoretical):
                yield copy(move)
                chained_move = move
                while chained_move.chained_move:
                    chained_move = chained_move.chained_move
                    yield copy(chained_move).set(pos_from=move.pos_from)
                last_chain_move = chained_move
                for chained_move in self.moves(last_chain_move.pos_to, piece, theoretical, index + 1):
                    yield copy(chained_move).set(pos_from=move.pos_from).unmark('n').mark('+')
        else:
            for move in self.movements[index].moves(pos_from, piece, theoretical):
                move_chain = self.expand(move)
                if move_chain[-1].movement_type == RoyalEnPassantMovement:
                    yield move
                last_pos = self.advance(move_chain)
                chain_options = []
                for last_chained_move in self.moves(last_pos, piece, theoretical, index + 1):
                    chain_options.append(self.contract(move_chain + [last_chained_move]))
                self.rollback(move_chain)
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
                        captures = chained_move.captured or [self.board.get_piece(chained_move.pos_to)]
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
                        captures = chained_move.captured or [self.board.get_piece(chained_move.pos_to)]
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
                captured = copy(move.captured)
                captured_piece = self.board.get_piece(move.pos_to)
                if captured_piece.side:
                    captured.append(captured_piece)
                if captured:
                    move.set(
                        pos_to=pos_from,
                        captured=captured,
                        movement_type=RangedMovement,
                    ).unmark('n').mark('g')
            yield move


class MultiActMovement(AutoActMovement, AutoMarkMovement, BaseMultiMovement, BaseChainMovement):
    def __init__(
        self,
        board: Board,
        move: Unpacked[BaseMovement] | None = None,
        active: Unpacked[AutoActMovement | AutoMarkMovement] | None = None,
        passive: Unpacked[AutoMarkMovement] | None = None,
    ):
        self.move = repack(move or [], list)
        self.active = repack(active or [], list)
        self.passive = repack(passive or [], list)
        super().__init__(board, [*self.move, *self.active, *self.passive])

    def generate(self, move: Move, piece: Piece) -> Move:
        if move.is_edit:
            return move
        actions = [movement for movement in self.active if isinstance(movement, AutoActMovement)]
        if not actions:
            return move
        promotion_piece = self.board.promotion_piece
        move_chain = self.expand(move)
        first_pos = move_chain[0].pos_from
        last_pos = self.advance(move_chain, bool(promotion_piece))
        full_move = Move(
            pos_from=first_pos,
            pos_to=last_pos,
            piece=piece,
        )
        delta_chain = []
        for movement in actions:
            self.advance(delta_chain)
            move_chain += delta_chain
            delta_chain = self.expand(movement.generate(copy(full_move), piece).chained_move)
        move = self.contract(move_chain + delta_chain)
        self.rollback(move_chain, bool(promotion_piece))
        self.board.promotion_piece = promotion_piece
        return move

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for movement in self.move:
            for move in movement.moves(pos_from, piece, theoretical):
                yield move if theoretical else self.generate(move, piece)
        if not theoretical:
            return
        for movement in [*self.active, *self.passive]:
            if isinstance(movement, AutoMarkMovement):
                for move in movement.moves(pos_from, piece, theoretical):
                    yield move

    def mark(self, pos: Position, piece: Piece, theoretical: bool = True):
        for movement in [*self.active, *self.passive]:
            if isinstance(movement, AutoMarkMovement):
                movement.mark(pos, piece, theoretical)

    def unmark(self, pos: Position, piece: Piece, theoretical: bool = True):
        for movement in [*self.active, *self.passive]:
            if isinstance(movement, AutoMarkMovement):
                movement.unmark(pos, piece, theoretical)

    def __copy_args__(self):
        return self.board, unpack(self.move), unpack(self.active), unpack(self.passive)


class MultiEnPassantTargetMovement(BaseMultiMovement, TargetMovement):
    def __init__(
        self, board: Board, movement_pairs: Unpacked[tuple[BaseMovement, BaseMovement]] | None = None
    ):
        movement_pairs = [tuple(x) for x in repack(movement_pairs or [], list)]
        super().__init__(board, list(chain.from_iterable(movement_pairs)))
        self.movement_pairs = movement_pairs

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for movement, _ in self.movement_pairs:
            yield from movement.moves(pos_from, piece, theoretical)

    def update(self, move: Move, piece: Piece):
        tester = copy(piece)
        tester.blocked_by = lambda p: False
        tester.captures = lambda p: p.side
        move_found = False
        for movement, target_movement in self.movement_pairs:
            for tester_move in movement.moves(move.pos_from, tester, False):
                if move.pos_to != tester_move.pos_to:
                    continue
                positions = []
                for target_move in target_movement.moves(move.pos_from, tester, False):
                    positions.append(target_move.pos_to)
                self.add_markers(piece, move.pos_to, positions)
                move_found = True
                break
            if move_found:
                break
        super().update(move, piece)

    def __copy_args__(self):
        return self.board, unpack(self.movement_pairs)


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
        both = move and capture
        if both and (move > 0) is (capture > 0):
            move = capture = 0
        if not both and (move < 0 or capture < 0):
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
                        captures = move.captured[:]
                        to_piece = self.board.get_piece(move.pos_to)
                        if to_piece.side and piece.captures(to_piece) and not move.swapped_piece:
                            captures.append(to_piece)
                        if not value:
                            if not captures != invert:
                                legal = True
                        elif any(piece.captures(x) and self.board.fits(value, x) for x in captures) != invert:
                            legal = True
                        if not theoretical and not legal:
                            continue
                        yield copy(move).set(is_legal=legal).unmark('n').mark(mark)


class ChoiceActMovement(AutoActMovement, ChoiceMovement, BaseChainMovement):
    def __init__(
        self,
        board: Board,
        movements: dict[str, Unpacked[BaseMovement]] | None = None,
        actions: dict[str, Unpacked[AutoActMovement]] | None = None
    ):
        if movements is None:
            movements = {}
        if actions is None:
            actions = {}
        movement_dict = {key: repack(value, list) for key, value in movements.items()}
        action_dict = {key: repack(value, list) for key, value in actions.items()}
        super().__init__(board, {**movement_dict, **action_dict})
        self.movement_dict = movement_dict
        self.action_dict = action_dict

    def generate(self, move: Move, piece: Piece) -> Move:
        if move.is_edit:
            return move
        caps = move.captured[:]
        to_piece = self.board.get_piece(move.pos_to)
        if to_piece.side and piece.captures(to_piece) and not move.swapped_piece:
            caps.append(to_piece)
        splits = [(k, k[1:], True) if k.startswith('!') else (k, k, False) for k in self.action_dict]
        matches = [k for k, v, i in splits if (
            (any(piece.captures(x) and self.board.fits(v, x) for x in caps) if v else not caps) != i
        )]
        actions = [mv for k in matches for mv in self.action_dict[k] if isinstance(mv, AutoActMovement)]
        if not actions:
            return move
        promotion_piece = self.board.promotion_piece
        move_chain = self.expand(move)
        first_pos = move_chain[0].pos_from
        last_pos = self.advance(move_chain, bool(promotion_piece))
        full_move = Move(
            pos_from=first_pos,
            pos_to=last_pos,
            piece=piece,
        )
        delta_chain = []
        for movement in actions:
            self.advance(delta_chain)
            move_chain += delta_chain
            delta_chain = self.expand(movement.generate(copy(full_move), piece).chained_move)
        move = self.contract(move_chain + delta_chain)
        self.rollback(move_chain, bool(promotion_piece))
        self.board.promotion_piece = promotion_piece
        return move

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            yield move if theoretical else self.generate(move, piece)

    def __copy_args__(self):
        return (
            self.board,
            {key: unpack(value) for key, value in self.movement_dict.items()},
            {key: unpack(value) for key, value in self.action_dict.items()},
        )


class RelayMovement(BaseChoiceMovement, ChangingLegalMovement):
    def __init__(
        self, board: Board,
        lookup: Unpacked[BaseMovement] | None = None,
        movements: dict[str, Unpacked[BaseMovement]] | None = None,
        check_enemy: int = 0
    ):
        if movements is None:
            movements = {}
        lookup = repack(lookup or [], list)
        movements['!'] = lookup
        super().__init__(board, movements)
        self.lookup = lookup
        self.check_enemy = check_enemy

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        relay_target_dict = self.board.relay_targets.get(piece.side, {})
        relay_source_dict = self.board.relay_sources.get(piece.side, {})
        tester = copy(piece)
        tester.blocked_by = lambda p: False
        tester.captures = lambda p: p.side
        lookup_result = set()
        for lookup in self.lookup:
            lookup_dict = relay_target_dict.setdefault(lookup, {})
            if pos_from not in lookup_dict:
                lookup_dict[pos_from] = set()
                for move in lookup.moves(pos_from, tester, theoretical):
                    lookup_dict[pos_from].add(move.pos_to)
                    relay_source_dict.setdefault(move.pos_to, {}).setdefault(lookup, set()).add(pos_from)
            lookup_result.update(lookup_dict[pos_from])
        for key in self.movement_dict:
            if key == '!':
                continue
            value, invert = (key[1:], True) if key.startswith('!') else (key, False)
            movements = self.movement_dict[key]
            is_relayed = False
            if not key:
                mark = None
                is_relayed = True
            else:
                mark = 'r!' if invert else 'r'
                for pos in lookup_result:
                    relay_piece = self.board.get_piece(pos)
                    if (
                        (self.check_enemy < 0 or bool(self.check_enemy) != bool(piece.friendly_to(relay_piece)))
                        and self.board.fits(value, relay_piece)
                    ):
                        is_relayed = True
                        break
            is_legal = is_relayed != invert
            if not theoretical and not is_legal:
                continue
            for movement in movements:
                for move in movement.moves(pos_from, piece, theoretical):
                    yield copy(move) if not mark else copy(move).set(is_legal=is_legal).unmark('n').mark(mark)

    def __copy_args__(self):
        return (
            self.board,
            unpack(self.lookup),
            {key: unpack(value) for key, value in self.movement_dict.items() if key != '!'},
            self.check_enemy,
        )


class CoordinateMovement(BaseChoiceMovement):
    def __init__(
        self, board: Board,
        movement: Unpacked[BaseMovement] | None = None,
        lookup: Unpacked[BaseMovement | str] | None = None,
        coordination: dict[str, Unpacked[tuple[BaseMovement, BaseMovement]]] | None = None
    ):
        if coordination is None:
            coordination = {}
        movement = repack(movement or [], list)
        lookup = repack(lookup or [], list)
        to_movement = lambda x: AbsoluteMovement(board, x) if isinstance(x, str) else x
        lookup = [to_movement(x) for x in lookup]
        movement_dict: dict[str, Unpacked[BaseMovement | tuple[BaseMovement, BaseMovement]]] = {
            key: [tuple(x) for x in repack(value, list)] for key, value in coordination.items()
        }
        movement_dict[''] = movement
        movement_dict['!'] = lookup
        super().__init__(board, {
            key: list(chain.from_iterable(value)) if key not in '!' else value
            for key, value in movement_dict.items()
        })
        self.movement_dict = movement_dict
        self.movement = movement
        self.lookup = lookup

    def coordinate(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        relay_target_dict = self.board.relay_targets.get(piece.side, {})
        relay_source_dict = self.board.relay_sources.get(piece.side, {})
        coord_target_dict = self.board.coordinate_targets.get(piece.side, {})
        coord_source_dict = self.board.coordinate_sources.get(piece.side, {})
        tester = copy(piece)
        tester.blocked_by = lambda p: False
        tester.captures = lambda p: p.side
        lookup_result = set()
        for lookup in self.lookup:
            lookup_dict = relay_target_dict.setdefault(lookup, {})
            if pos_from not in lookup_dict:
                lookup_dict[pos_from] = set()
                for move in lookup.moves(pos_from, tester, theoretical):
                    lookup_dict[pos_from].add(move.pos_to)
                    relay_source_dict.setdefault(move.pos_to, {}).setdefault(lookup, set()).add(pos_from)
            lookup_result.update(lookup_dict[pos_from])
        tester.captures = lambda p: False
        coordinate_poss = set()
        for key in self.movement_dict:
            if key in '!':
                continue
            value, invert = (key[1:], True) if key.startswith('!') else (key, False)
            partners = []
            for pos in lookup_result:
                partner = self.board.get_piece(pos)
                if piece == partner or not partner.side:
                    continue
                if piece.friendly_to(partner) and self.board.fits(value, partner):
                    partners.append(partner)
                    if invert:
                        break
            if not theoretical and bool(partners) == invert:
                continue
            for movements in self.movement_dict[key]:
                partner_dict = coord_source_dict.setdefault(movements[1], {})
                def partner_moves():
                    for new_partner in partners:
                        partner_pos = new_partner.board_pos
                        if partner_pos in partner_dict:
                            yield from partner_dict[partner_pos]
                            continue
                        partner_dict[partner_pos] = set()
                        partner_tester = copy(new_partner)
                        partner_tester.blocked_by = lambda p: False
                        partner_tester.captures = lambda p: False
                        for partner_move in movements[1].moves(partner_pos, partner_tester, theoretical):
                            pos_to = partner_move.pos_to
                            partner_dict[partner_pos].add(pos_to)
                            coord_target_dict.setdefault(pos_to, {}).setdefault(movements[1], set()).add(partner_pos)
                            yield pos_to
                pos_generator = partner_moves()
                for move in movements[0].moves(pos_from, tester, theoretical):
                    if movements[1] in coord_target_dict.get(move.pos_to, {}):
                        is_legal = True
                    else:
                        is_legal = False
                        for pos in pos_generator:
                            if move.pos_to == pos:
                                is_legal = True
                                break
                    if is_legal:
                        coordinate_poss.add(move.pos_to)
                # finish generating partner moves
                for _ in pos_generator:
                    pass
        return coordinate_poss

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for movement in self.movement:
            for move in movement.moves(pos_from, piece, theoretical):
                move = copy(move).unmark('n').mark('q')
                if not theoretical:
                    move.set(captured=[
                        capture for x in self.coordinate(move.pos_to, piece, theoretical)
                        if piece.captures((capture := self.board.get_piece(x)))
                    ])
                yield move

    def __copy_args__(self):
        return (
            self.board,
            unpack(self.movement),
            unpack(self.lookup),
            {key: unpack(value) for key, value in self.movement_dict.items() if key not in '!'},
        )


class BaseAreaMovement(BaseMovement):
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
    @staticmethod
    def fits(template: str, tag: str) -> bool:
        template, invert = (template[1:], True) if template.startswith('!') else (template, False)
        return fits(template, tag) != invert

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        if theoretical:
            for movement in self.movements:
                for move in movement.moves(pos_from, piece, theoretical):
                    yield copy(move)
        else:
            for tag in self.movement_dict:
                if (
                    not self.board.ply_simulation and
                    not any(self.fits(template, tag or '') for template in self.board.move_tags)
                ):
                    continue
                for movement in self.movement_dict[tag]:
                    for move in movement.moves(pos_from, piece, theoretical):
                        if not tag:
                            yield copy(move)
                        else:
                            move = copy(move).set(tag=tag)
                            chained_move = move
                            while chained_move.chained_move and not chained_move.chained_move.tag:
                                chained_move = chained_move.chained_move.set(tag=tag)
                            yield move


class TagActMovement(AutoActMovement, TagMovement, BaseChainMovement):
    def __init__(
        self,
        board: Board,
        movements: dict[str, Unpacked[BaseMovement]] | None = None,
        actions: dict[str, Unpacked[AutoActMovement]] | None = None
    ):
        if movements is None:
            movements = {}
        if actions is None:
            actions = {}
        movement_dict = {key: repack(value, list) for key, value in movements.items()}
        action_dict = {key: repack(value, list) for key, value in actions.items()}
        super().__init__(board, {**movement_dict, **action_dict})
        self.movement_dict = movement_dict
        self.action_dict = action_dict

    def generate(self, move: Move, piece: Piece) -> Move:
        if move.is_edit:
            return move
        templates = [template for template in self.action_dict if self.fits(template or '', move.tag or '')]
        actions = [mv for tmpl in templates for mv in self.action_dict[tmpl] if isinstance(mv, AutoActMovement)]
        if not actions:
            return move
        promotion_piece = self.board.promotion_piece
        move_chain = self.expand(move)
        first_pos = move_chain[0].pos_from
        last_pos = self.advance(move_chain, bool(promotion_piece))
        full_move = Move(
            pos_from=first_pos,
            pos_to=last_pos,
            piece=piece,
        )
        delta_chain = []
        for movement in actions:
            self.advance(delta_chain)
            move_chain += delta_chain
            delta_chain = self.expand(movement.generate(copy(full_move), piece).chained_move)
        move = self.contract(move_chain + delta_chain)
        self.rollback(move_chain, bool(promotion_piece))
        self.board.promotion_piece = promotion_piece
        return move

    def moves(self, pos_from: Position, piece: Piece, theoretical: bool = False):
        for move in super().moves(pos_from, piece, theoretical):
            yield move if theoretical else self.generate(move, piece)

    def __copy_args__(self):
        return (
            self.board,
            {key: unpack(value) for key, value in self.movement_dict.items()},
            {key: unpack(value) for key, value in self.action_dict.items()},
        )


class ImitatorMovement(ChangingMovement):
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
    AutoActMovement,
)

is_active = lambda move: (
    move and not move.is_edit and move.pos_from and move.pos_to and
    (move.pos_from != move.pos_to or move.movement_type and not issubclass(move.movement_type, passive_movements))
)
