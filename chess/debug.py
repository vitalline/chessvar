from __future__ import annotations

import sys

from copy import deepcopy, copy
from json import dumps
from typing import TYPE_CHECKING, TextIO

from chess.data import piece_groups, get_piece_types, get_set_name
from chess.movement.types import BaseMovement, DropMovement
from chess.movement.util import to_algebraic as toa, from_algebraic as fra, from_algebraic_map as frm
from chess.pieces.groups import classic as fide
from chess.pieces.piece import Piece
from chess.pieces.side import Side
from chess.save import save_piece_type, save_custom_type, unpack, repack
from chess.util import get_filename

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
    debug_log_data = []  # noqa
    debug_log_data.append(f"Board size: {board.board_width}x{board.board_height}")
    debug_log_data.append(f"Screen size: {board.width}x{board.height}")
    debug_log_data.append(f"Square size: {board.square_size}")
    debug_log_data.append(f"Windowed screen size: {board.windowed_size[0]}x{board.windowed_size[1]}")
    debug_log_data.append(f"Windowed square size: {board.windowed_square_size}")
    debug_log_data.append(f"Color scheme ID: {'-' if board.color_index is None else board.color_index}")
    debug_log_data.append("Color scheme:")
    color_scheme = deepcopy(board.color_scheme)  # just in case trickster mode messes with the color scheme RIGHT NOW
    for k, v in color_scheme.items():
        debug_log_data.append(f"  {k} = {v}")
    debug_log_data.append(f"Piece sets ({len(piece_groups)}):")
    digits = len(str(len(piece_groups)))
    for i, group in enumerate(piece_groups):
        debug_log_data.append(f"  ID {i:0{digits}d}: {group['name']}")
    for i in sorted(board.chaos_sets):
        debug_log_data.append(f"  ID {-i:0{digits}d}: {board.chaos_sets[i][1]}")
    debug_log_data.append(
        f"ID blocklist ({len(board.board_config['block_ids'])}): "
        f"{', '.join(str(i) for i in board.board_config['block_ids']) or 'None'}"
    )
    debug_log_data.append(
        f"Chaos ID blocklist ({len(board.board_config['block_ids_chaos'])}): "
        f"{', '.join(str(i) for i in board.board_config['block_ids_chaos']) or 'None'}"
    )
    debug_log_data.append(f"Variant: {board.variant or 'None'}")
    side_id_strings = {
        side: '-' if set_id is None else f"{set_id:0{digits}d}"
        for side, set_id in board.piece_set_ids.items()
    }
    debug_log_data.append(
        f"Game: "
        f"(ID {side_id_strings[Side.WHITE]}) {board.piece_set_names[Side.WHITE]} vs. "
        f"(ID {side_id_strings[Side.BLACK]}) {board.piece_set_names[Side.BLACK]}"
    )
    for side in board.piece_set_ids:
        debug_log_data.append(f"{side} setup: {', '.join(piece.name for piece in board.piece_sets[side])}")
    for side in board.piece_set_ids:
        debug_log_data.append(f"{side} pieces ({len(board.movable_pieces[side])}):")
        for piece in board.movable_pieces[side]:
            debug_log_data.append(f'  {toa(piece.board_pos)} {piece.board_pos}: {piece.name}')
        if not board.movable_pieces[side]:
            debug_log_data[-1] += " None"
    for side in board.piece_set_ids:
        debug_log_data.append(f"{side} royal pieces ({len(board.royal_pieces[side])}):")
        for piece in board.royal_pieces[side]:
            debug_log_data.append(f'  {toa(piece.board_pos)} {piece.board_pos}: {piece.name}')
        if not board.royal_pieces[side]:
            debug_log_data[-1] += " None"
    for side in board.piece_set_ids:
        debug_log_data.append(f"{side} quasi-royal pieces ({len(board.quasi_royal_pieces[side])}):")
        for piece in board.quasi_royal_pieces[side]:
            debug_log_data.append(f'  {toa(piece.board_pos)} {piece.board_pos}: {piece.name}')
        if not board.quasi_royal_pieces[side]:
            debug_log_data[-1] += " None"
    for side in board.piece_set_ids:
        debug_log_data.append(f"{side} probabilistic pieces ({len(board.probabilistic_pieces[side])}):")
        for piece in board.probabilistic_pieces[side]:
            debug_log_data.append(f'  {toa(piece.board_pos)} {piece.board_pos}: {piece.name}')
        if not board.probabilistic_pieces[side]:
            debug_log_data[-1] += " None"
    for side in board.piece_set_ids:
        debug_log_data.append(f"{side} auto-ranged pieces ({len(board.auto_ranged_pieces[side])}):")
        for piece in board.auto_ranged_pieces[side]:
            debug_log_data.append(f'  {toa(piece.board_pos)} {piece.board_pos}: {piece.name}')
        if not board.auto_ranged_pieces[side]:
            debug_log_data[-1] += " None"
    for side in board.piece_set_ids:
        debug_log_data.append(f"{side} auto-capture squares ({len(board.auto_capture_markers[side])}):")
        for pos in sorted(board.auto_capture_markers[side]):
            piece_poss = board.auto_capture_markers[side][pos]
            debug_log_data.append(f"""  {toa(pos)} {pos}: (From {len(piece_poss)}) {
            ', '.join(f'{toa(xy)} {xy}' for xy in sorted(piece_poss))
            }""")
        if not board.auto_capture_markers[side]:
            debug_log_data[-1] += " None"
    for side in board.piece_set_ids:
        promotions = board.promotions.get(side, {})
        debug_log_data.append(f"{side} promotion rules ({len(promotions)}):")
        for piece in promotions:
            debug_log_data.append(f"  {piece.name} ({len(promotions[piece])}):")
            rows = set()
            for pos in promotions[piece]:
                row = pos[0]
                if row in rows:
                    continue
                rows.add(row)
            if rows == set(range(board.board_height)):
                rows = {-1}
            for row in sorted(rows):
                piece_list = []
                for to_piece in promotions[piece][(max(row, 0), 0)]:
                    suffixes = []
                    if isinstance(to_piece, Piece):
                        if to_piece.side not in {side, Side.NONE}:
                            suffixes.append(f"Side: {to_piece.side}")
                        if to_piece.movement and to_piece.movement.total_moves:
                            suffixes.append(f"Moves: {to_piece.movement.total_moves}")
                        if to_piece.promoted_from:
                            suffixes.append(f"Promoted from: {to_piece.promoted_from.name}")
                        if to_piece.is_hidden is False:
                            suffixes.append('Never hide')
                    suffix = f" ({', '.join(suffixes)})" if suffixes else ''
                    piece_list.append(f"{to_piece.name}{suffix}")
                piece_list = ', '.join(string for string in piece_list)
                debug_log_data.append(f"    {toa((row, -1))} {(row, -1)}: {piece_list if piece_list else 'None'}")
            if not promotions[piece]:
                debug_log_data[-1] += " None"
        if not promotions:
            debug_log_data[-1] += " None"
    for side in board.piece_set_ids:
        drops = board.drops.get(side, {})
        debug_log_data.append(f"{side} drop rules ({len(drops)}):")
        for piece in drops:
            debug_log_data.append(f"  {piece.name} ({len(drops[piece])}):")
            rows = set()
            for pos in drops[piece]:
                row = pos[0]
                if row in rows:
                    continue
                rows.add(row)
            if rows == set(range(board.board_height)):
                rows = {-1}
            for row in sorted(rows):
                piece_list = []
                for to_piece in drops[piece][(max(row, 0), 0)]:
                    suffixes = []
                    if isinstance(to_piece, Piece):
                        if to_piece.side not in {side, Side.NONE}:
                            suffixes.append(f"Side: {to_piece.side}")
                        if to_piece.movement and to_piece.movement.total_moves:
                            suffixes.append(f"Moves: {to_piece.movement.total_moves}")
                        if to_piece.promoted_from:
                            suffixes.append(f"Promoted from: {to_piece.promoted_from.name}")
                        if to_piece.is_hidden is False:
                            suffixes.append('Never hide')
                    suffix = f" ({', '.join(suffixes)})" if suffixes else ''
                    piece_list.append(f"{to_piece.name}{suffix}")
                piece_list = ', '.join(string for string in piece_list)
                debug_log_data.append(f"    {toa((row, -1))} {(row, -1)}: {piece_list if piece_list else 'None'}")
            if not drops[piece]:
                debug_log_data[-1] += " None"
        if not drops:
            debug_log_data[-1] += " None"
    for side in board.piece_set_ids:
        piece_list = ', '.join(piece.name for piece in board.edit_promotions[side])
        debug_log_data.append(
            f"{side} replacements ({len(board.edit_promotions[side])}): {piece_list if piece_list else 'None'}"
        )
    debug_log_data.append(f"Edit piece set: {board.edit_piece_set_id}")
    debug_log_data.append(f"Custom pieces ({len(board.custom_pieces)}):")
    for piece, data in board.custom_pieces.items():
        debug_log_data.append(f"  '{piece}': {save_custom_type(data)}")
    if not board.custom_pieces:
        debug_log_data[-1] += " None"
    debug_log_data.append(f"Past custom pieces ({len(board.past_custom_pieces)}):")
    for piece, data in board.past_custom_pieces.items():
        debug_log_data.append(f"  '{piece}': {save_custom_type(data)}")
    if not board.past_custom_pieces:
        debug_log_data[-1] += " None"
    if board.custom_pawn != fide.Pawn:
        debug_log_data.append(f"Custom pawn: {board.custom_pawn.name} ({save_piece_type(board.custom_pawn)})")
    else:
        debug_log_data.append("Custom pawn: None")
    debug_log_data.append(f"Custom layout ({len(board.custom_layout)}):")
    for pos, piece in board.custom_layout.items():
        suffixes = []
        if piece.movement and piece.movement.total_moves:
            suffixes.append(f"Moves: {piece.movement.total_moves}")
        if piece.promoted_from:
            suffixes.append(f"Promoted from: {piece.promoted_from.name}")
        if piece.is_hidden is False:
            suffixes.append('Never hide')
        suffix = f" ({', '.join(suffixes)})" if suffixes else ''
        debug_log_data.append(f"  {toa(pos)} {pos}: {piece}{suffix}")
    if not board.custom_layout:
        debug_log_data[-1] += " None"
    data = (board.load_dict or {}).get('promotions', {})
    for side in board.piece_set_ids:
        promotions = board.custom_promotions.get(side, {})
        debug_log_data.append(f"{side} custom promotion rules ({len(promotions)}):")
        for piece in promotions:
            debug_log_data.append(f"  {piece.name} ({len(promotions[piece])}):")
            compressed = data.get(str(side.value), {}).get(save_piece_type(piece), {})
            from_mapping = frm(list(compressed), board.width, board.height)
            mapping = {}
            for pos, value in from_mapping.items():
                if value not in mapping:
                    mapping[value] = pos
            for value, pos in mapping.items():
                piece_list = []
                for to_piece in promotions[piece][pos]:
                    suffixes = []
                    if isinstance(to_piece, Piece):
                        if to_piece.side not in {side, Side.NONE}:
                            suffixes.append(f"Side: {to_piece.side}")
                        if to_piece.movement and to_piece.movement.total_moves:
                            suffixes.append(f"Moves: {to_piece.movement.total_moves}")
                        if to_piece.promoted_from:
                            suffixes.append(f"Promoted from: {to_piece.promoted_from.name}")
                        if to_piece.is_hidden is False:
                            suffixes.append('Never hide')
                    suffix = f" ({', '.join(suffixes)})" if suffixes else ''
                    piece_list.append(f"{to_piece.name}{suffix}")
                piece_list = ', '.join(string for string in piece_list)
                debug_log_data.append(f"    {value} {fra(value)}: {piece_list if piece_list else 'None'}")
            if not promotions[piece]:
                debug_log_data[-1] += " None"
        if not promotions:
            debug_log_data[-1] += " None"
    data = (board.load_dict or {}).get('drops', {})
    for side in board.piece_set_ids:
        drops = board.custom_drops.get(side, {})
        debug_log_data.append(f"{side} custom drop rules ({len(drops)}):")
        for piece in drops:
            debug_log_data.append(f"  {piece.name} ({len(drops[piece])}):")
            compressed = data.get(str(side.value), {}).get(save_piece_type(piece), {})
            from_mapping = frm(list(compressed), board.width, board.height)
            mapping = {}
            for pos, value in from_mapping.items():
                if value not in mapping:
                    mapping[value] = pos
            for value, pos in mapping.items():
                piece_list = []
                for to_piece in drops[piece][pos]:
                    suffixes = []
                    if isinstance(to_piece, Piece):
                        if to_piece.side not in {side, Side.NONE}:
                            suffixes.append(f"Side: {to_piece.side}")
                        if to_piece.movement and to_piece.movement.total_moves:
                            suffixes.append(f"Moves: {to_piece.movement.total_moves}")
                        if to_piece.promoted_from:
                            suffixes.append(f"Promoted from: {to_piece.promoted_from.name}")
                        if to_piece.is_hidden is False:
                            suffixes.append('Never hide')
                    suffix = f" ({', '.join(suffixes)})" if suffixes else ''
                    piece_list.append(f"{to_piece.name}{suffix}")
                piece_list = ', '.join(string for string in piece_list)
                debug_log_data.append(f"    {value} {fra(value)}: {piece_list if piece_list else 'None'}")
            if not drops[piece]:
                debug_log_data[-1] += " None"
        if not drops:
            debug_log_data[-1] += " None"
    for side in board.custom_extra_drops:
        debug_log_data.append(
            f"{side} starting drops ({len(board.custom_extra_drops[side])}): "
            f"{', '.join(piece.name for piece in board.custom_extra_drops[side]) or 'None'}"
        )
    for side in board.captured_pieces:
        debug_log_data.append(
            f"{side} drops ({len(board.captured_pieces[side])}): "
            f"{', '.join(piece.name for piece in board.captured_pieces[side]) or 'None'}"
        )
    en_passant_pos = toa(board.en_passant_target.board_pos) if board.en_passant_target else 'None'
    debug_log_data.append(f"En passant target: {en_passant_pos}")
    en_passant_squares = ', '.join(toa(xy) for xy in sorted(board.en_passant_markers)) or 'None'
    debug_log_data.append(f"En passant squares ({len(board.en_passant_markers)}): {en_passant_squares}")
    castling_ep_pos = toa(board.castling_ep_target.board_pos) if board.castling_ep_target else 'None'
    debug_log_data.append(f"Castling EP target: {castling_ep_pos}")
    castling_ep_squares = ', '.join(toa(xy) for xy in sorted(board.castling_ep_markers)) or 'None'
    debug_log_data.append(f"Castling EP squares ({len(board.castling_ep_markers)}): {castling_ep_squares}")
    piece_modes = {0: "Shown", 1: "Hidden", 2: "Penultima"}
    debug_log_data.append(f"Hide pieces: {board.should_hide_pieces} - {piece_modes[board.should_hide_pieces]}")
    move_modes = {None: "Default", False: "Shown", True: "Hidden"}
    debug_log_data.append(f"Hide moves: {board.should_hide_moves} - {move_modes[board.should_hide_moves]}")
    drop_modes = {k: f"Pieces {v} be dropped on the board" for k, v in {False: "cannot", True: "can"}.items()}
    debug_log_data.append(f"Use drops: {board.use_drops} - {drop_modes[board.use_drops]}")
    check_modes = {False: "Capture the royal piece to win", True: "Checkmate the royal piece to win"}
    debug_log_data.append(f"Use check: {board.use_check} - {check_modes[board.use_check]}")
    stalemate_modes = {0: "draws", 1: "loses", -1: "wins"}
    if isinstance(board.stalemate_rule, dict):
        for side, mode in board.stalemate_rule.items():
            debug_log_data.append(f"Stalemate rule: {side} {stalemate_modes[mode]} when stalemated")
    else:
        debug_log_data.append(f"Stalemate rule: Player {stalemate_modes[board.stalemate_rule]} when stalemated")
    royal_modes = {0: "Default", 1: "Force royal (Threaten Any)", 2: "Force quasi-royal (Threaten Last)"}
    debug_log_data.append(f"Royal mode: {board.royal_piece_mode} - {royal_modes[board.royal_piece_mode]}")
    chaos_modes = {
        0: "Off",
        1: "Chaos (Matching Pieces)",
        2: "Chaos (Matching Pieces), Asymmetrical",
        3: "Extreme Chaos (Any Pieces)",
        4: "Extreme Chaos (Any Pieces), Asymmetrical"
    }
    debug_log_data.append(f"Chaos mode: {board.chaos_mode} - {chaos_modes[board.chaos_mode]}")
    debug_log_data.append(f"Board mode: {'Edit' if board.edit_mode else 'Play'}")
    debug_log_data.append(f"Current ply: {board.ply_count}")
    debug_log_data.append(f"Turn side: {board.turn_side if board.turn_side else 'None'}")
    if board.turn_rules is None:
        debug_log_data.append(f"Turn rules: None")
    else:
        debug_log_data.append(f"Turn rules ({len(board.turn_rules)}):")
        for order in board.get_order():
            order_rules = board.turn_rules.get(order)
            if order_rules is None:
                debug_log_data.append(f"  Priority {order}: Any")
                continue
            debug_log_data.append(f"  Priority {order} ({len(order_rules)}):")
            states = [x for x in [0, 1, -1, 2, -2] if x in order_rules]
            for state in states:
                state_rules = order_rules[state]
                state_explanation = {
                    0: "Default",
                    1: "White is NOT in check",
                    2: "Black is NOT in check",
                    -1: "White is in check",
                    -2: "Black is in check"
                }.get(state, "Unknown")
                if state_rules is None:
                    debug_log_data.append(f"    State {state} ({state_explanation}): Any")
                    continue
                debug_log_data.append(f"    State {state} ({state_explanation}) ({len(state_rules)}):")
                for last in sorted(state_rules):
                    last_rules = state_rules[last]
                    not_last = False
                    if last and last[0] is False:
                        not_last, last = last
                    not_last = 'not ' if not_last else ''
                    last_string = (
                        "Any last move" if last == '*' else
                        f"Last move was {not_last}made earlier" if last is '' else
                        f"Last move was {not_last}untagged" if last is None else
                        f"Last move was {not_last}{last.__name__}"
                        if isinstance(last, type) and issubclass(last, BaseMovement) else
                        f"Last move was {not_last}{last}"
                    )
                    if last_rules is None:
                        debug_log_data.append(f"      {last_string}: Any")
                        continue
                    debug_log_data.append(f"      {last_string} ({len(last_rules)}):")
                    for piece in last_rules:
                        piece_rules = last_rules[piece]
                        not_piece = False
                        if piece and piece[0] is False:
                            not_piece, piece = piece
                        not_piece = 'Not ' if not_piece else ''
                        if piece_rules is None:
                            debug_log_data.append(f"        {not_piece}{piece.name}: Any")
                            continue
                        debug_log_data.append(f"        {not_piece}{piece.name} ({len(piece_rules)}):")
                        for tag in piece_rules:
                            tag_rules = piece_rules[tag]
                            not_tag = False
                            if tag and tag[0] is False:
                                not_tag, tag = tag
                            not_tag = 'Not ' if not_tag else ''
                            tag_string = (
                                "Any" if tag == '*' else
                                f"{not_tag}Untagged" if tag is None else
                                f"{not_tag}{tag.__name__}"
                                if isinstance(tag, type) and issubclass(tag, BaseMovement) else
                                f"{not_tag}{tag}"
                            )
                            if tag_rules is None:
                                debug_log_data.append(f"          {tag_string}: Any")
                                continue
                            debug_log_data.append(f"          {tag_string} ({len(tag_rules)}):")
                            for move_type in tag_rules:
                                type_string = {
                                    'm': "Move",
                                    'c': "Capture",
                                    'd': "Drop",
                                    'p': "Pass",
                                }.get(move_type, "Unknown")
                                check_rule = tag_rules[move_type]
                                check_explanation = {
                                    0: "Any", None: "Any",
                                    1: "Only as check",
                                    -1: "Never as check",
                                }.get(check_rule, "Unknown")
                                debug_log_data.append(f"            {type_string}: {check_rule} ({check_explanation})")
                            if not tag_rules:
                                debug_log_data[-1] += " None"
                        if not piece_rules:
                            debug_log_data[-1] += " None"
                    if not last_rules:
                        debug_log_data[-1] += " None"
                if not state_rules:
                    debug_log_data[-1] += " None"
            if not order_rules:
                debug_log_data[-1] += " None"
        if not board.turn_rules:
            debug_log_data[-1] += " None"
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
    debug_log_data.append(f"Turn order ({len(start) + len(loop)}):")
    if start:
        debug_log_data.append(f"  Start: ({len(start)}):")
        for i, data in enumerate(start):
            turn_side, turn_rules = data
            turn_rules = copy(repack(turn_rules))
            for j, rule in enumerate(turn_rules):
                if rule and 'cls' in rule:
                    turn_rules[j] = copy(rule)
                    turn_rules[j]['cls'] = unpack([save_piece_type(t) for t in repack(rule['cls'])])
            turn_rules = unpack(turn_rules)
            turn_suffix = '' if turn_rules is None else f", {turn_rules}"
            debug_log_data.append(f"    {i + 1}: {turn_side}{turn_suffix}")
    if loop:
        pad = ''
        if start:
            debug_log_data.append(f"  Loop: ({len(loop)}):")
            pad = '  '
        for i, data in enumerate(loop, len(start)):
            turn_side, turn_rules = data
            turn_rules = copy(repack(turn_rules))
            for j, rule in enumerate(turn_rules):
                if rule and 'cls' in rule:
                    turn_rules[j] = copy(rule)
                    turn_rules[j]['cls'] = unpack([save_piece_type(t) for t in repack(rule['cls'])])
            turn_rules = unpack(turn_rules)
            turn_suffix = '' if turn_rules is None else f", {turn_rules}"
            debug_log_data.append(f"  {pad}{i + 1}: {turn_side}{turn_suffix}")
    if not start and not loop:
        debug_log_data[-1] += " None"
    possible_moves = sum((
        sum(v.values(), []) for k, v in board.moves.get(board.turn_side, {}).items() if not isinstance(k, str)
    ), [])
    debug_log_data.append(f"Moves possible: {len(possible_moves)}")
    debug_log_data.append(f"Unique moves: {sum(len(i) for i in board.unique_moves()[board.turn_side].values())}")
    debug_log_data.append(f"Check side: {board.check_side if board.check_side else 'None'}")
    debug_log_data.append(f"Game over: {board.game_over}")
    debug_log_data.append(f"Action history ({len(board.move_history)}):")
    for i, move in enumerate(board.move_history):
        if not move:
            debug_log_data.append(f"  {i + 1}: (Pass) None")
        else:
            move_type = 'Edit' if move.is_edit else 'Drop' if move.movement_type == DropMovement else 'Move'
            debug_log_data.append(f"  {i + 1}: ({move_type}) {move}")
            j = 0
            while move.chained_move:
                move = move.chained_move
                move_type = 'Edit' if move.is_edit else 'Drop' if move.movement_type == DropMovement else 'Move'
                debug_log_data.append(f"  {i + 1}.{j + 1}: ({move_type}) {move}")
                j += 1
    if not board.move_history:
        debug_log_data[-1] += " None"
    debug_log_data.append(f"Future action history ({len(board.future_move_history)}):")
    for i, move in enumerate(board.future_move_history[::-1], len(board.move_history)):
        if not move:
            debug_log_data.append(f"  {i + 1}: (Pass) None")
        else:
            move_type = 'Edit' if move.is_edit else 'Drop' if move.movement_type == DropMovement else 'Move'
            debug_log_data.append(f"  {i + 1}: ({move_type}) {move}")
            j = 0
            while move.chained_move:
                move = move.chained_move
                move_type = 'Edit' if move.is_edit else 'Drop' if move.movement_type == DropMovement else 'Move'
                debug_log_data.append(f"  {i + 1}.{j + 1}: ({move_type}) {move}")
                j += 1
    if not board.future_move_history:
        debug_log_data[-1] += " None"
    empty = True
    debug_log_data.append(f"Roll history ({len(board.roll_history)}):")
    for i, roll in enumerate(board.roll_history):
        if roll:
            empty = False
            debug_log_data.append(f"  Roll {i + 1}:")
            for pos, value in roll.items():
                debug_log_data.append(f"    {toa(pos)} {pos}: {value}")
    if empty:
        debug_log_data[-1] += " None"
    empty = True
    debug_log_data.append(f"Probabilistic piece history ({len(board.probabilistic_piece_history)}):")
    for i, pieces in enumerate(board.probabilistic_piece_history):
        if pieces:
            empty = False
            debug_log_data.append(f"  Ply {i + 1}:")
            for pos, piece in sorted(pieces, key=lambda x: x[0]):
                debug_log_data.append(f"    {toa(pos)} {pos}: {piece.name}")
    if empty:
        debug_log_data[-1] += " None"
    debug_log_data.append(f"Roll seed: {board.roll_seed} (update: {board.board_config['update_roll_seed']})")
    debug_log_data.append(f"Piece set seed: {board.set_seed}")
    debug_log_data.append(f"Chaos set seed: {board.chaos_seed}")
    return debug_log_data