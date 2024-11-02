from __future__ import annotations

import sys

from copy import deepcopy, copy
from json import dumps
from typing import TYPE_CHECKING, TextIO

from chess.data import get_piece_types, get_set_name, piece_groups
from chess.movement.types import DropMovement
from chess.movement.util import to_alpha as b26, to_algebraic as toa, from_algebraic as fra, from_algebraic_map as frm
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
    pad = ''
    debug_log = []  # noqa
    debug_log.append(f"Board size: {board.board_width}x{board.board_height}")
    debug_log.append("Borders:")
    if board.border_cols or board.border_rows:
        file_splits = (f'{b26(x)}/{b26(x + 1)}' for x in board.border_cols)
        if file_splits:
            debug_log.append(
                f"{pad:2}Files: {', '.join(file_splits)} {tuple(board.border_cols)}"
            )
        else:
            debug_log.append(f"{pad:2}Files: None")
        rank_splits = (f'{x}/{x + 1}' for x in board.border_rows)
        if board.border_rows:
            debug_log.append(
                f"{pad:2}Ranks: {', '.join(rank_splits)} {tuple(board.border_rows)}"
            )
        else:
            debug_log.append(f"{pad:2}Ranks: None")
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
    debug_log.append(
        f"ID blocklist ({len(board.board_config['block_ids'])}): "
        f"{', '.join(str(i) for i in board.board_config['block_ids']) or 'None'}"
    )
    debug_log.append(
        f"Chaos ID blocklist ({len(board.board_config['block_ids_chaos'])}): "
        f"{', '.join(str(i) for i in board.board_config['block_ids_chaos']) or 'None'}"
    )
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
    for side in board.piece_set_ids:
        debug_log.append(f"{side} pieces ({len(board.movable_pieces[side])}):")
        for piece in board.movable_pieces[side]:
            debug_log.append(f"{pad:2}{toa(piece.board_pos)} {piece.board_pos}: {piece.name}")
        if not board.movable_pieces[side]:
            debug_log[-1] += " None"
    for side in board.piece_set_ids:
        debug_log.append(f"{side} royal groups ({len(board.royal_groups[side])}):")
        groups = {
            key: board.royal_groups[side][key] for key in sorted(  # this should put mixin classes before pieces
                board.royal_groups[side], key=lambda x: (1, x.name) if issubclass(x, Piece) else (0, x.__name__)
            )
        }
        for key, group in groups.items():
            debug_log.append(f"{pad:2}\"{key}\" ({len(group)}):")
            for piece in group:
                debug_log.append(f"{pad:2}{toa(piece.board_pos)} {piece.board_pos}: {piece.name}")
            if not group:
                debug_log[-1] += " None"
        if not board.royal_groups[side]:
            debug_log[-1] += " None"
    for side in board.piece_set_ids:
        debug_log.append(f"{side} royal pieces ({len(board.royal_pieces[side])}):")
        for piece in board.royal_pieces[side]:
            debug_log.append(f"{pad:2}{toa(piece.board_pos)} {piece.board_pos}: {piece.name}")
        if not board.royal_pieces[side]:
            debug_log[-1] += " None"
    for side in board.piece_set_ids:
        debug_log.append(f"{side} anti-royal pieces ({len(board.anti_royal_pieces[side])}):")
        for piece in board.anti_royal_pieces[side]:
            debug_log.append(f"{pad:2}{toa(piece.board_pos)} {piece.board_pos}: {piece.name}")
        if not board.anti_royal_pieces[side]:
            debug_log[-1] += " None"
    for side in board.piece_set_ids:
        debug_log.append(f"{side} probabilistic pieces ({len(board.probabilistic_pieces[side])}):")
        for piece in board.probabilistic_pieces[side]:
            debug_log.append(f"{pad:2}{toa(piece.board_pos)} {piece.board_pos}: {piece.name}")
        if not board.probabilistic_pieces[side]:
            debug_log[-1] += " None"
    for side in board.piece_set_ids:
        debug_log.append(f"{side} auto-ranged pieces ({len(board.auto_ranged_pieces[side])}):")
        for piece in board.auto_ranged_pieces[side]:
            debug_log.append(f"{pad:2}{toa(piece.board_pos)} {piece.board_pos}: {piece.name}")
        if not board.auto_ranged_pieces[side]:
            debug_log[-1] += " None"
    for side in board.piece_set_ids:
        debug_log.append(f"{side} auto-capture squares ({len(board.auto_capture_markers[side])}):")
        for pos in sorted(board.auto_capture_markers[side]):
            piece_poss = board.auto_capture_markers[side][pos]
            debug_log.append(f"""  {toa(pos)} {pos}: (From {len(piece_poss)}) {
            ', '.join(f'{toa(xy)} {xy}' for xy in sorted(piece_poss))
            }""")
        if not board.auto_capture_markers[side]:
            debug_log[-1] += " None"
    for side in board.piece_set_ids:
        debug_log.append(f"{side} en passant targets ({len(board.en_passant_targets[side])}):")
        for pos in sorted(board.en_passant_targets[side]):
            piece_poss = board.en_passant_targets[side][pos]
            debug_log.append(f"""  {toa(pos)} {pos}: (From {len(piece_poss)}) {
            ', '.join(f'{toa(xy)} {xy}' for xy in sorted(piece_poss))
            }""")
        if not board.en_passant_targets[side]:
            debug_log[-1] += " None"
    for side in board.piece_set_ids:
        debug_log.append(f"{side} royal en passant targets ({len(board.royal_ep_targets[side])}):")
        for pos in sorted(board.royal_ep_targets[side]):
            piece_poss = board.royal_ep_targets[side][pos]
            debug_log.append(f"""  {toa(pos)} {pos}: (From {len(piece_poss)}) {
            ', '.join(f'{toa(xy)} {xy}' for xy in sorted(piece_poss))
            }""")
        if not board.royal_ep_targets[side]:
            debug_log[-1] += " None"
    for side in board.piece_set_ids:
        promotions = board.promotions.get(side, {})
        debug_log.append(f"{side} promotion rules ({len(promotions)}):")
        for piece in promotions:
            debug_log.append(f"{pad:2}{piece.name} ({len(promotions[piece])}):")
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
                debug_log.append(f"{pad:4}{toa((row, -1))} {(row, -1)}: {piece_list if piece_list else 'None'}")
            if not promotions[piece]:
                debug_log[-1] += " None"
        if not promotions:
            debug_log[-1] += " None"
    for side in board.piece_set_ids:
        drops = board.drops.get(side, {})
        debug_log.append(f"{side} drop rules ({len(drops)}):")
        for piece in drops:
            debug_log.append(f"{pad:2}{piece.name} ({len(drops[piece])}):")
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
                debug_log.append(f"{pad:4}{toa((row, -1))} {(row, -1)}: {piece_list if piece_list else 'None'}")
            if not drops[piece]:
                debug_log[-1] += " None"
        if not drops:
            debug_log[-1] += " None"
    debug_log.append(f"Edit piece set: {board.edit_piece_set_id}")
    for side in board.piece_set_ids:
        piece_list = ', '.join(piece.name for piece in board.edit_promotions[side])
        debug_log.append(
            f"{side} replacements ({len(board.edit_promotions[side])}): {piece_list if piece_list else 'None'}"
        )
    debug_log.append(f"Obstacles ({len(board.obstacles)}):")
    for piece in board.obstacles:
        debug_log.append(f"{pad:2}{toa(piece.board_pos)} {piece.board_pos}: {piece.name}")
    if not board.obstacles:
        debug_log[-1] += " None"
    debug_log.append(f"Piece groups ({len(board.piece_groups)}):")
    for group in board.piece_groups:
        debug_log.append(
            f"{pad:2}{group} ({len(board.piece_groups[group])}): "
            f"{', '.join(piece.name for piece in board.piece_groups[group])}"
        )
    if not board.piece_groups:
        debug_log[-1] += " None"
    debug_log.append(f"Custom pieces ({len(board.custom_pieces)}):")
    for piece, data in board.custom_pieces.items():
        debug_log.append(f"{pad:2}'{piece}': {save_custom_type(data)}")
    if not board.custom_pieces:
        debug_log[-1] += " None"
    debug_log.append(f"Past custom pieces ({len(board.past_custom_pieces)}):")
    for piece, data in board.past_custom_pieces.items():
        debug_log.append(f"{pad:2}'{piece}': {save_custom_type(data)}")
    if not board.past_custom_pieces:
        debug_log[-1] += " None"
    if board.custom_pawn != fide.Pawn:
        debug_log.append(f"Custom pawn: {board.custom_pawn.name} ({save_piece_type(board.custom_pawn)})")
    else:
        debug_log.append("Custom pawn: None")
    debug_log.append(f"Custom layout ({len(board.custom_layout)}):")
    for pos, piece in board.custom_layout.items():
        suffixes = []
        if piece.movement and piece.movement.total_moves:
            suffixes.append(f"Moves: {piece.movement.total_moves}")
        if piece.promoted_from:
            suffixes.append(f"Promoted from: {piece.promoted_from.name}")
        if piece.is_hidden is False:
            suffixes.append('Never hide')
        suffix = f" ({', '.join(suffixes)})" if suffixes else ''
        debug_log.append(f"{pad:2}{toa(pos)} {pos}: {piece}{suffix}")
    if not board.custom_layout:
        debug_log[-1] += " None"
    data = (board.load_dict or {}).get('promotions', {})
    for side in board.piece_set_ids:
        promotions = board.custom_promotions.get(side, {})
        debug_log.append(f"{side} custom promotion rules ({len(promotions)}):")
        for piece in promotions:
            debug_log.append(f"{pad:2}{piece.name} ({len(promotions[piece])}):")
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
                debug_log.append(f"{pad:4}{value} {fra(value)}: {piece_list if piece_list else 'None'}")
            if not promotions[piece]:
                debug_log[-1] += " None"
        if not promotions:
            debug_log[-1] += " None"
    data = (board.load_dict or {}).get('drops', {})
    for side in board.piece_set_ids:
        drops = board.custom_drops.get(side, {})
        debug_log.append(f"{side} custom drop rules ({len(drops)}):")
        for piece in drops:
            debug_log.append(f"{pad:2}{piece.name} ({len(drops[piece])}):")
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
                debug_log.append(f"{pad:4}{value} {fra(value)}: {piece_list if piece_list else 'None'}")
            if not drops[piece]:
                debug_log[-1] += " None"
        if not drops:
            debug_log[-1] += " None"
    for side in board.custom_extra_drops:
        debug_log.append(
            f"{side} starting drops ({len(board.custom_extra_drops[side])}): "
            f"{', '.join(piece.name for piece in board.custom_extra_drops[side]) or 'None'}"
        )
    for side in board.captured_pieces:
        debug_log.append(
            f"{side} drops ({len(board.captured_pieces[side])}): "
            f"{', '.join(piece.name for piece in board.captured_pieces[side]) or 'None'}"
        )
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
        order_rules = board.turn_rules.get(order)
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
                    if isinstance(allow_last, str) and allow_last not in {'*'}:
                        allow_last = f'"{allow_last}"'
                    if isinstance(block_last, str) and block_last not in {None}:
                        block_last = f'"{block_last}"'
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
                            if isinstance(allow_piece, str) and allow_piece not in {'*', ''}:
                                allow_piece = f'"{allow_piece}"'
                            if isinstance(block_piece, str) and block_piece not in {None, ''}:
                                block_piece = f'"{block_piece}"'
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
                                    if isinstance(allow_type, str) and allow_type not in {'*', ''}:
                                        allow_type = f'"{allow_type}"'
                                    if isinstance(block_type, str) and block_type not in {None, ''}:
                                        block_type = f'"{block_type}"'
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
                                        for block_action in sorted(allow_action_rules):
                                            action_string = (
                                                "Any action" if allow_action == '*' and block_action is None else
                                                f"{allow_action.capitalize()}" if block_action is None else
                                                f"NOT {block_action}" if allow_action == '*' else
                                                f"{allow_action.capitalize()}, NOT {block_action}"
                                            )
                                            check_rule = allow_action_rules[block_action]
                                            check_string = {
                                                0: "Any",
                                                1: "Only as check",
                                                -1: "Never as check",
                                            }.get(check_rule, "Unknown")
                                            debug_log.append(f"{pad:12}{action_string}: {check_rule} ({check_string})")
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
    debug_log.append(f"Move order ({len(start) + len(loop)}):")
    if start:
        debug_log.append(f"{pad:2}Start: ({len(start)}):")
        for i, data in enumerate(start):
            turn_side, turn_rules = data
            turn_rules = list(repack(turn_rules))
            for j, rule in enumerate(turn_rules):
                for string in ('action', 'last', 'piece', 'type'):
                    if rule and string in rule:
                        turn_rules[j] = copy(rule)
                        turn_rules[j][string] = unpack([t for t in repack(rule[string])])
            turn_rules = unpack(turn_rules)
            turn_suffix = '' if turn_rules is None else f", {turn_rules}"
            debug_log.append(f"{pad:4}{i + 1}: {turn_side}{turn_suffix}")
    if loop:
        pad = ''
        if start:
            debug_log.append(f"{pad:2}Loop: ({len(loop)}):")
            pad = '  '
        for i, data in enumerate(loop, len(start)):
            turn_side, turn_rules = data
            turn_rules = list(repack(turn_rules))
            for j, rule in enumerate(turn_rules):
                for string in ('action', 'last', 'piece', 'type'):
                    if rule and string in rule:
                        turn_rules[j] = copy(rule)
                        turn_rules[j][string] = unpack([t for t in repack(rule[string])])
            turn_rules = unpack(turn_rules)
            turn_suffix = '' if turn_rules is None else f", {turn_rules}"
            debug_log.append(f"{pad:2}{pad}{i + 1}: {turn_side}{turn_suffix}")
    if not start and not loop:
        debug_log[-1] += " None"
    for side in board.end_rules:
        debug_log.append(f"Win conditions for {side}:")
        for rule in board.end_rules[side]:
            debug_log.append(f"{pad:2}{rule.capitalize()}:")
            for group in board.end_rules[side][rule]:
                group_string = f'"{group}"' if group else "Any"
                group_value = board.end_rules[side][rule][group]
                debug_log.append(f"{pad:4}{group_string}: {group_value}")
    possible_moves = sum((
        sum(v.values(), []) for k, v in board.moves.get(board.turn_side, {}).items() if not isinstance(k, str)
    ), [])
    debug_log.append(f"Moves possible: {len(possible_moves)}")
    debug_log.append(f"Unique moves: {sum(len(i) for i in board.unique_moves()[board.turn_side].values())}")
    debug_log.append(f"Check side: {board.check_side if board.check_side else 'None'}")
    debug_log.append(f"Game over: {board.game_over}")
    debug_log.append(f"Action history ({len(board.move_history)}):")
    for i, move in enumerate(board.move_history):
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
    debug_log.append(f"Future action history ({len(board.future_move_history)}):")
    for i, move in enumerate(board.future_move_history[::-1], len(board.move_history)):
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
    if not board.future_move_history:
        debug_log[-1] += " None"
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
            for pos, piece in sorted(pieces, key=lambda x: x[0]):
                debug_log.append(f"{pad:4}{toa(pos)} {pos}: {piece.name}")
    if empty:
        debug_log[-1] += " None"
    debug_log.append(f"Roll seed: {board.roll_seed} (update: {board.board_config['update_roll_seed']})")
    debug_log.append(f"Piece set seed: {board.set_seed}")
    debug_log.append(f"Chaos set seed: {board.chaos_seed}")
    return debug_log