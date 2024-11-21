from __future__ import annotations

from base64 import b64decode, b64encode
from copy import copy
from importlib import import_module
from random import Random
from traceback import print_exc
from typing import TYPE_CHECKING, Any
from warnings import warn

from chess.movement import types as movement_types
from chess.movement.base import BaseMovement
from chess.movement.move import Move
from chess.movement.util import LAST, Position, sort_key
from chess.movement.util import to_algebraic as toa, from_algebraic as fra
from chess.movement.util import to_algebraic_map as tom, from_algebraic_map as frm
from chess.pieces import types as piece_types
from chess.pieces.piece import AbstractPiece, Piece
from chess.pieces.side import Side
from chess.pieces.types import Neutral
from chess.pieces.util import UtilityPiece, NoPiece
from chess.util import CUSTOM_PREFIX, MOVEMENT_SUFFIXES, UNSET_STRING, Unset, AnyJson, AnyJsonType, IntIndex, TypeOr

if TYPE_CHECKING:
    from chess.board import Board

TYPE_CONFLICTS = {
    x: s for s in (map(frozenset, (
        (piece_types.Delayed, piece_types.Delayed1),
        (piece_types.Double, piece_types.Enemy),
    ))) for x in s
}


def make_tuple(thing: AnyJson) -> tuple | AnyJsonType:
    if isinstance(thing, dict):
        return tuple((k, make_tuple(thing[k])) for k in thing)
    if isinstance(thing, list):
        return tuple(make_tuple(x) for x in thing)
    return thing


def condense(data: AnyJson, alias_dict: dict, recursive: bool = False) -> AnyJson:
    tuple_dict = {make_tuple(v): k for k, v in alias_dict.items()}

    def find_alias(thing: AnyJson, tuple_thing: tuple | AnyJsonType) -> AnyJson:
        if tuple_thing in tuple_dict:
            return tuple_dict[tuple_thing]
        if isinstance(thing, dict):
            return {tuple_dict.get(k, k): find_alias(thing[k], v) for k, v in tuple_thing}
        if isinstance(thing, list):
            return [find_alias(x, tx) for x, tx in zip(thing, tuple_thing)]
        return thing

    old_data = None
    while old_data != data:
        old_data, data = data, find_alias(data, make_tuple(data))
        if not recursive:
            break
    return data


def expand(data: AnyJson, alias_dict: dict, recursive: bool = False) -> AnyJson:
    if recursive:
        old_data = None
        while old_data != data:
            old_data, data = data, expand(data, alias_dict)
        return data
    if isinstance(data, dict):
        return {alias_dict.get(k, k): expand(v, alias_dict) for k, v in data.items()}
    if isinstance(data, list):
        return [expand(x, alias_dict) for x in data]
    if isinstance(data, str) and data in alias_dict:
        return alias_dict[data]
    return data


def condense_algebraic(
    data: dict[Position, AnyJson],
    width: int,
    height: int,
    x_offset: int,
    y_offset: int,
    areas: dict[str, set[Position]],
) -> dict[str, AnyJson]:
    data_groups = {}
    for key, value in data.items():
        data_groups.setdefault(make_tuple(value), set()).add(key)
    result = {}
    for group in data_groups.values():
        mapping = tom(list(group), width, height, x_offset, y_offset, areas)
        for notation, poss in mapping.items():
            if not poss:
                continue
            value = data[poss[0]]
            for pos in poss[1:]:
                if data[pos] != value:
                    for pos2 in poss:
                        result[toa(pos2)] = data[pos2]
                    break
            else:
                result[notation] = value
    return {k: result[k] for k in sorted(result, key=lambda s: sort_key(s if s in areas else fra(s)))}


def expand_algebraic(
    data: dict[str, AnyJson],
    width: int,
    height: int,
    x_offset: int,
    y_offset: int,
    areas: dict[str, set[Position]],
) -> dict[Position, AnyJson]:
    mapping = frm(list(data), width, height, x_offset, y_offset, areas)
    result = {}
    for pos, notation in mapping.items():
        result[pos] = copy(data[notation])
    return result


