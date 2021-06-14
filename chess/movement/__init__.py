from __future__ import annotations

from typing import TYPE_CHECKING

from chess.movement.base import *

if TYPE_CHECKING:
    from chess.board import Board

# movement_settings = [(RiderMovement, direction.value) for direction in Directions if direction.value != []]
movement_settings = [(RiderMovement, direction) for direction in rng_directions() if direction != []]


def get_movements(board: Board):
    return gen_movements(board, movement_settings)

