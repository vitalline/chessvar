from __future__ import annotations

import sys

from copy import deepcopy
from typing import TYPE_CHECKING, TextIO

from chess.data import get_piece_types, get_set_data, get_set_name, piece_groups
from chess.data import action_types, end_types, prefix_chars, prefix_types, type_prefixes
from chess.movement.move import Move
from chess.movement.types import DropMovement
from chess.movement.util import ANY, to_alpha as b26
from chess.movement.util import to_algebraic as toa, from_algebraic as fra
from chess.movement.util import to_algebraic_map as tom, from_algebraic_map as frm
from chess.pieces.groups.classic import Pawn
from chess.pieces.piece import AbstractPiece, Piece
from chess.pieces.side import Side
from chess.pieces.types import Neutral
from chess.pieces.util import UtilityPiece, NoPiece, Block, Border, Shield, Void, Wall
from chess.save import save_piece_type, save_custom_type
from chess.util import TypeOr, dumps, get_file_path, pluralize, spell, spell_ordinal, sign

if TYPE_CHECKING:
    from chess.board import Board


def get_piece_mapping(board: Board, side: Side = Side.WHITE) -> dict[str, list[str]]:
    mapping = {}
    set_mapping = {}
    defaults = {}
    def add_piece(piece: type[AbstractPiece], default: bool = False):
        piece_type = save_piece_type(piece)
        if piece_type not in set_mapping.setdefault(piece.name, set()):
            set_mapping[piece.name].add(piece_type)
            mapping.setdefault(piece.name, []).append(piece_type)
            if piece.name not in defaults:
                if default and len(set_mapping[piece.name]) == 1:
                    defaults[piece.name] = piece_type
                if not default and len(set_mapping[piece.name]) > 1:
                    mapping[piece.name] = [None] + mapping[piece.name]
    custom_piece_names = [piece.name for piece in board.custom_pieces.values()]
    custom_piece_name_counts = {}
    for name in custom_piece_names:
        custom_piece_name_counts[name] = custom_piece_name_counts.get(name, 0) + 1
    for side in (side, side.opponent()):
        for new_piece in board.piece_sets.get(side, []):
            add_piece(new_piece, custom_piece_name_counts.get(new_piece.name, 1) == 1)
        pawns = board.custom_pawns if board.custom_pawns is not None else [Pawn]
        for new_piece in (pawns.get(side, []) if isinstance(pawns, dict) else pawns):
            add_piece(new_piece, custom_piece_name_counts.get(new_piece.name, 1) == 1)
    for _, new_piece in board.custom_pieces.items():
        add_piece(new_piece)
    for piece_set_id in range(len(piece_groups)):
        for new_piece in get_set_data(side, piece_set_id):
            add_piece(new_piece)
    for new_piece in [Block, Border, Shield, Void, Wall]:
        add_piece(new_piece)
    for _, new_piece in board.past_custom_pieces.items():
        add_piece(new_piece)
    return mapping


def get_piece_name(piece: TypeOr[AbstractPiece], mapping: dict[str, list[str]]) -> str:
    name = piece.name
    if len(mapping.get(name, ())) <= 1:
        return name
    piece_type = save_piece_type(piece)
    if piece_type == mapping[name][0]:
        return name
    return f"{name} ({save_piece_type(piece)})"


def print_piece_data(board: Board, fp: TextIO = sys.stdout, side: Side = Side.WHITE) -> None:
    fp.write('{\n')
    for i, t in enumerate(sorted(get_piece_types(side), key=lambda x: save_piece_type(x))):
        if i:
            fp.write(',\n')
        fp.write(f'  "{save_piece_type(t)}":')
        p = t(board=board, side=side)
        fp.write(dumps(save_custom_type(p), separators=(',', ':'), ensure_ascii=False))
    fp.write('\n}')


def print_piece_sets(fp: TextIO = sys.stdout) -> None:
    piece_types = get_piece_types()
    digits = len(str(len(piece_groups)))
    for i, group in enumerate(piece_groups):
        for side, piece_set in (
            [(Side.NONE, group['set'])] if 'set' in group else
            [(side, group[f"set_{side.key()[0]}"]) for side in (Side.WHITE, Side.BLACK)]
        ):
            name = group['name'] + (f" - {side}" if side else '')
            fp.write(f"ID {i:0{digits}d}{side.key()[:1]}: {name} {get_set_name(piece_set)}\n")
            fp.write(f"  [{', '.join(piece_types[piece] for piece in piece_set)}]\n")
            fp.write(f"  <{', '.join(save_piece_type(piece) for piece in piece_set)}>\n")


def print_piece_types(fp: TextIO = sys.stdout, side: Side = Side.WHITE) -> None:
    for name, path, file in sorted(
        (n, save_piece_type(t), (t.file_name if issubclass(t, Piece) else '')) for t, n in get_piece_types(side).items()
    ):
        fp.write(f"{name}: {path}, {file}\n")