def substitute(data: AnyJson, subs: IntIndex | dict[int, IntIndex], side: Side = Side.NONE) -> AnyJson:
    result = data
    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            try:
                result[k] = substitute(v, subs, Side(int(k)))
            except ValueError:
                result[substitute(k, subs, side)] = substitute(v, subs, side)
    if isinstance(data, list):
        result = [substitute(x, subs, side) for x in data]
    if isinstance(data, str):
        start = data.find('{')
        if start != -1:
            end = data.find('}', start)
            if end != -1:
                key = data[start + 1 : end].split(':', 1)
                try:
                    key = [int(v) for v in key]
                    if isinstance(subs, list) and len(key) == 1:
                        result = subs[key[0]]
                    elif isinstance(subs, dict) and len(key) == 1:
                        result = subs[side.value()][key[0]]
                    elif isinstance(subs, dict) and len(key) == 2:
                        result = subs[key[0]][key[1]]
                    result = data[:start] + result + substitute(data[end + 1:], subs, side)
                except (ValueError, IndexError, KeyError):
                    pass
    return result


def save_piece_type(
    piece_type: type[AbstractPiece] | frozenset | None,
    last: type[AbstractPiece] | None = None,
) -> str | None:
    if piece_type is None:
        return None
    if piece_type is Unset:
        return UNSET_STRING
    if piece_type is last:
        return LAST
    return piece_type.type_str()


def load_piece_type(
    data: str | None,
    from_dict: dict | None = None,
    last: str | None = None,
) -> type[AbstractPiece] | frozenset | None:
    if not data:
        return None
    if data == UNSET_STRING:
        return Unset
    if data == LAST:
        return load_piece_type(last, from_dict)
    if from_dict and data in from_dict:
        return from_dict[data]
    parts = data.split('.', 1)
    module_path = f"chess.pieces.groups.{parts[0]}" if len(parts) > 1 else f"chess.pieces.util"
    try:
        return getattr(import_module(module_path), parts[-1])
    except (AttributeError, ImportError, IndexError):
        return None


def save_movement_type(movement_type: type[BaseMovement] | frozenset | None) -> list | str | None:
    if movement_type is None:
        return None
    if movement_type is Unset:
        return UNSET_STRING
    if movement_types.__name__.startswith(CUSTOM_PREFIX):
        return save_custom_movement_type(movement_type)
    return movement_type.type_str()


def load_movement_type(data: list | str | None) -> type[BaseMovement] | frozenset | None:
    if not data:
        return None
    if data == UNSET_STRING:
        return Unset
    if isinstance(data, list):
        bases = {}
        for x in data:
            if base := load_movement_type(x):
                name = base.__name__
                if name.startswith(CUSTOM_PREFIX):
                    name = name.removeprefix('_')
                bases[name] = base
            else:
                return None
        return load_custom_movement_type(bases)
    if isinstance(data, str):
        for i in range(len(MOVEMENT_SUFFIXES) + 1):
            name = data + ''.join(MOVEMENT_SUFFIXES[:i][::-1])
            movement_type = getattr(movement_types, name, None)
            if movement_type:
                return movement_type
    return None


def save_piece(
    piece: AbstractPiece | frozenset | None,
    last: type[AbstractPiece] | None = None,
) -> dict | str | None:
    if piece is None:
        return None
    if piece is Unset:
        return UNSET_STRING
    if isinstance(piece, NoPiece):
        return toa(piece.board_pos) if piece.board_pos else None
    return {k: v for k, v in {
        'cls': save_piece_type(type(piece), last),
        'pos': toa(piece.board_pos) if piece.board_pos else None,
        'side': (
            piece.side.value if not isinstance(piece, Neutral)
            and not (isinstance(piece, UtilityPiece) and piece.side == piece.default_side) else None
        ),
        'from': save_piece_type(piece.promoted_from, last) if piece.promoted_from else None,
        'moves': piece.movement.total_moves if piece.movement else None,
        'show': None if isinstance(piece, UtilityPiece) or piece.should_hide is None else not piece.should_hide,
    }.items() if v or (k == 'show' and v is False)}


