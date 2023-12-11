from __future__ import annotations

from typing import TYPE_CHECKING

from chess.movement.util import Position

if TYPE_CHECKING:
    from chess.movement.movement import BaseMovement
    from chess.pieces.piece import Piece


class Move(object):
    def __init__(self, piece: Piece, pos_from: Position, pos_to: Position, movement: BaseMovement | None = None):
        self.piece = piece
        self.pos_from = pos_from
        self.pos_to = pos_to
        self.movement = movement
