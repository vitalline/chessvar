from __future__ import annotations

from typing import TYPE_CHECKING

from chess.movement.base import *

if TYPE_CHECKING:
    from chess.board import Board

movement_settings = [
    (RiderMovement, direction) for direction in Directions
]


def get_movements(board: Board):
    return gen_movements(board, movement_settings)