def load_piece(
    board: Board,
    data: dict | str | None,
    from_dict: dict | None = None,
    last: str | None = None,
) -> AbstractPiece | frozenset | None:
    if not data:
        return None
    if data == UNSET_STRING:
        return Unset
    if isinstance(data, str):
        return NoPiece(board, board_pos=fra(data))
    side = Side(data.get('side', 0))
    piece_type = load_piece_type(data.get('cls'), from_dict, last) or NoPiece
    piece = piece_type(
        board=board,
        board_pos=fra(data['pos']) if 'pos' in data else None,  # type: ignore
        side=side,
    )
    piece.promoted_from = load_piece_type(data.get('from'), from_dict, last)
    if piece.movement:
        piece.movement.set_moves(data.get('moves', 0))
    if isinstance(piece, Piece):
        show_piece = data.get('show')
        if show_piece is not None:
            piece.is_hidden = piece.should_hide = not show_piece
        piece.sprite.scale = board.square_size / piece.sprite.texture.width
        if not isinstance(piece, NoPiece):
            board.update_piece(piece)
    return piece


def save_custom_movement_type(movement: type[BaseMovement]) -> list[str]:
    return [save_movement_type(base) for base in movement.__bases__ if issubclass(base, BaseMovement)]


def load_custom_movement_type(bases: dict[str, type[BaseMovement]]) -> type[BaseMovement]:
    if len(bases) == 1:
        return list(bases.values())[0]
    # Here's the issue: moves have a movement_type attribute, which is used for direct comparisons. If we want to load a
    # multiclass movement type, it will not be equal to the original movement type, even if it is functionally the same.
    # A name-based comparison is used as a workaround when directly comparing moves, but who knows what else will break?
    name = CUSTOM_PREFIX + '_'.join(bases)
    bases = list(v for k, v in bases.items())
    return type(name, (*bases, BaseMovement), {})  # type: ignore


def save_movement(movement: BaseMovement | frozenset | None) -> list | str | None:
    def save_arg(arg: Any) -> Any:  # helper function for saving constructor arguments of a movement object:
        if isinstance(arg, BaseMovement):  # the movement here is made out of movement (Multi, Bent, others)
            return save_movement(arg)  # save the movement recursively. not the most efficient, but it works
        if isinstance(arg, list | tuple):  # is this a direction? a list of directions? a list of movements?
            if not arg:  # nope, this is an empty list. return it as is and don't bother with the rest of it
                return arg  # we don't need to do anything else here, just return the empty list (moving on)
            if isinstance(arg[0], int):  # this is a direction, a position, or another kind of numeric tuple
                return list(arg)  # it is important to preserve order here because directions have it fixed!
            if isinstance(arg[0], BaseMovement):  # this is a list of movements, so we save them recursively
                return [save_arg(x) for x in arg]  # no need to sort them, who knows what would that change?
            if isinstance(arg, tuple):  # tuples tend to be used for things that have order, like directions
                return [save_arg(x) for x in arg]  # if we sort them, that order is lost. we save them as is
            return sorted([save_arg(x) for x in arg])  # otherwise let's save the arguments in a sorted list
        if isinstance(arg, dict):  # support for saving dicts in movement arguments is a good thing to have.
            return {k: save_arg(v) for k, v in arg.items()}  # save them recursively. this is to be expected
        return arg  # if it's not a list, tuple, dict, or movement, it's probably a simple value. keep as is
    if movement is None:  # if the movement is None, return None. this is the only case where we return None
        return None  # if the movement is Unset (which I'm pretty sure it never is), return the UNSET_STRING
    if movement is Unset:  # otherwise, we need to return a list consisting of the movement type as a string
        return UNSET_STRING  # and the rest of the arguments saved as a list of arguments (using the helper)
    args = list(movement.__copy_args__()[1:])  # store arguments of the movement (except the board argument)
    while args and not args[-1]:  # movement classes have optional constructor args with falsy defaults that
        args.pop()  # aren't needed to reconstruct the movement, so we can remove the trailing ones and then
    return [save_movement_type(type(movement))] + [save_arg(arg) for arg in args]  # save the data as a list