def save_piece_data(board: Board, file_path: str = None) -> str:
    file_path = file_path or get_file_path('debug_piece_data', 'json', ts_format='')
    with open(file_path, mode='w', encoding='utf-8') as fp:
        print_piece_data(board, fp)
    return file_path


def save_piece_sets(file_path: str = None) -> str:
    file_path = file_path or get_file_path('debug_piece_sets', 'log', ts_format='')
    with open(file_path, mode='w', encoding='utf-8') as fp:
        print_piece_sets(fp)
    return file_path


def save_piece_types(file_path: str = None, side: Side = Side.WHITE) -> str:
    file_path = file_path or get_file_path('debug_piece_types', 'log', ts_format='')
    with open(file_path, mode='w', encoding='utf-8') as fp:
        print_piece_types(fp, side)
    return file_path


def debug_info(board: Board) -> list[str]:
    pad = ''
    s26 = lambda x: b26(x + (0 if x < 0 else 1))
    offset_x, offset_y = board.notation_offset
    mapping = {side: get_piece_mapping(board, side) for side in (Side.WHITE, Side.BLACK, Side.NONE)}
    piece_side = lambda piece: piece.side if isinstance(piece, AbstractPiece) else Side.NONE
    def name(piece: TypeOr[AbstractPiece], side: Side = Side.NONE):
        if not piece or isinstance(piece, NoPiece) or isinstance(piece, type) and issubclass(piece, NoPiece):
            return 'None'
        return get_piece_name(piece, mapping.get(piece_side(piece) or side, mapping.get(side, mapping[Side.NONE])))
    debug_log = []  # noqa
    debug_log.append(f"Board size: {board.board_width}x{board.board_height}")
    if offset_x or offset_y:
        debug_log.append(f"Notation offset: {', '.join(f'{x:+}' if x else '0' for x in board.notation_offset)}")
    else:
        debug_log.append("Notation offset: None")
    debug_log.append("Borders:")
    if board.border_cols or board.border_rows:
        if board.border_cols:
            file_splits = list(f'{s26(x)}/{s26(x + 1)}' for x in board.border_cols)
            debug_log.append(f"{pad:2}File ({len(file_splits)}): {', '.join(file_splits)} {tuple(board.border_cols)}")
        else:
            debug_log.append(f"{pad:2}File (0): None")
        if board.border_rows:
            rank_splits = list(f'{x}/{x + 1}' for x in board.border_rows)
            debug_log.append(f"{pad:2}Rank ({len(rank_splits)}): {', '.join(rank_splits)} {tuple(board.border_rows)}")
        else:
            debug_log.append(f"{pad:2}Rank (0): None")
    else:
        debug_log[-1] += " None"
    debug_log.append(f"Visual board size: {board.visual_board_width}x{board.visual_board_height}")
    debug_log.append(f"Screen size: {board.width}x{board.height}")
    debug_log.append(f"Square size: {board.square_size}")
    debug_log.append(f"Windowed screen size: {board.windowed_size[0]}x{board.windowed_size[1]}")
    debug_log.append(f"Windowed square size: {board.windowed_square_size}")
    debug_log.append(f"Color scheme ID: {'-' if board.color_index is None else board.color_index}")
    debug_log.append("Color scheme:")
    color_scheme = deepcopy(board.color_scheme)  # just in case trickster mode messes with the color scheme RIGHT NOW
    for k, v in color_scheme.items():
        debug_log.append(f"{pad:2}{k} = {v}")
    debug_log.append(f"Piece sets ({len(piece_groups)}):")
    digits = len(str(len(piece_groups)))
    for i, group in enumerate(piece_groups):
        debug_log.append(f"{pad:2}ID {i:0{digits}d}: {group['name']}")
    for i in sorted(board.chaos_sets):
        debug_log.append(f"{pad:2}ID {-i:0{digits}d}: {board.chaos_sets[i][1]}")
    for section_type, section_data in (
        ("ID", board.board_config['block_ids']),
        ("Chaos ID", board.board_config['block_ids_chaos']),
    ):
        strings = ', '.join(f"{i:0{digits}d}" for i in section_data)
        debug_log.append(f"{section_type} blocklist ({len(section_data)}): {strings or 'None'}")
    debug_log.append(f"Variant: {board.custom_variant or board.variant or 'None'}")
    if board.custom_variant:
        debug_log[-1] += " (Custom)"
    side_id_strings = {
        side: '-' if set_id is None else f"{set_id:0{digits}d}"
        for side, set_id in board.piece_set_ids.items()
    }
    debug_log.append(
        f"Game: "
        f"(ID {side_id_strings[Side.WHITE]}) {board.piece_set_names[Side.WHITE]} vs. "
        f"(ID {side_id_strings[Side.BLACK]}) {board.piece_set_names[Side.BLACK]}"
    )
    for side in board.piece_set_ids:
        debug_log.append(f"{side} setup: {', '.join(name(piece, side) for piece in board.piece_sets[side])}")
    debug_log.append(f"Piece groups ({len(board.piece_groups)}):")
    for group in board.piece_groups:
        group_string = ', '.join(name(piece) for piece in board.piece_groups[group])
        debug_log.append(f"{pad:2}{group} ({len(board.piece_groups[group])}): {group_string or 'None'}")
    if not board.piece_groups:
        debug_log[-1] += " None"
    debug_log.append(f"Obstacles ({len(board.obstacles)}):")
    for piece in board.obstacles:
        debug_log.append(f"{pad:2}{toa(piece.board_pos)} {piece.board_pos}: {name(piece)}")
    if not board.obstacles:
        debug_log[-1] += " None"
    for side in board.piece_set_ids:
        debug_log.append(f"{side} pieces ({len(board.movable_pieces[side])}):")
        for piece in board.movable_pieces[side]:
            debug_log.append(f"{pad:2}{toa(piece.board_pos)} {piece.board_pos}: {name(piece, side)}")
        if not board.movable_pieces[side]:
            debug_log[-1] += " None"
    if isinstance(board.custom_pawns, dict):
        custom_pawn_data = [(side, board.custom_pawns.get(side, [])) for side in board.piece_set_ids]
    else:
        custom_pawn_data = [(Side.NONE, board.custom_pawns)]
    for side, data in custom_pawn_data:
        side_string = f"{side} pawn" if side else "Pawn"
        if data is not None:
            pawn_string = ', '.join(name(piece, side) for piece in data)
            debug_log.append(f"{pluralize(max(1, len(data)), side_string)} ({len(data)}): {pawn_string or 'None'}")
        else:
            debug_log.append(f"{side_string} (0): Default")
    for side in board.piece_set_ids:
        poss = board.areas.get(side, {}).get(Pawn.name) or []
        if poss:
            strs = (
                f"{k} ({len(v)})" if len(v) > 1 else f"{k} {v[0]}" for k, v in
                tom(poss, board.board_width, board.board_height, offset_x, offset_y, {}).items()
            )
            debug_log.append(f"{side} pawn area ({len(poss)}): {', '.join(strs)}")
        else:
            debug_log.append(f"{side} pawn area (0): None")
    for side in board.piece_set_ids:
        piece_counts = board.piece_counts.get(side, board.piece_counts)
        piece_limits = board.piece_limits.get(side, board.piece_limits)
        debug_log.append(f"{side} piece counts ({len(piece_limits)}):")
        for group, limit in piece_limits.items():
            count = piece_counts.get(group, 0)
            debug_log.append(f"{pad:2}{group}: {count}/{limit}")
    for side in board.piece_set_ids:
        debug_log.append(f"{side} royal groups ({len(board.royal_groups[side])}):")
        for key, group in board.royal_groups[side].items():
            debug_log.append(f"{pad:2}{key} ({len(group)}):")
            for piece in group:
                debug_log.append(f"{pad:4}{toa(piece.board_pos)} {piece.board_pos}: {name(piece, side)}")
            if not group:
                debug_log[-1] += " None"
        if not board.royal_groups[side]:
            debug_log[-1] += " None"
    for section_type, section_data in (
        ('royal', board.royal_pieces),
        ('anti-royal', board.anti_royal_pieces),
        ('probabilistic', board.probabilistic_pieces),
        ('auto-ranged', board.auto_ranged_pieces),
    ):
        for side in board.piece_set_ids:
            side_section_data = section_data.get(side) or {}
            debug_log.append(f"{side} {section_type} pieces ({len(side_section_data)}):")
            for piece in side_section_data:
                debug_log.append(f"{pad:2}{toa(piece.board_pos)} {piece.board_pos}: {name(piece, side)}")
            if not side_section_data:
                debug_log[-1] += " None"
    for section_type, section_data in (
        ('auto-capture squares', board.auto_capture_markers),
        ('en passant targets', board.en_passant_targets),
        ('royal en passant targets', board.royal_ep_targets),
    ):
        for side in board.piece_set_ids:
            side_section_data = section_data.get(side) or {}
            debug_log.append(f"{side} {section_type} ({len(side_section_data)}):")
            for pos in sorted(side_section_data):
                piece_poss = {p for p in side_section_data[pos] if not isinstance(p, (type, str))}
                poss_string = ', '.join(f'{toa(xy)} {xy}' for xy in sorted(piece_poss))
                debug_log.append(f"{pad:2}{toa(pos)} {pos}: (From {len(piece_poss)}) {poss_string or 'None'}")
            if not side_section_data:
                debug_log[-1] += " None"
    for section, section_data, custom_data in (
        ('promotion', board.promotions, board.custom_promotions),
        ('drop', board.drops, board.custom_drops),
    ):
        for side in board.piece_set_ids:
            side_areas = board.areas.get(side) or {}
            section_rules = section_data.get(side) or {}
            debug_log.append(f"{side} {section} rules ({len(section_rules)}):")
            for piece in section_rules:
                debug_log.append(f"{pad:2}{name(piece, side)} ({len(section_rules[piece])}):")
                if custom_data:
                    base_data = (board.load_dict or {}).get(f"{section}s") or {}
                    from_mapping = frm(
                        list(base_data.get(str(side.value), {}).get(save_piece_type(piece), {})),
                        board.board_width, board.board_height, offset_x, offset_y, side_areas
                    )
                    to_mapping = {}
                    for pos, value in from_mapping.items():
                        if value not in to_mapping:
                            to_mapping[value] = pos
                else:
                    rows = set()
                    for pos in section_rules[piece]:
                        row = pos[0]
                        if row in rows:
                            continue
                        rows.add(row)
                    all_rows = True
                    for abs_row in range(board.board_height):
                        if abs_row + offset_y not in rows:
                            all_rows = False
                            break
                    if all_rows:
                        rows = {ANY}
                    to_mapping = {toa((row, ANY)): (0 if row == ANY else row, 0) for row in rows}
                for string, pos in to_mapping.items():
                    piece_list = []
                    for to_piece in section_rules[piece][pos]:
                        suffixes = []
                        if isinstance(to_piece, AbstractPiece):
                            if to_piece.side not in {side, Side.NONE}:
                                suffixes.append(f"Side: {to_piece.side}")
                            if to_piece.movement and to_piece.movement.total_moves:
                                suffixes.append(f"Moves: {to_piece.movement.total_moves}")
                            if to_piece.promoted_from:
                                suffixes.append(f"Promoted from: {name(to_piece.promoted_from, side)}")
                            if to_piece.should_hide is not None and not isinstance(to_piece, UtilityPiece):
                                suffixes.append("Always hide" if to_piece.should_hide else "Never hide")
                            if to_piece.should_hide is not False and isinstance(to_piece, UtilityPiece):
                                suffixes.append("Always hide" if to_piece.should_hide else "Can be hidden")
                        suffix = f" ({', '.join(suffixes)})" if suffixes else ''
                        piece_list.append(f"{name(to_piece, side)}{suffix}")
                    piece_list = ', '.join(string for string in piece_list)
                    if string not in side_areas:
                        poss = frm([string], board.board_width, board.board_height, offset_x, offset_y, side_areas)
                        if len(poss) > 1:
                            string = f"{string} ({len(poss)})"
                        else:
                            string = f"{string} {fra(string)}"
                    else:
                        string = f"{string} ({len(side_areas[string])})"
                    debug_log.append(f"{pad:4}{string}: {piece_list if piece_list else 'None'}")
                if not section_rules[piece]:
                    debug_log[-1] += " None"
            if not section_rules:
                debug_log[-1] += " None"
    for section_type, section_data in (
        ('starting drops', board.custom_extra_drops),
        ('drops', board.captured_pieces),
    ):
        for side in board.piece_set_ids:
            side_section_data = section_data.get(side) or []
            side_section_string = ', '.join(name(piece, side) for piece in side_section_data)
            debug_log.append(f"{side} {section_type} ({len(side_section_data)}): {side_section_string or 'None'}")
    debug_log.append(f"Edit piece set: {board.edit_piece_set_id}")
    for side in board.piece_set_ids:
        side_data = board.edit_promotions.get(side, [])
        piece_list = ', '.join(
            ((
                f"{piece.side}" if isinstance(piece, AbstractPiece)
                and not (isinstance(piece, UtilityPiece)
                and piece.side is piece.default_side) else ""
            ) + name(piece, side)) if piece else 'None' for piece in side_data
        )
        debug_log.append(f"{side} replacements ({len(side_data)}): {piece_list or 'None'}")
    for section, section_data in (("Custom", board.custom_pieces), ("Past custom", board.past_custom_pieces)):
        debug_log.append(f"{section} pieces ({len(section_data)}):")
        for piece, data in section_data.items():
            debug_log.append(f"{pad:2}{piece}:")
            custom_data = save_custom_type(data(board))
            if not custom_data:
                debug_log[-1] += " None"
            else:
                for key_data in (
                    ('cls', "Type"),
                    'name',
                    ('path', "Texture path"),
                    ('file', "Texture name"),
                    ('cb', "Colorbound", False),
                    ('movement', None, None, lambda x: dumps(x, compression=3, indent=2, ensure_ascii=False)),
                ):
                    key_data = key_data if isinstance(key_data, tuple) else (key_data,)
                    key_data = key_data + (None,) * (4 - len(key_data))
                    key, string, default, build = key_data[:4]
                    if string is None:
                        string = key.capitalize()
                    if default is None:
                        default = 'None'
                    if build is None:
                        build = lambda x: (', '.join(map(str, x)) if isinstance(x, list) else str(x)) or 'None'
                    debug_log.append(f"{pad:4}{string}:")
                    value = build(custom_data.get(key, default)).splitlines()
                    if len(value) > 1:
                        debug_log.extend(f"{pad:6}{line}" for line in value)
                    else:
                        debug_log[-1] += f" {value[0]}"
        if not section_data:
            debug_log[-1] += " None"
    debug_log.append(f"Custom areas ({len(board.custom_areas)}):")
    for area, data in board.custom_areas.items():
        if isinstance(data, dict):
            debug_log.append(f"{pad:2}{area}:")
            entries = [(f"{pad:4}{side}", data.get(side)) for side in (Side.WHITE, Side.BLACK)]
        else:
            entries = [(f"{pad:2}{area}", data)]
        for prefix, poss in entries:
            poss = poss or []
            if poss:
                strs = (
                    f"{k} ({len(v)})" if len(v) > 1 else f"{k} {v[0]}" for k, v in
                    tom(poss, board.board_width, board.board_height, offset_x, offset_y, {}).items()
                )
                debug_log.append(f"{prefix} ({len(poss)}): {', '.join(strs)}")
            else:
                debug_log.append(f"{prefix} (0): None")
    if not board.custom_areas:
        debug_log[-1] += " None"
    debug_log.append(f"Custom layout ({len(board.custom_layout)}):")
    base_data = (board.load_dict or {}).get(f"layout") or {}
    neutral_areas = {k: v for k, v in board.custom_areas.items() if isinstance(v, set)}
    from_mapping = frm(base_data, board.board_width, board.board_height, offset_x, offset_y, neutral_areas)
    to_mapping = {}
    for pos, value in from_mapping.items():
        if value not in to_mapping:
            to_mapping[value] = pos
    for string, pos in to_mapping.items():
        piece = board.custom_layout.get(pos)
        if not piece or isinstance(piece, NoPiece):
            continue
        piece_name = name(piece)
        if piece.side is not (piece.default_side if isinstance(piece, UtilityPiece) else Side.NONE):
            piece_name = f"{piece.side} {piece_name}"
        suffixes = []
        if piece.movement and piece.movement.total_moves:
            suffixes.append(f"Moves: {piece.movement.total_moves}")
        if piece.promoted_from:
            suffixes.append(f"Promoted from: {name(piece.promoted_from, piece.side)}")
        if piece.should_hide is not None and not isinstance(piece, UtilityPiece):
            suffixes.append("Always hide" if piece.should_hide else "Never hide")
        if piece.should_hide is not False and isinstance(piece, UtilityPiece):
            suffixes.append("Always hide" if piece.should_hide else "Can be hidden")
        suffix = f" ({', '.join(suffixes)})" if suffixes else ''
        if string not in neutral_areas:
            poss = frm([string], board.board_width, board.board_height, offset_x, offset_y, neutral_areas)
            if len(poss) > 1:
                string = f"{string} ({len(poss)})"
            else:
                string = f"{string} {fra(string)}"
        else:
            string = f"{string} ({len(neutral_areas[string])})"
        debug_log.append(f"{pad:2}{string}: {piece_name}{suffix}")
    if not board.custom_layout:
        debug_log[-1] += " None"
    piece_mode = {0: "Shown", 1: "Hidden", 2: "Penultima"}.get(board.hide_pieces, "Unknown")
    debug_log.append(f"Hide pieces: {board.hide_pieces} - {piece_mode}")
    move_mode = {None: "Default", False: "Shown", True: "Hidden"}.get(board.hide_move_markers, "Unknown")
    debug_log.append(f"Hide moves: {board.hide_move_markers} - {move_mode}")
    drop_mode = {
        k: f"Pieces {v} be dropped on the board" for k, v in {False: "cannot", True: "can"}.items()
    }.get(board.use_drops, "Unknown")
    debug_log.append(f"Use drops: {board.use_drops} - {drop_mode}")
    chaos_mode = {
        0: "Off",
        1: "Chaos (Matching Pieces)",
        2: "Chaos (Matching Pieces), Asymmetrical",
        3: "Extreme Chaos (Any Pieces)",
        4: "Extreme Chaos (Any Pieces), Asymmetrical"
    }.get(board.chaos_mode, "Unknown")
    debug_log.append(f"Chaos mode: {board.chaos_mode} - {chaos_mode}")
    debug_log.append(f"Board mode: {'Edit' if board.edit_mode else 'Play'}")
    debug_log.append(f"Current ply: {board.ply_count}")
    debug_log.append(f"Current turn: {board.turn_data[0]}")
    debug_log.append(f"Current side: {board.turn_side if board.turn_side else 'None'}")
    debug_log.append(f"Current move: {board.turn_data[2]}")
    debug_log.append(f"Current turn index: {board.get_turn_index()}")
    start, loop = [], []
    start_ended = False
    for data in board.custom_turn_order:
        if data[0] == Side.NONE:
            start_ended = True
            continue
        (loop if start_ended else start).append(data)
    if start and not loop and not start_ended:
        start, loop = loop, start
    if not start and not loop:
        loop = [(Side.WHITE, None), (Side.BLACK, None)]
    def default_builder(data_value):
        if isinstance(data_value, list):
            return ', '.join(map(default_builder, data_value))
        data_value = str(data_value)
        prefix_set = set()
        prefix_list = []
        while data_value[:1] in prefix_types:
            if not data_value:
                if prefix_chars['last'] not in prefix_set:
                    prefix_list.append(prefix_chars['last'])
                    prefix_set.add(prefix_chars['last'])
                break
            if data_value[:1] not in prefix_set:
                prefix_list.append(data_value[:1])
                prefix_set.add(data_value[:1])
            data_value = data_value[1:]
        if {'*', '.'}.intersection(data_value):
            data_value = f'"{data_value}"'
        generic_prefix_list, typed_prefix_list = [], []
        for ch in prefix_list:
            (typed_prefix_list if ch in type_prefixes else generic_prefix_list).append(prefix_types[ch])
        generic_prefix = ' '.join(s.capitalize() for s in generic_prefix_list)
        typed_prefix = ', '.join(s.capitalize() for s in typed_prefix_list)
        return f"{' '.join(s for s in (generic_prefix, typed_prefix, data_value) if s)}" or 'None'
    def action_builder(data_value):
        if isinstance(data_value, list):
            return ', '.join(action_builder(x) for x in data_value)
        invert_action = False
        if data_value[:1] == prefix_chars['not']:
            data_value = data_value[1:]
            invert_action = True
        data_string = action_types[data_value] if data_value in action_types else f"unknown ({data_value})"
        return ("Not " if invert_action else '') + data_string.capitalize()
    start_count = 0
    start_index = 0
    debug_log.append(f"Turn order ({len(start) + len(loop)}):")
    for section_name, section in (('Start', start), ('Loop', loop)):
        if section:
            if start_count or not start_index:
                debug_log.append(f"{pad:2}{section_name}: ({len(section)}):")
            pad_count = 2 if start_index and not start_count else 4
            for i, data in enumerate(section, start_count):
                turn_side, turn_rules = data
                if not turn_rules:
                    debug_log.append(f"{pad:{pad_count}}{i + 1}: {turn_side}")
                else:
                    debug_log.append(f"{pad:{pad_count}}{i + 1}: {turn_side} ({len(turn_rules)}):")
                    for ri, rule in enumerate(turn_rules):
                        debug_log.append(f"{pad:{pad_count + 2}}Option {ri + 1}:")
                        for field, when in (('last', 'ago'), ('next', 'until')):
                            for si, sub_rule in enumerate(rule.get(field, [])):
                                debug_log.append(f"{pad:{pad_count + 4}}{field.capitalize()} option {si + 1}:")
                                for key_data in (
                                    ('by', f"Moves {when}"),
                                    'piece',
                                    ('move', "Move type"),
                                    ('type', "Action type", action_builder),
                                    'from',
                                    'to',
                                    ('take', "Captured"),
                                    ('lose', "Lost"),
                                    ('new', "New piece"),
                                    ('old', "Total moves"),
                                ):
                                    key_data = key_data if isinstance(key_data, tuple) else (key_data,)
                                    key_data = key_data + (None,) * (3 - len(key_data))
                                    key, string, builder = key_data[:3]
                                    if key not in sub_rule:
                                        continue
                                    if string is None:
                                        string = key.capitalize()
                                    if builder is None:
                                        builder = default_builder
                                    debug_log.append(f"{pad:{pad_count + 6}}{string}:")
                                    value = builder(sub_rule[key]).splitlines()
                                    if len(value) > 1:
                                        debug_log.extend(f"{pad:{pad_count + 8}}{line}" for line in value)
                                    else:
                                        debug_log[-1] += f" {value[0]}"
                        for field, cond in (('at', 'position'),):
                            for si, sub_rule in enumerate(rule.get(field, [])):
                                debug_log.append(f"{pad:{pad_count + 4}}{cond.capitalize()} condition {si + 1}:")
                                for key_data in (
                                    'count',
                                    'piece',
                                    'side',
                                    'at',
                                ):
                                    key_data = key_data if isinstance(key_data, tuple) else (key_data,)
                                    key_data = key_data + (None,) * (3 - len(key_data))
                                    key, string, builder = key_data[:3]
                                    if key not in sub_rule:
                                        continue
                                    if string is None:
                                        string = key.capitalize()
                                    if builder is None:
                                        builder = default_builder
                                    debug_log.append(f"{pad:{pad_count + 6}}{string}:")
                                    value = builder(sub_rule[key]).splitlines()
                                    if len(value) > 1:
                                        debug_log.extend(f"{pad:{pad_count + 8}}{line}" for line in value)
                                    else:
                                        debug_log[-1] += f" {value[0]}"
                        for key_data in (
                            'order',
                            (
                                'state', "Board state", lambda l: ', '.join({
                                    0: "Any",
                                    1: "White is not in check", -1: "White is in check",
                                    2: "Black is not in check", -2: "Black is in check",
                                }.get(x, 'Unknown') for x in l)
                            ),
                            'piece',
                            ('move', "Move type"),
                            ('type', 'Action type', action_builder),
                            'from',
                            'to',
                            ('take', "Captured"),
                            ('lose', "Lost"),
                            ('new', "New piece"),
                            ('old', "Total moves"),
                            ('check', "Check", lambda l: ', '.join(
                                {0: 'Any', 1: 'Yes', -1: 'No'}.get(x, 'Unknown') for x in l
                            )),
                        ):
                            key_data = key_data if isinstance(key_data, tuple) else (key_data,)
                            key_data = key_data + (None,) * (3 - len(key_data))
                            key, string, builder = key_data[:3]
                            if key not in rule:
                                continue
                            if string is None:
                                string = key.capitalize()
                            if builder is None:
                                builder = default_builder
                            debug_log.append(f"{pad:{pad_count + 4}}{string}:")
                            value = builder(rule[key]).splitlines()
                            if len(value) > 1:
                                debug_log.extend(f"{pad:{pad_count + 6}}{line}" for line in value)
                            else:
                                debug_log[-1] += f" {value[0]}"
        start_count += len(section)
        start_index += 1
    if not start and not loop:
        debug_log[-1] += " None"
    standard_conditions = set(end_types.values())
    for side in board.end_rules:
        if side:
            debug_log.append(f"End conditions for {side}:")
        else:
            debug_log.append("Conflict resolution rules:")
        for condition in board.end_rules[side]:
            invert, rule = (True, condition[1:]) if condition[:1] == prefix_chars['not'] else (False, condition)
            if rule in standard_conditions:
                rule_start = rule.capitalize()
                end_data = board.end_data.get(side, {}).get(condition, {})
            else:
                if side in board.areas and rule in board.areas[side]:
                    rule_start = f"Reach {rule} with"
                else:
                    try:
                        pos = fra(rule)
                        if pos == (ANY, ANY):
                            rule_start = f"Have"
                        elif pos[0] == ANY:
                            rule_start = f"Reach the {s26(pos[1] + 1)}-file with"
                        elif pos[1] == ANY:
                            rule_start = f"Reach the {spell_ordinal(pos[0] + 1, 0)} rank with"
                        else:
                            rule_start = f"Reach {toa(pos)} with"
                    except ValueError:
                        rule_start = f"Reach {rule} with"
                end_data = board.area_groups.get(side, {}).get(condition, {})
            if isinstance(board.end_rules[side][condition], dict):
                end_rules = board.end_rules[side][condition]
            else:
                end_rules = {'': board.end_rules[side][condition]}
                end_data = {'': end_data}
            for group in end_rules:
                rule_string = rule_start
                opponent = f"{side.opponent()}"
                group_string = ''
                group_value = end_rules[group]
                two = lambda x: f'"{x}"' if any(ch in group for ch in '*.') else pluralize(x)
                one = lambda x: f'"{x}"' if any(ch in group for ch in '*.') else x
                if side is Side.NONE:
                    rule_string = f"Be the one to {rule_string[0].lower() + rule_string[1:]}"
                    if group in {'', '*'}:
                        group_string = True  # only show the rule string
                        rule_string = rule_string.removesuffix(' with')
                    else:
                        group_string = f"a {one(group)}"
                elif rule in standard_conditions and group_value in {'+', '-'}:
                    group_value = int(group_value + '1')
                    prefix = "all of" if rule == 'capture' else "the last of"
                    if group in {'', '*'}:
                        group_string = f"{prefix} {opponent}'s pieces"
                    elif rule == 'capture':
                        group_string = f"all {opponent} {two(group)}"
                    else:
                        group_string = f"the last {opponent} {one(group)}"
                elif rule in standard_conditions and group in {'', '*'}:
                    times = abs(int(group_value)) or 1
                    if rule == 'capture':
                        if times > 1:
                            group_string = f"{spell(times)} of {opponent}'s pieces"
                        else:
                            group_string = f"a {opponent} piece"
                    elif times > 1:
                        group_string = f"{opponent} {spell(times)} times"
                    else:
                        group_string = opponent
                elif isinstance(group_value, str) and group_value[-1:] == '!':
                    value_string = group_value[:-1] or '1'
                    group_value = int(value_string + ('1' if value_string in {'+', '-'} else ''))
                    rule_string = f"Be the only one to {rule_string[0].lower() + rule_string[1:]}"
                else:
                    group_value = int(group_value)
                if invert:
                    rule_string = f"Do not {rule_string[0].lower() + rule_string[1:]}"
                if not group_string:
                    group_string = 'piece' if group in {'', '*'} else group
                    times = abs(int(group_value)) or 1
                    if rule in standard_conditions:
                        if times > 1:
                            group_string = f"{spell(times)} {opponent} {two(group_string)}"
                        else:
                            group_string = f"a {opponent} {one(group_string)}"
                    elif times > 1:
                        group_string = f"{spell(times)} {two(group_string)}"
                    else:
                        group_string = f"a {one(group_string)}"
                if group_string is not True:
                    rule_string = f"{rule_string} {group_string}"
                group_result = {1: "win", 0: "draw", -1: "lose"}.get(sign(group_value))
                full_rule = f"{rule_string} to {group_result}"
                if side is Side.NONE:
                    debug_log.append(f"{pad:2}{full_rule}")
                    continue
                group_data = ''
                if rule in standard_conditions:
                    end_value = end_data.get(group) or 0
                else:
                    end_group = end_data.get(group) or []
                    end_value = len(end_group)
                    if end_value:
                        pieces = [f'{name(p, side)} on {toa(p.board_pos)} {p.board_pos}'.strip() for p in end_group]
                        # that str.strip() call is there just in case Piece.board_pos is None for some reason
                        group_data = f" - {', '.join(pieces)}"
                ratio = f"{end_value}/{abs(group_value) or 1}"
                debug_log.append(f"{pad:2}{full_rule}: {ratio}{group_data}")
    possible_moves = sum((
        sum(v.values(), []) for k, v in board.moves.get(board.turn_side, {}).items() if not isinstance(k, str)
    ), [])
    debug_log.append(f"Moves possible: {len(possible_moves)}")
    debug_log.append(f"Unique moves: {sum(len(i) for i in board.unique_moves()[board.turn_side].values())}")
    debug_log.append(f"Check side: {board.check_side if board.check_side else 'None'}")
    debug_log.append(f"Game over: {board.game_over}")
    def clear_hidden(m: Move):
        for piece in (m.piece, m.promotion, m.placed_piece, m.swapped_piece, *m.captured):
            if isinstance(piece, AbstractPiece):
                piece.is_hidden = None
    def side_name(piece: TypeOr[AbstractPiece]):
        if isinstance(piece, AbstractPiece):
            return f"{piece.side if not isinstance(piece, Neutral) else ''} {name(piece)}".strip()
        elif isinstance(piece, type) and issubclass(piece, AbstractPiece):
            return name(piece)
        else:
            return 'None'
    start_count = 0
    for section_type, section_data in (
        ("Action", board.move_history),
        ("Future action", board.future_move_history[::-1]),
    ):
        section_data = deepcopy(section_data)
        debug_log.append(f"{section_type} history ({len(section_data)}):")
        for i, move in enumerate(section_data, start_count):
            if not move:
                debug_log.append(f"{pad:2}{i + 1}: (Pass) None")
            else:
                clear_hidden(move)
                move_type = 'Edit' if move.is_edit else 'Drop' if move.movement_type == DropMovement else 'Move'
                debug_log.append(f"{pad:2}{i + 1}: ({move_type}) {move.to_string(side_name)}")
                j = 0
                while move.chained_move:
                    move = move.chained_move
                    clear_hidden(move)
                    move_type = 'Edit' if move.is_edit else 'Drop' if move.movement_type == DropMovement else 'Move'
                    debug_log.append(f"{pad:2}{i + 1}.{j + 1}: ({move_type}) {move.to_string(side_name)}")
                    j += 1
        if not board.move_history:
            debug_log[-1] += " None"
        start_count += len(section_data)
    empty = True
    debug_log.append(f"Roll history ({len(board.roll_history)}):")
    for i, roll in enumerate(board.roll_history):
        if roll:
            empty = False
            debug_log.append(f"{pad:2}Roll {i + 1}:")
            for pos, value in roll.items():
                debug_log.append(f"{pad:4}{toa(pos)} {pos}: {value}")
    if empty:
        debug_log[-1] += " None"
    empty = True
    debug_log.append(f"Probabilistic piece history ({len(board.probabilistic_piece_history)}):")
    for i, pieces in enumerate(board.probabilistic_piece_history):
        if pieces:
            empty = False
            turn_side = board.get_turn_side(i, 0)
            debug_log.append(f"{pad:2}Ply {i + 1}:")
            for pos, piece in sorted(pieces.items(), key=lambda x: x[0]):
                debug_log.append(f"{pad:4}{toa(pos)} {pos}: {name(piece, turn_side)}")
    if empty:
        debug_log[-1] += " None"
    debug_log.append(f"Roll seed: {board.roll_seed} (update: {board.board_config['update_roll_seed']})")
    debug_log.append(f"Piece set seed: {board.set_seed}")
    debug_log.append(f"Chaos set seed: {board.chaos_seed}")
    return debug_log
