from __future__ import annotations

import sys

from copy import deepcopy, copy
from json import dumps
from typing import TYPE_CHECKING, TextIO

from chess.data import end_types, get_piece_types, get_set_name, piece_groups
from chess.movement.types import DropMovement
from chess.movement.util import to_alpha as b26
from chess.movement.util import to_algebraic as toa, from_algebraic as fra
from chess.movement.util import to_algebraic_map as tom, from_algebraic_map as frm
from chess.pieces.groups.classic import Pawn
from chess.pieces.piece import Piece
from chess.pieces.side import Side
from chess.save import save_piece_type, save_custom_type
from chess.util import get_filename, sign, spell, spell_ordinal, unpack, repack

if TYPE_CHECKING:
    from chess.board import Board


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
    for name, path, file in sorted((n, save_piece_type(t), t.file_name) for t, n in get_piece_types(side).items()):
        fp.write(f"{name}: {path}, {file}\n")


def save_piece_data(board: Board, file_path: str = None) -> None:
    with open(
        file_path or
        get_filename('debug_piece_data', 'json', ts_format=''),
        mode='w',
        encoding='utf-8',
    ) as fp:
        print_piece_data(board, fp)


def save_piece_sets(file_path: str = None) -> None:
    with open(
        file_path or
        get_filename('debug_piece_sets', 'txt', ts_format=''),
        mode='w',
        encoding='utf-8',
    ) as fp:
        print_piece_sets(fp)


def save_piece_types(file_path: str = None, side: Side = Side.WHITE) -> None:
    with open(
        file_path or
        get_filename('debug_piece_types', 'txt', ts_format=''),
        mode='w',
        encoding='utf-8',
    ) as fp:
        print_piece_types(fp, side)