def load_movement(board: Board, data: list | str | None, from_dict: dict | None) -> BaseMovement | frozenset | None:
    def load_arg(arg: Any) -> Any:  # the logic is slightly less complicated in this helper function but only slightly
        if isinstance(arg, list):  # it's a list, so it's either a direction, a movement, or a list of either of those
            if not arg:  # if it's empty, it's an empty list. duh. just return it as is, same as the last helper func.
                return arg  # it is the one case where we don't have to do anything. if only life was always this easy
            if isinstance(arg[0], str):  # if the first element is a string, it's a movement, so it needs to be loaded
                return load_movement(board, arg, from_dict)  # again, inefficient, but it certainly gets the job done.
            if isinstance(arg[0], int):  # if the first element is an integer, it's a direction. or a position, but eh
                return tuple(arg)  # so we return it as a tuple, because we use tuples for directions basically always
            return [load_arg(x) for x in arg]  # it's either a list of directions or a list of movements. recurse more
        if isinstance(arg, dict):  # oh hey, dicts are finally useful! hooray! but it means more work to be done here.
            return {k: load_arg(v) for k, v in arg.items()}  # and still as expected, load recursively, etc., whatever
        return arg  # if it's not a list or dict, it's probably a simple value. no need to do anything. just return it
    if data is None:  # if the data is None, return None. this is, of course, still the only case where we return None
        return None  # if the data is UNSET_STRING, return Unset. similarly, it is the only case where we return Unset
    if data == UNSET_STRING:  # otherwise, we need to load the movement type and the rest of the arguments, so that we
        return Unset  # can create a new instance of the movement type with the arguments we just loaded. very simple.
    bases, data_copy = {}, data.copy()  # oh boy, here comes the hard part. we need to load the movement classes first
    for i, base_string in enumerate(data):  # for every base class string or list that's at the start of the data list
        if base := load_movement_type(base_string):  # we need to load a movement class corresponding to the string or
            bases[base_string] = base  # list. but once we can't, we assume that all the movement classes have already
            data_copy.pop(i)  # been loaded and that the rest are arguments. so we remove the leading entries from the
        else:  # argument list until we encounter something that is not a base entry. that's when we know we are done,
            break  # and we can move on to loading the arguments. the bases are stored in a dict for easy access later
    args = board, *[load_arg(arg) for arg in data_copy]  # we need to load the arguments alongside the board object...
    return load_custom_movement_type(bases)(*args)  # and that's it. we are done. movement loaded successfully. maybe.


def save_custom_type(piece: TypeOr[AbstractPiece] | None) -> dict | None:
    if piece is None:
        return None
    piece, piece_type = (piece, type(piece)) if isinstance(piece, Piece) else (None, piece)
    if not issubclass(piece_type, Piece):
        return None
    bases = [base.__name__ for base in piece_type.__bases__ if base.__module__ == piece_types.__name__]
    if len(bases) == 1:
        bases = bases[0]
    return {k: v for k, v in {
        'cls': bases,
        'name': piece_type.name,
        'file': piece_type.file_name,
        'path': piece_type.asset_folder,
        'cb': piece_type.is_colorbound(),
        'movement': getattr(piece_type, 'movement_data', save_movement(piece.movement if piece else None)),
    }.items() if v}


