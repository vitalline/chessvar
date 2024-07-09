from __future__ import annotations

from importlib import import_module
from random import Random
from typing import TYPE_CHECKING, Type

from chess.movement.move import Move
from chess.movement.util import to_alpha as toa, from_alpha as fra
from chess.pieces import pieces as abc
from chess.pieces.groups.util import NoPiece
from chess.util import Unset

if TYPE_CHECKING:
    from chess.board import Board


UNSET_STRING = '*'


def save_type(piece_type: Type[abc.Piece] | frozenset | None) -> dict | str | None:
    if piece_type is None:
        return None
    if piece_type is Unset:
        return UNSET_STRING
    return {
        'module': piece_type.__module__.rsplit('.', 1)[-1],
        'class': piece_type.__name__,
    }


def load_type(data: dict | str | None) -> Type[abc.Piece] | frozenset | None:
    if data is None:
        return None
    if data == UNSET_STRING:
        return Unset
    return getattr(import_module(f"chess.pieces.groups.{data['module']}"), data['class'])


def save_piece(piece: abc.Piece | frozenset | None) -> dict | str | None:
    if piece is None:
        return None
    if piece is Unset:
        return UNSET_STRING
    if isinstance(piece, NoPiece):
        return toa(piece.board_pos) if piece.board_pos else None
    return {k: v for k, v in {
        **save_type(type(piece)),
        'pos': toa(piece.board_pos) if piece.board_pos else None,
        'side': piece.side.value,
        'moves': piece.movement.total_moves,
        'show': True if piece.is_hidden is False else None,
    }.items() if v}


def load_piece(data: dict | str | None, board: Board) -> abc.Piece | frozenset | None:
    if data is None:
        return None
    if data == UNSET_STRING:
        return Unset
    if isinstance(data, str):
        return NoPiece(board, fra(data))
    side = abc.Side(data.get('side', 0))
    piece = load_type(data)(
        board=board,
        board_pos=fra(data['pos']) if 'pos' in data else None,  # type: ignore
        side=side,
        promotions=board.promotions.get(side),
        promotion_squares=board.promotion_squares.get(side),
    )
    piece.is_hidden = False if data.get('show') is True else None
    piece.movement.set_moves(data.get('moves', 0))
    piece.scale = board.square_size / piece.texture.width
    if not piece.is_empty():
        board.update_piece(piece)
    return piece


def save_move(move: Move | frozenset | None) -> dict | str | None:
    if move is None:
        return None
    if move is Unset:
        return UNSET_STRING
    return {k: v for k, v in {
        'from': toa(move.pos_from) if move.pos_from else None,
        'to': toa(move.pos_to) if move.pos_to else None,
        'type': move.movement_type.__name__ if move.movement_type is not None else None,
        'piece': save_piece(move.piece),
        'captured': save_piece(move.captured_piece),
        'swapped': save_piece(move.swapped_piece),
        'promotion': save_piece(move.promotion),
        'chain': save_move(move.chained_move),
        'edit': move.is_edit,
    }.items() if v}


def load_move(data: dict | str | None, board: Board) -> Move | frozenset | None:
    if data is None:
        return None
    if data == UNSET_STRING:
        return Unset
    return Move(
        pos_from=fra(data['from']) if 'from' in data else None,  # type: ignore
        pos_to=fra(data['to']) if 'to' in data else None,  # type: ignore
        movement_type=getattr(import_module('chess.movement.movement'), data['type']) if 'type' in data else None,
        piece=load_piece(data.get('piece'), board),
        captured_piece=load_piece(data.get('captured'), board),
        swapped_piece=load_piece(data.get('swapped'), board),
        promotion=load_piece(data.get('promotion'), board),
        chained_move=load_move(data.get('chain'), board),
        is_edit=data.get('edit', False),
    )


def save_rng(rng: Random) -> list:
    state = rng.getstate()
    return [state[0], list(state[1]), state[2]]


def load_rng(data: list) -> Random:
    state = data[0], tuple(data[1]), data[2]
    rng = Random()
    rng.setstate(state)
    return rng