def debug_info(board: Board) -> list[str]:
    pad = ''
    debug_log = []  # noqa
    debug_log.append(f"Board size: {board.board_width}x{board.board_height}")
    debug_log.append("Borders:")
    if board.border_cols or board.border_rows:
        file_splits = list(f'{b26(x)}/{b26(x + 1)}' for x in board.border_cols)
        if file_splits:
            debug_log.append(f"{pad:2}Files ({len(file_splits)}): {', '.join(file_splits)} {tuple(board.border_cols)}")
        else:
            debug_log.append(f"{pad:2}Files (0): None")
        rank_splits = list(f'{x}/{x + 1}' for x in board.border_rows)
        if board.border_rows:
            debug_log.append(f"{pad:2}Ranks ({len(rank_splits)}): {', '.join(rank_splits)} {tuple(board.border_rows)}")
        else:
            debug_log.append(f"{pad:2}Ranks (0): None")
    else:
        debug_log[-1] += " None"
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
    debug_log.append(f"Variant: {board.variant or 'None'}")
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
        debug_log.append(f"{side} setup: {', '.join(piece.name for piece in board.piece_sets[side])}")
    debug_log.append(f"Piece groups ({len(board.piece_groups)}):")
    for group in board.piece_groups:
        group_string = ', '.join(piece.name for piece in board.piece_groups[group])
        debug_log.append(f"{pad:2}{group} ({len(board.piece_groups[group])}): {group_string or 'None'}")
    if not board.piece_groups:
        debug_log[-1] += " None"
    for side in board.piece_set_ids:
        debug_log.append(f"{side} pieces ({len(board.movable_pieces[side])}):")
        for piece in board.movable_pieces[side]:
            debug_log.append(f"{pad:2}{toa(piece.board_pos)} {piece.board_pos}: {piece.name}")
        if not board.movable_pieces[side]:
            debug_log[-1] += " None"
    if board.custom_pawn != Pawn:
        debug_log.append(f"Pawn: {board.custom_pawn.name} ({save_piece_type(board.custom_pawn)})")
    else:
        debug_log.append("Pawn: Default")
    for side in board.piece_set_ids:
        poss = board.areas.get(side, {}).get(Pawn.name) or []
        if poss:
            strs = list(tom(poss, board.board_width, board.board_height, {}))
            debug_log.append(f"{side} pawn area ({len(poss)}): {', '.join(f'{pos} {fra(pos)}' for pos in strs)}")
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
                debug_log.append(f"{pad:4}{toa(piece.board_pos)} {piece.board_pos}: {piece.name}")
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
                debug_log.append(f"{pad:2}{toa(piece.board_pos)} {piece.board_pos}: {piece.name}")
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
                piece_poss = side_section_data[pos]
                poss_string = ', '.join(f'{toa(xy)} {xy}' for xy in sorted(piece_poss))
                debug_log.append(f"{pad:2}{toa(pos)} {pos}: (From {len(piece_poss)}) {poss_string or 'None'}")
            if not side_section_data:
                debug_log[-1] += " None"
    for section, section_data in (('promotion', board.promotions), ('drop', board.drops)):
        for side in board.piece_set_ids:
            section_rules = section_data.get(side) or {}
            debug_log.append(f"{side} {section} rules ({len(section_rules)}):")
            for piece in section_rules:
                debug_log.append(f"{pad:2}{piece.name} ({len(section_rules[piece])}):")
                rows = set()
                for pos in section_rules[piece]:
                    row = pos[0]
                    if row in rows:
                        continue
                    rows.add(row)
                if rows == set(range(board.board_height)):
                    rows = {-1}
                for row in sorted(rows):
                    piece_list = []
                    for to_piece in section_rules[piece][(max(row, 0), 0)]:
                        suffixes = []
                        if isinstance(to_piece, Piece):
                            if to_piece.side not in {side, Side.NONE}:
                                suffixes.append(f"Side: {to_piece.side}")
                            if to_piece.movement and to_piece.movement.total_moves:
                                suffixes.append(f"Moves: {to_piece.movement.total_moves}")
                            if to_piece.promoted_from:
                                suffixes.append(f"Promoted from: {to_piece.promoted_from.name}")
                            if to_piece.should_hide is not None:
                                suffixes.append("Always hide" if to_piece.should_hide else "Never hide")
                        suffix = f" ({', '.join(suffixes)})" if suffixes else ''
                        piece_list.append(f"{to_piece.name}{suffix}")
                    piece_list = ', '.join(string for string in piece_list)
                    debug_log.append(f"{pad:4}{toa((row, -1))} {(row, -1)}: {piece_list if piece_list else 'None'}")
                if not section_rules[piece]:
                    debug_log[-1] += " None"
            if not section_rules:
                debug_log[-1] += " None"
    debug_log.append(f"Edit piece set: {board.edit_piece_set_id}")
    for side in board.piece_set_ids:
        side_data = board.edit_promotions.get(side, [])
        piece_list = ', '.join(piece.name for piece in side_data)
        debug_log.append(f"{side} replacements ({len(side_data)}): {piece_list or 'None'}")
    debug_log.append(f"Obstacles ({len(board.obstacles)}):")
    for piece in board.obstacles:
        debug_log.append(f"{pad:2}{toa(piece.board_pos)} {piece.board_pos}: {piece.name}")
    if not board.obstacles:
        debug_log[-1] += " None"
    for section, section_data in (("Custom", board.custom_pieces), ("Past custom", board.past_custom_pieces)):
        debug_log.append(f"{section} pieces ({len(section_data)}):")
        for piece, data in section_data.items():
            debug_log.append(f"{pad:2}{piece}: {save_custom_type(data)}")
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
                strs = list(tom(poss, board.board_width, board.board_height, {}))
                debug_log.append(f"{prefix} ({len(poss)}): {', '.join(f'{pos} {fra(pos)}' for pos in strs)}")
            else:
                debug_log.append(f"{prefix} (0): None")
    if not board.custom_areas:
        debug_log[-1] += " None"
    debug_log.append(f"Custom layout ({len(board.custom_layout)}):")
    for pos, piece in board.custom_layout.items():
        suffixes = []
        if piece.movement and piece.movement.total_moves:
            suffixes.append(f"Moves: {piece.movement.total_moves}")
        if piece.promoted_from:
            suffixes.append(f"Promoted from: {piece.promoted_from.name}")
        if piece.should_hide is not None:
            suffixes.append("Always hide" if piece.should_hide else "Never hide")
        suffix = f" ({', '.join(suffixes)})" if suffixes else ''
        debug_log.append(f"{pad:2}{toa(pos)} {pos}: {piece}{suffix}")
    if not board.custom_layout:
        debug_log[-1] += " None"
    for section, section_data in (('promotion', board.custom_promotions), ('drop', board.custom_drops)):
        data = (board.load_dict or {}).get(f"{section}s") or {}
        for side in board.piece_set_ids:
            section_rules = section_data.get(side) or {}
            debug_log.append(f"{side} custom {section} rules ({len(section_rules)}):")
            for piece in section_rules:
                debug_log.append(f"{pad:2}{piece.name} ({len(section_rules[piece])}):")
                compressed = data.get(str(side.value), {}).get(save_piece_type(piece), {})
                from_mapping = frm(list(compressed), board.board_width, board.board_height, board.areas.get(side) or {})
                mapping = {}
                for pos, value in from_mapping.items():
                    if value not in mapping:
                        mapping[value] = pos
                for value, pos in mapping.items():
                    piece_list = []
                    for to_piece in section_rules[piece][pos]:
                        suffixes = []
                        if isinstance(to_piece, Piece):
                            if to_piece.side not in {side, Side.NONE}:
                                suffixes.append(f"Side: {to_piece.side}")
                            if to_piece.movement and to_piece.movement.total_moves:
                                suffixes.append(f"Moves: {to_piece.movement.total_moves}")
                            if to_piece.promoted_from:
                                suffixes.append(f"Promoted from: {to_piece.promoted_from.name}")
                            if to_piece.should_hide is not None:
                                suffixes.append("Always hide" if to_piece.should_hide else "Never hide")
                        suffix = f" ({', '.join(suffixes)})" if suffixes else ''
                        piece_list.append(f"{to_piece.name}{suffix}")
                    piece_list = ', '.join(string for string in piece_list)
                    debug_log.append(f"{pad:4}{value} {fra(value)}: {piece_list if piece_list else 'None'}")
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
            side_section_string = ', '.join(piece.name for piece in side_section_data)
            debug_log.append(f"{side} {section_type} ({len(side_section_data)}): {side_section_string or 'None'}")
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
    debug_log.append(f"Movement rules ({len(board.turn_rules)}):")
    for order in board.get_order():
        order_rules = board.turn_rules.get(order) or {}
        debug_log.append(f"{pad:2}Priority {order} ({len(order_rules)}):")
        states = [x for x in [0, 1, -1, 2, -2] if x in order_rules]
        for state in states:
            state_rules = order_rules[state]
            state_string = {
                0: "Any board state",
                1: "White is NOT in check",
                2: "Black is NOT in check",
                -1: "White is in check",
                -2: "Black is in check"
            }.get(state, "Unknown")
            debug_log.append(f"{pad:4}State {state} ({state_string}) ({len(state_rules)}):")
            for allow_last in sorted(state_rules):
                allow_last_rules = state_rules[allow_last]
                for block_last in sorted(allow_last_rules):
                    block_last_rules = allow_last_rules[block_last]
                    last_string = (
                        "Any last move" if allow_last == '*' and block_last is None else
                        f"Last move was {allow_last}" if block_last is None else
                        f"Last move was NOT {block_last}" if allow_last == '*' else
                        f"Last move was {allow_last}, NOT {block_last}"
                    )
                    debug_log.append(f"{pad:6}{last_string} ({len(block_last_rules)}):")
                    for allow_piece in sorted(block_last_rules):
                        allow_piece_rules = block_last_rules[allow_piece]
                        for block_piece in sorted(allow_piece_rules):
                            block_piece_rules = allow_piece_rules[block_piece]
                            piece_string = (
                                "Any piece" if allow_piece == '*' and block_piece is None else
                                "Piece moved" if allow_piece == '' and block_piece is None else
                                "Piece NOT moved" if allow_piece == '*' and block_piece == '' else
                                f"{allow_piece}, NOT moved" if allow_piece != '*' and block_piece == '' else
                                f"NOT {block_piece}, moved" if allow_piece == '' and block_piece is not None else
                                f"{allow_piece}" if block_piece is None else
                                f"NOT {block_piece}" if allow_piece == '*' else
                                f"{allow_piece}, NOT {block_piece}"
                            )
                            debug_log.append(f"{pad:8}{piece_string} ({len(block_piece_rules)}):")
                            for allow_type in sorted(block_piece_rules):
                                allow_type_rules = block_piece_rules[allow_type]
                                for block_type in sorted(allow_type_rules):
                                    block_type_rules = allow_type_rules[block_type]
                                    type_string = (
                                        "Any move" if allow_type == '*' and block_type is None else
                                        "Tag used" if allow_type == '' and block_type is None else
                                        "Tag NOT used" if allow_type == '*' and block_type == '' else
                                        f"{allow_type}, NOT used" if allow_type != '*' and block_type == '' else
                                        f"NOT {block_type}, used" if allow_type == '' and block_type is not None else
                                        f"{allow_type}" if block_type is None else
                                        f"NOT {block_type}" if allow_type == '*' else
                                        f"{allow_type}, NOT {block_type}"
                                    )
                                    debug_log.append(f"{pad:10}{type_string} ({len(block_type_rules)}):")
                                    for allow_action in block_type_rules:
                                        allow_action_rules = block_type_rules[allow_action]
                                        allow_string = 'turn pass' if allow_action == 'pass' else allow_action
                                        for block_action in sorted(allow_action_rules):
                                            check_rule = allow_action_rules[block_action]
                                            block_string = 'turn pass' if block_action == 'pass' else block_action
                                            action_string = (
                                                "Any action" if allow_action == '*' and block_action is None else
                                                f"{allow_string.capitalize()}" if block_action is None else
                                                f"NOT {block_string}" if allow_action == '*' else
                                                f"{allow_string.capitalize()}, NOT {block_string}"
                                            )
                                            check_string = {
                                                0: action_string,
                                                1: f"{action_string}: Only as check",
                                                -1: f"{action_string}: Never as check",
                                            }.get(check_rule, f"{action_string}: Unknown")
                                            debug_log.append(f"{pad:12}{check_string} ({check_rule})")
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
    start_count = 0
    start_index = 0
    debug_log.append(f"Move order ({len(start) + len(loop)}):")
    for section_name, section in (('Start', start), ('Loop', loop)):
        if section:
            if start_count or not start_index:
                debug_log.append(f"{pad:2}{section_name}: ({len(section)}):")
            pad_count = 2 if start_index and not start_count else 4
            for i, data in enumerate(section, start_count):
                turn_side, turn_rules = data
                turn_rules = list(repack(turn_rules))
                for j, rule in enumerate(turn_rules):
                    for string in ('action', 'last', 'piece', 'type'):
                        if rule and string in rule:
                            turn_rules[j] = copy(rule)
                            turn_rules[j][string] = unpack([t for t in repack(rule[string])])
                turn_rules = unpack(turn_rules)
                turn_suffix = '' if turn_rules is None else f", {turn_rules}"
                debug_log.append(f"{pad:{pad_count}}{i + 1}: {turn_side}{turn_suffix}")
        start_count += len(section)
        start_index += 1
    if not start and not loop:
        debug_log[-1] += " None"
    standard_conditions = set(end_types.values())
    generic_strings = {'': 'the pieces', '*': 'any piece'}
    for side in board.end_rules:
        debug_log.append(f"End conditions for {side}:")
        for rule in board.end_rules[side]:
            if rule in standard_conditions:
                rule_string = rule.capitalize()
                end_data = board.end_data.get(side, {}).get(rule, {})
            else:
                if side in board.areas and rule in board.areas[side]:
                    rule_string = f"Reach {rule} with"
                else:
                    try:
                        pos = fra(rule)
                        if pos == (-1, -1):
                            rule_string = f"Have"
                        elif pos[0] == -1:
                            rule_string = f"Reach the {b26(pos[1] + 1)}-file with"
                        elif pos[1] == -1:
                            rule_string = f"Reach the {spell_ordinal(pos[0] + 1, 0)} rank with"
                        else:
                            rule_string = f"Reach {toa(pos)} with"
                    except ValueError:
                        rule_string = f"Reach {rule} with"
                end_data = board.area_groups.get(side, {}).get(rule, {})
            for group in board.end_rules[side][rule]:
                group_value = board.end_rules[side][rule][group]
                if rule in standard_conditions and group_value in {'+', '-'}:
                    group_value = int(group_value + '1')
                    group_string = f"last {generic_strings.get(group, group)}"
                elif isinstance(group_value, str) and group_value[-1:] == '!':
                    group_string = group_value[:-1] or '1'
                    group_value = int(group_string + ('1' if group_string in {'+', '-'} else ''))
                    group_string = f"{spell(abs(group_value) or 1)} of {generic_strings.get(group, group)} and stay"
                else:
                    group_value = int(group_value)
                    group_string = f"{spell(abs(group_value) or 1)} of {generic_strings.get(group, group)}"
                group_result = {1: "win", 0: "draw", -1: "lose"}.get(sign(group_value))
                if rule in standard_conditions:
                    end_value = end_data.get(group) or 0
                else:
                    end_group = end_data.get(group) or []
                    end_value = len(end_group)
                    if end_value:
                        pieces = [f'{p.name} on {toa(p.board_pos)} {p.board_pos}'.strip() for p in end_group]
                        # that str.strip() call is there just in case Piece.board_pos is None for some reason
                        end_value = f"{end_value} - {', '.join(pieces)}"
                full_rule = f"{rule_string} {group_string} to {group_result}"
                ratio = f"{end_value}/{abs(group_value) or 1}"
                debug_log.append(f"{pad:2}{full_rule}: {ratio}")
    possible_moves = sum((
        sum(v.values(), []) for k, v in board.moves.get(board.turn_side, {}).items() if not isinstance(k, str)
    ), [])
    debug_log.append(f"Moves possible: {len(possible_moves)}")
    debug_log.append(f"Unique moves: {sum(len(i) for i in board.unique_moves()[board.turn_side].values())}")
    debug_log.append(f"Check side: {board.check_side if board.check_side else 'None'}")
    debug_log.append(f"Game over: {board.game_over}")
    start_count = 0
    for section_type, section_data in (
        ("Action", board.move_history),
        ("Future action", board.future_move_history[::-1]),
    ):
        debug_log.append(f"{section_type} history ({len(section_data)}):")
        for i, move in enumerate(section_data, start_count):
            if not move:
                debug_log.append(f"{pad:2}{i + 1}: (Pass) None")
            else:
                move_type = 'Edit' if move.is_edit else 'Drop' if move.movement_type == DropMovement else 'Move'
                debug_log.append(f"{pad:2}{i + 1}: ({move_type}) {move}")
                j = 0
                while move.chained_move:
                    move = move.chained_move
                    move_type = 'Edit' if move.is_edit else 'Drop' if move.movement_type == DropMovement else 'Move'
                    debug_log.append(f"{pad:2}{i + 1}.{j + 1}: ({move_type}) {move}")
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
            debug_log.append(f"{pad:2}Ply {i + 1}:")
            for pos, piece in sorted(pieces.items(), key=lambda x: x[0]):
                debug_log.append(f"{pad:4}{toa(pos)} {pos}: {piece.name}")
    if empty:
        debug_log[-1] += " None"
    debug_log.append(f"Roll seed: {board.roll_seed} (update: {board.board_config['update_roll_seed']})")
    debug_log.append(f"Piece set seed: {board.set_seed}")
    debug_log.append(f"Chaos set seed: {board.chaos_seed}")
    return debug_log