def load_custom_type(data: dict | None, name: str) -> type[AbstractPiece] | None:
    if not data:
        return None
    base_strings = data.get('cls', ())
    if isinstance(base_strings, str):
        base_strings = [base_strings]
    base_set = set()
    bases = [Piece]
    for base_string in base_strings:
        base = getattr(piece_types, base_string, None)
        if base and base not in base_set and not base_set.intersection(TYPE_CONFLICTS.get(base, ())):
            base_set.add(base)
            bases.append(base)
    args = {}
    if 'name' in data:
        args['name'] = data['name']
    if 'file' in data:
        args['file_name'] = data['file']
    if 'path' in data:
        args['asset_folder'] = data['path']
    if 'cb' in data:
        args['colorbound'] = data['cb']
    if 'movement' in data:
        args['movement_data'] = data['movement']
    cls = type(CUSTOM_PREFIX + name, tuple(bases), args)

    def init(self, board, **kwargs):
        bases[0].__init__(
            self, board,
            load_movement(board, getattr(self, 'movement_data', None), board.custom_pieces),
            **kwargs
        )

    cls.__init__ = init
    return cls  # type: ignore


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
        'type': save_movement_type(move.movement_type),
        'piece': save_piece(piece),
        'captured': save_piece(capture),
        'swapped': save_piece(swapped),
        'drop': save_piece_type(move.placed_piece),
        'promotion': save_piece(promotion),
        'chain': save_move(move.chained_move),
        'edit': move.is_edit,
        'tag': move.tag,
    }.items() if v}


def load_move(board: Board, data: dict | str | None, from_dict: dict | None) -> Move | frozenset | None:
    if not data:
        return None
    if data == UNSET_STRING:
        return Unset
    pos_from = fra(data['from']) if 'from' in data else None
    pos_to = fra(data['to']) if 'to' in data else None
    piece = load_piece(board, data.get('piece'), from_dict)
    if not piece:
        piece = NoPiece(board, board_pos=pos_to or pos_from)
    elif not piece.board_pos:
        piece.board_pos = pos_to or pos_from
    capture = load_piece(board, data.get('captured'), from_dict)
    if capture and not capture.board_pos:
        capture.board_pos = pos_to
    swapped = load_piece(board, data.get('swapped'), from_dict)
    if swapped and not swapped.board_pos:
        swapped.board_pos = pos_from
    return Move(
        pos_from=pos_from,
        pos_to=pos_to,
        movement_type=load_movement_type(data.get('type')),
        piece=piece,
        captured_piece=capture,
        swapped_piece=swapped,
        placed_piece=load_piece_type(data.get('drop'), from_dict),
        promotion=load_piece(board, data.get('promotion'), from_dict),
        chained_move=load_move(board, data.get('chain'), from_dict),
        is_edit=data.get('edit', 0),
        tag=data.get('tag', None),
    )


def save_rng(rng: Random) -> list:
    state = rng.getstate()
    # noinspection PyBroadException
    try:  # compress the state of a version 3 random number generator using base64 encoding for the data
        data = bytearray(x for i in state[1][:-1] for x in i.to_bytes(4, signed=False, byteorder='big'))
        return [state[0], b64encode(data).decode(), state[1][-1], state[2]]
    except Exception:  # but just in case something goes wrong, here is a fallback that returns the state as a list
        warn('Failed to compress random number generator state. Falling back to uncompressed state.')
        print_exc()
        return [state[0], list(state[1]), state[2]]


def load_rng(data: list) -> Random:
    if isinstance(data[1], str):
        arr = b64decode(data[1])  # assuming compressed data, do the inverse of the save_rng function
        tup = (*(int.from_bytes(arr[i:i + 4], signed=False, byteorder='big') for i in range(0, len(arr), 4)), data[2])
        state = (data[0], tup, data[3])
    else:  # assuming fallback, load the state as is
        state = (data[0], tuple(data[1]), data[2])
    rng = Random()
    rng.setstate(state)
    return rng
