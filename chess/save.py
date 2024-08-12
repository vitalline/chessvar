from __future__ import annotations

from base64 import b64decode, b64encode
from importlib import import_module
from random import Random
from typing import TYPE_CHECKING, Type

from chess.movement.move import Move
from chess.movement.movement import BaseMovement
from chess.movement.util import to_alpha as toa, from_alpha as fra
from chess.pieces import pieces as abc
from chess.pieces.groups.util import NoPiece
from chess.util import Unset

if TYPE_CHECKING:
    from chess.board import Board


UNSET_STRING = '*'

SUFFIXES = ('Movement', 'Rider')


def save_type(piece_type: Type[abc.Piece] | frozenset | None) -> str | None:
    if piece_type is None:
        return None
    if piece_type is Unset:
        return UNSET_STRING
    return f"{piece_type.__module__.rsplit('.', 1)[-1]}.{piece_type.__name__}"


def load_type(data: str | None) -> Type[abc.Piece] | frozenset | None:
    if data is None:
        return None
    if data == UNSET_STRING:
        return Unset
    mod, cls = data.split('.', 1)
    return getattr(import_module(f"chess.pieces.groups.{mod}"), cls)


def save_movement(movement_type: Type[BaseMovement] | frozenset | None) -> str | None:
    if movement_type is None:
        return None
    if movement_type is Unset:
        return UNSET_STRING
    name = movement_type.__name__
    for suffix in SUFFIXES:
        if name.endswith(suffix, 1):
            name = name[:-len(suffix)]
    return name


def load_movement(data: str | None) -> Type[BaseMovement] | frozenset | None:
    if data is None:
        return None
    if data == UNSET_STRING:
        return Unset
    for i in range(len(SUFFIXES) + 1):
        name = data + ''.join(SUFFIXES[:i][::-1])
        movement_type = getattr(import_module('chess.movement.movement'), name, None)
        if movement_type:
            return movement_type
    return None


def save_piece(piece: abc.Piece | frozenset | None) -> dict | str | None:
    if piece is None:
        return None
    if piece is Unset:
        return UNSET_STRING
    if isinstance(piece, NoPiece):
        return toa(piece.board_pos) if piece.board_pos else None
    return {k: v for k, v in {
        'cls': save_type(type(piece)),
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
    piece_type = load_type(data.get('cls')) or NoPiece
    piece = piece_type(
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
    piece = move.piece
    if piece and (piece.board_pos == (move.pos_to or move.pos_from)):
        piece = piece.on(None)
    capture = move.captured_piece
    if capture and (capture.board_pos == move.pos_to):
        capture = capture.on(None)
    swapped = move.swapped_piece
    if swapped and (swapped.board_pos == move.pos_from):
        swapped = swapped.on(None)
    promotion = move.promotion
    if promotion:
        promotion = promotion.on(None)
    return {k: v for k, v in {
        'from': toa(move.pos_from) if move.pos_from else None,
        'to': toa(move.pos_to) if move.pos_to else None,
        'type': save_movement(move.movement_type),
        'piece': save_piece(piece),
        'captured': save_piece(capture),
        'swapped': save_piece(swapped),
        'promotion': save_piece(promotion),
        'chain': save_move(move.chained_move),
        'edit': move.is_edit,
    }.items() if v}


def load_move(data: dict | str | None, board: Board) -> Move | frozenset | None:
    if data is None:
        return None
    if data == UNSET_STRING:
        return Unset
    pos_from = fra(data['from']) if 'from' in data else None
    pos_to = fra(data['to']) if 'to' in data else None
    piece = load_piece(data.get('piece'), board)
    if piece and not piece.board_pos:
        piece.board_pos = pos_to or pos_from
    capture = load_piece(data.get('captured'), board)
    if capture and not capture.board_pos:
        capture.board_pos = pos_to
    swapped = load_piece(data.get('swapped'), board)
    if swapped and not swapped.board_pos:
        swapped.board_pos = pos_from
    return Move(
        pos_from=pos_from,
        pos_to=pos_to,
        movement_type=load_movement(data.get('type')),
        piece=piece,
        captured_piece=capture,
        swapped_piece=swapped,
        promotion=load_piece(data.get('promotion'), board),
        chained_move=load_move(data.get('chain'), board),
        is_edit=data.get('edit', False),
    )


def save_rng(rng: Random) -> list:
    state = rng.getstate()
    data = bytearray(x for i in state[1][:-1] for x in i.to_bytes(4, signed=False, byteorder='big'))
    return [state[0], b64encode(data).decode(), state[1][-1], state[2]]


def load_rng(data: list) -> Random:
    arr = b64decode(data[1])
    tup = (*(int.from_bytes(arr[i:i + 4], signed=False, byteorder='big') for i in range(0, len(arr), 4)), data[2])
    state = (data[0], tup, data[3])
    rng = Random()
    rng.setstate(state)
    return rng
