from __future__ import annotations

from collections import defaultdict
from copy import copy, deepcopy
from itertools import chain, product, zip_longest
from json import dumps, loads, JSONDecodeError
from math import ceil, floor, isqrt
from os import makedirs, name as os_name, system
from os.path import dirname, isfile, join
from random import Random
from sys import argv
from traceback import print_exc
from typing import Any

from PIL.ImageColor import getrgb
from arcade import key, MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT, Text
from arcade import Sprite, SpriteList, Window
from arcade import get_screens, start_render

from chess.color import colors, default_colors, trickster_colors
from chess.color import average, darken, desaturate, lighten, saturate
from chess.config import Config
from chess.data import base_rng, max_seed, get_set_data, get_set_name
from chess.data import default_board_width, default_board_height, default_size
from chess.data import min_width, min_height, min_size, max_size, size_step
from chess.data import action_types, end_types, penultima_textures, piece_groups
from chess.debug import debug_info, save_piece_data, save_piece_sets, save_piece_types
from chess.movement.base import BaseMovement
from chess.movement.move import Move
from chess.movement.types import AutoCaptureMovement, AutoRangedAutoCaptureRiderMovement
from chess.movement.types import CastlingMovement, CastlingPartnerMovement
from chess.movement.types import CloneMovement, DropMovement, ProbabilisticMovement
from chess.movement.util import Position, add, to_alpha as b26
from chess.movement.util import to_algebraic as toa, from_algebraic as fra, is_algebraic as isa
from chess.movement.util import to_algebraic_map as tom, from_algebraic_map as frm
from chess.pieces.groups.classic import Pawn, King
from chess.pieces.groups.colorbound import King as CBKing
from chess.pieces.piece import Piece, is_active
from chess.pieces.side import Side
from chess.pieces.types import Delayed, Delayed1, Slow
from chess.pieces.util import NoPiece, Obstacle, Block, Border, Shield, Void, Wall
from chess.save import condense, expand, condense_algebraic as cnd_alg, expand_algebraic as exp_alg, substitute
from chess.save import load_move, load_piece, load_rng, load_piece_type, load_custom_type, load_movement_type
from chess.save import save_move, save_piece, save_rng, save_piece_type, save_custom_type
from chess.util import get_filename, is_prefix_of, select_save_data, select_save_name
from chess.util import Default, Unset, base_dir, config_path, deduplicate, fits, sign, spell, unpack, repack


class Board(Window):
    def __init__(self):
        # super boring initialization stuff (bluh bluh)
        self.board_config = Config(config_path)
        if not isfile(config_path):
            self.board_config.save(config_path)

        self.border_cols, self.border_rows = [], []
        self.board_width, self.board_height = default_board_width, default_board_height
        self.visual_board_width = self.board_width + len(self.border_cols)
        self.visual_board_height = self.board_height + len(self.border_rows)
        self.square_size = default_size

        super().__init__(
            width=round((self.visual_board_width + 2) * self.square_size),
            height=round((self.visual_board_height + 2) * self.square_size),
            title='Chess',
            resizable=True,
            vsync=True,
            center_window=True,
            visible=False,
        )

        self.origin = self.width / 2, self.height / 2
        self.set_minimum_size(round(min_width), round(min_height))

        self.windowed_size = self.width, self.height
        self.windowed_square_size = self.square_size

        if self.board_config['color_id'] < 0 or self.board_config['color_id'] >= len(colors):
            self.board_config['color_id'] %= len(colors)
            self.board_config.save(config_path)

        self.color_index = self.board_config['color_id'] or 0  # index of the current color scheme
        self.color_scheme = colors[self.color_index]  # current color scheme
        self.background_color = self.color_scheme['background_color']  # background color
        self.log_data = []  # list of important logged strings
        self.verbose_data = []  # list of all logged strings
        self.verbose = self.board_config['verbose']  # whether to use verbose data for console output
        self.variant = ''  # name of the variant being played
        self.load_data = None  # last loaded data
        self.load_dict = None  # last loaded data, parsed from JSON
        self.load_path = None  # path to the last loaded data file
        self.save_info = [None]  # list of comment strings in save data
        self.save_data = None  # last saved data
        self.save_path = None  # path to the last saved data file
        self.save_loaded = False  # whether a save was successfully loaded
        self.game_loaded = False  # whether the game had successfully loaded
        self.skip_mouse_move = 0  # setting this to >=1 skips mouse movement events
        self.skip_caption_update = False  # setting this to True skips window caption updates
        self.highlight_square = None  # square that is being highlighted with the keyboard
        self.hovered_square = None  # square we are currently hovering over
        self.clicked_square = None  # square we clicked on
        self.selected_square = None  # square selected for moving
        self.square_was_clicked = False  # used to discern two-click moving from dragging
        self.piece_was_selected = False  # used to discern between selecting a piece and moving it
        self.held_buttons = 0  # mouse button that was pressed
        self.promotion_piece = None  # piece that is currently being promoted
        self.promotion_area = {}  # squares to draw possible promotions on
        self.promotion_area_drops = {}  # dropped pieces matching the squares above
        self.action_count = 0  # current number of actions taken
        self.ply_count = 0  # current overall move number
        self.ply_simulation = 0  # current number of look-ahead moves
        self.move_history = []  # list of moves made so far
        self.future_move_history = []  # list of moves that were undone, in reverse order
        self.roll_history = []  # list of rolls made so far (used for ProbabilisticMovement)
        self.move_seed = None  # seed for move selection
        self.move_rng = None  # random number generator for move selection
        self.roll_seed = None  # seed for probabilistic movement
        self.roll_rng = None  # random number generator for probabilistic movement
        self.set_seed = None  # seed for piece set selection
        self.set_rng = None  # random number generator for piece set selection
        self.areas = {}  # special areas on the board
        self.initial_turns = 0  # amount of initial turns
        self.turn_order = [(Side.WHITE, {}), (Side.BLACK, {})]  # order of turns
        self.turn_data = [0, Side.NONE, 0]  # [turn number, turn side, move number]
        self.turn_side = Side.NONE  # side whose turn it is
        self.turn_rules = None  # rules of movement for the current turn
        self.end_rules = {}  # conditions under which the game ends
        self.end_data = {}  # additional data for the game end rules
        self.end_condition = None  # condition that has been met to end the game
        self.end_value = 0  # value of the game ending condition, if applicable
        self.end_group = None  # group of the game ending condition, if applicable
        self.win_side = Side.NONE  # side that has won the game, if any
        self.check_side = Side.NONE  # side that is currently in check, if any
        self.check_groups = set()  # groups that are currently in check
        self.use_drops = self.board_config['use_drops']  # whether pieces can be dropped
        self.hide_pieces = self.board_config['hide_pieces'] % 3  # 0: don't hide, 1: hide all, 2: penultima mode
        self.hide_move_markers = self.board_config['hide_moves']  # whether to hide the move markers; None uses above
        self.hide_edit_pieces = False  # whether to mark pieces placed in edit mode as hidden
        self.auto_moves = True  # whether to skip move animations if allowed
        self.flip_mode = False  # whether the board is flipped
        self.edit_mode = False  # allows to edit the board position if set to True
        self.game_over = False  # act 6 act 6 intermission 3 (game over)
        self.trickster_color_index = 0  # hey wouldn't it be funny if there was an easter egg here
        self.trickster_color_delta = 0  # but it's not like that's ever going to happen right
        self.trickster_angle_delta = 0  # this is just a normal chess game after all
        self.no_piece = NoPiece(self)  # piece that represents an empty square
        self.pieces = []  # list of pieces on the board
        self.piece_counts = {}  # number of pieces of each type for each side
        self.piece_limits = {}  # maximum number of pieces of each type for each side
        self.piece_set_ids = {Side.WHITE: 0, Side.BLACK: 0}  # ids of piece sets to use for each side
        self.piece_set_names = {Side.WHITE: '', Side.BLACK: ''}  # names of piece sets to use for each side
        self.edit_piece_set_id = None  # id of piece set used when placing pieces in edit mode, None uses current sets
        self.chaos_mode = self.board_config['chaos_mode']  # 0: no, 1: match pos, 2: match pos asym, 3: any, 4: any asym
        self.chaos_sets = {}  # piece sets generated in chaos mode
        self.piece_sets = {Side.WHITE: [], Side.BLACK: []}  # types of pieces each side starts with
        self.piece_groups = {}  # groups of pieces that share certain properties
        self.drops = {Side.WHITE: {}, Side.BLACK: {}}  # drop options, as {side: {was: {pos: as}}}
        self.promotions = {Side.WHITE: {}, Side.BLACK: {}}  # promotion options, as {side: {from: {pos: [to]}}}
        self.edit_promotions = {Side.WHITE: [], Side.BLACK: []}  # types of pieces each side can place in edit mode
        self.movable_pieces = {Side.WHITE: [], Side.BLACK: []}  # pieces that can be moved by each side
        self.area_groups = {Side.WHITE: {}, Side.BLACK: {}}  # groups of pieces that have reached certain positions
        self.royal_groups = {Side.WHITE: {}, Side.BLACK: {}}  # groups that are currently considered royal
        self.royal_pieces = {Side.WHITE: [], Side.BLACK: []}  # these have to stay on the board and should be protected
        self.royal_markers = {Side.WHITE: set(), Side.BLACK: set()}  # squares where the side's royal pieces are
        self.anti_royal_pieces = {Side.WHITE: [], Side.BLACK: []}  # these need to remain attacked at all times
        self.anti_royal_markers = {Side.WHITE: set(), Side.BLACK: set()}  # squares where the side's anti-royals are
        self.en_passant_targets = {Side.WHITE: {}, Side.BLACK: {}}  # pieces that can be captured en passant
        self.en_passant_markers = {Side.WHITE: {}, Side.BLACK: {}}  # where the side's pieces can be captured e.p.
        self.royal_ep_targets = {Side.WHITE: {}, Side.BLACK: {}}  # royal pieces that can be captured en passant
        self.royal_ep_markers = {Side.WHITE: {}, Side.BLACK: {}}  # where the side's royals can be captured e.p.
        self.auto_ranged_pieces = {Side.WHITE: [], Side.BLACK: []}  # pieces that auto-capture anywhere they can move to
        self.auto_capture_markers = {Side.WHITE: {}, Side.BLACK: {}}  # squares where the side's pieces can auto-capture
        self.relay_pieces = {Side.WHITE: {}, Side.BLACK: {}}  # pieces that are relaying powers onto certain squares
        self.relay_markers = {Side.WHITE: {}, Side.BLACK: {}}  # squares the side's pieces are relaying their powers to
        self.probabilistic_pieces = {Side.WHITE: [], Side.BLACK: []}  # pieces that can move probabilistically
        self.probabilistic_piece_history = []  # list of probabilistic piece positions for every ply
        self.obstacles = []  # list of obstacles (neutral pieces that block movement and cannot move)
        self.penultima_pieces = {Side.WHITE: {}, Side.BLACK: {}}  # piece textures that are used for penultima mode
        self.past_custom_pieces = {}  # custom piece types that have been used before a reset of custom data
        self.custom_pawns = None  # custom pawn types
        self.custom_pieces = {}  # custom piece types
        self.custom_layout = {}  # custom starting layout of the board
        self.custom_areas = {}  # custom areas on the board
        self.custom_promotions = {}  # custom promotion options
        self.custom_drops = {}  # custom drop options
        self.custom_extra_drops = {}  # custom extra drops, as {side: [was]}
        self.custom_turn_order = []  # custom turn order options
        self.custom_end_rules = {}  # custom game end conditions
        self.captured_pieces = {Side.WHITE: [], Side.BLACK: []}  # pieces captured by each side
        self.alias_dict = {}  # dictionary of aliases for save data
        self.moves = {Side.WHITE: {}, Side.BLACK: {}}  # dictionary of valid moves from any square
        self.chain_moves = {Side.WHITE: {}, Side.BLACK: {}}  # dictionary of moves chained from a certain move (from/to)
        self.chain_start = None  # move that started the current chain (if any)
        self.theoretical_moves = {Side.WHITE: {}, Side.BLACK: {}}  # dictionary of theoretical moves from any square
        self.moves_queried = {Side.WHITE: False, Side.BLACK: False}  # whether moves have been queried for each side
        self.theoretical_moves_queried = {Side.WHITE: False, Side.BLACK: False}  # same for theoretical moves
        self.display_moves = {Side.WHITE: False, Side.BLACK: False}  # whether to display moves for each side
        self.display_theoretical_moves = {Side.WHITE: False, Side.BLACK: False}  # same for theoretical moves
        self.move_type_markers = False  # whether to display type-based move markers
        self.anchor = 0, 0  # used to have the board scale from the origin instead of the center
        self.highlight = Sprite("assets/util/selection.png")  # sprite for the highlight marker
        self.highlight.color = self.color_scheme['highlight_color']  # color it according to the color scheme
        self.highlight.scale = self.square_size / self.highlight.texture.width  # scale it to the size of a square
        self.selection = Sprite("assets/util/selection.png")  # sprite for the selection marker
        self.selection.color = self.color_scheme['selection_color']  # color it according to the color scheme
        self.selection.scale = self.square_size / self.selection.texture.width  # scale it to the size of a square
        self.active_piece = None  # piece that is currently being moved
        self.is_active = True  # whether the window is active or not
        self.is_focused = True  # whether the mouse cursor is over the window
        self.label_list = []  # labels for the rows and columns
        self.board_sprite_list = SpriteList()  # sprites for the board squares
        self.move_sprite_list = SpriteList()  # sprites for the move markers
        self.type_sprite_list = SpriteList()  # sprites for the type-based move markers
        self.piece_sprite_list = SpriteList()  # sprites for the pieces
        self.promotion_area_sprite_list = SpriteList()  # sprites for the promotion area background tiles
        self.promotion_piece_sprite_list = SpriteList()  # sprites for the possible promotion pieces
        self.save_interval = 0  # time since the last autosave

        # load piece set ids from the config
        for side in self.piece_set_ids:
            self.piece_set_ids[side] = self.board_config[f'{side.key()}id'] or self.piece_set_ids[side]
        self.edit_piece_set_id = self.board_config['edit_id']

        # initialize random number seeds and generators
        self.roll_seed = (
            self.board_config['roll_seed']
            if self.board_config['roll_seed'] is not None
            else base_rng.randint(0, max_seed)
        )
        self.roll_rng = None  # will be initialized later
        self.set_seed = (
            self.board_config['set_seed']
            if self.board_config['set_seed'] is not None
            else base_rng.randint(0, max_seed)
        )
        self.set_rng = Random(self.set_seed)
        self.chaos_seed = (
            self.board_config['chaos_seed']
            if self.board_config['chaos_seed'] is not None
            else base_rng.randint(0, max_seed)
        )
        self.chaos_rng = Random(self.chaos_seed)

        # log verbose data
        if self.verbose is None:
            self.log(f"Info: Output suppressed", False)
        else:
            self.log(f"Info: Verbose output: {'ON' if self.verbose else 'OFF'}", False)
        self.log(f"Info: Roll seed: {self.roll_seed}", False)
        self.log(f"Info: Piece set seed: {self.set_seed}", False)
        self.log(f"Info: Chaos set seed: {self.chaos_seed}", False)

        # set up the board
        self.resize_board()
        self.load(argv[1] if len(argv) > 1 else None)
        if not self.save_loaded:
            self.reset_custom_data()
            self.reset_board()
            self.log_special_modes()
        self.game_loaded = True

    def get_board_position(
        self,
        pos: tuple[float, float],
        size: float | None = None,
        origin: tuple[float, float] | None = None,
        width: int | None = None,
        height: int | None = None,
        border_cols: list[int] | None = None,
        border_rows: list[int] | None = None,
        flip: bool | None = None,
    ) -> Position:
        x, y = pos
        size = size or self.square_size
        origin = origin or self.origin
        width = width or self.visual_board_width
        height = height or self.visual_board_height
        border_cols = border_cols or self.border_cols
        border_rows = border_rows or self.border_rows
        flip = flip if flip is not None else self.flip_mode
        board_size = width, height
        col = round((x - origin[0]) / size + (board_size[0] - 1) / 2)
        row = round((y - origin[1]) / size + (board_size[1] - 1) / 2)
        for border_col in border_cols:
            if col > border_col:
                col -= 1
            elif col == border_col:
                col = -1
                break
        for border_row in border_rows:
            if row > border_row:
                row -= 1
            elif row == border_row:
                row = -1
                break
        col, row = (board_size[0] - 1 - col, board_size[1] - 1 - row) if flip else (col, row)
        return row, col

    def get_screen_position(
        self,
        pos: Position,
        size: float | None = None,
        origin: tuple[float, float] | None = None,
        width: int | None = None,
        height: int | None = None,
        border_cols: list[int] | None = None,
        border_rows: list[int] | None = None,
        flip: bool | None = None,
    ) -> tuple[float, float]:
        row, col = pos
        size = size or self.square_size
        origin = origin or self.origin
        width = width or self.visual_board_width
        height = height or self.visual_board_height
        border_cols = border_cols or self.border_cols
        border_rows = border_rows or self.border_rows
        flip = flip if flip is not None else self.flip_mode
        board_size = width, height
        col, row = (board_size[0] - 1 - col, board_size[1] - 1 - row) if flip else (col, row)
        col += sum(1 for border_col in border_cols if col >= border_col)
        row += sum(1 for border_row in border_rows if row >= border_row)
        x = (col - (board_size[0] - 1) / 2) * size + origin[0]
        y = (row - (board_size[1] - 1) / 2) * size + origin[1]
        return x, y

    # From now on we shall unanimously assume that the first coordinate corresponds to row number (AKA vertical axis).

    @staticmethod
    def get_square_color(pos: Position) -> int:
        return (pos[0] + pos[1]) % 2

    def is_dark_square(self, pos: Position) -> bool:
        return self.get_square_color(pos) == 0

    def is_light_square(self, pos: Position) -> bool:
        return self.get_square_color(pos) == 1

    def get_piece(self, pos: Position | None) -> Piece:
        return self.no_piece if self.not_on_board(pos) else self.pieces[pos[0]][pos[1]]

    def get_side(self, pos: Position | None) -> Side:
        return self.get_piece(pos).side

    def get_turn(self, offset: int = 0, origin: int | None = None) -> int:
        if origin is None:
            origin = self.ply_count
        ply_count = origin + offset
        return (
            (ply_count - 1 - self.initial_turns) % (len(self.turn_order) - self.initial_turns) + self.initial_turns
            if ply_count > self.initial_turns else ply_count - 1
        )

    def get_turn_side(self, offset: int = 0, origin: int | None = None) -> Side:
        index = self.get_turn(offset, origin)
        if index < 0:
            return Side.NONE
        return self.turn_order[index][0]

    def get_order(self, rules: dict = None) -> list[int]:
        rules = rules or self.turn_rules or {0}
        return sorted(rules, reverse=True)

    def get_promotion_side(self, piece: Piece):
        return (
            piece.side if piece.side in {Side.WHITE, Side.BLACK} else
            (Side.WHITE if piece.board_pos[0] < self.board_height / 2 else Side.BLACK)
        )

    def shift_ply(self, offset: int) -> None:
        if self.ply_count <= 0:
            self.ply_count = 1
            self.load_turn_rules()
            self.turn_data = [1, self.turn_side, 1]
            return
        direction = sign(offset)
        for i in range(abs(offset)):
            self.ply_count += direction
            turn_side = self.get_turn_side()
            if self.turn_side == turn_side:
                self.turn_data[2] += direction
            else:
                self.turn_data[1] = turn_side
                if direction > 0:
                    if turn_side == self.turn_order[0][0]:
                        self.turn_data[0] += 1
                    self.turn_data[2] = 1
                else:
                    if self.turn_side == self.turn_order[0][0]:
                        self.turn_data[0] -= 1
                    self.turn_data[2] = 0
                    while self.get_turn_side(-self.turn_data[2]) == turn_side:
                        self.turn_data[2] += 1
        self.load_turn_rules()

    def fits(self, template: str, data: Any):
        if isinstance(data, Move):
            return self.fits(template, (data.tag or data.movement_type or ''))
        if isinstance(data, (Piece, BaseMovement)):
            data = type(data)
        if isinstance(data, type) and issubclass(data, Piece):
            return fits(template, (data.group(), data.name, data.type()))
        if isinstance(data, type) and issubclass(data, BaseMovement):
            return fits(template, data.__name__)
        return fits(template, data)

    def set_position(self, piece: Piece, pos: Position) -> None:
        piece.board_pos = pos
        piece.position = self.get_screen_position(pos)

    def reset_position(self, piece: Piece) -> None:
        self.set_position(piece, piece.board_pos)

    def on_board(self, pos: Position | None) -> bool:
        return not self.not_on_board(pos)

    def not_on_board(self, pos: Position | None) -> bool:
        return pos is None or pos[0] < 0 or pos[0] >= self.board_height or pos[1] < 0 or pos[1] >= self.board_width

    def not_a_piece(self, pos: Position | None) -> bool:
        return isinstance(self.get_piece(pos), NoPiece)

    def nothing_selected(self) -> bool:
        return self.not_a_piece(self.selected_square)

    def select_piece(self, pos: Position | None) -> None:
        if self.not_on_board(pos):
            return  # there's nothing to select off the board
        if pos == self.selected_square:
            return  # piece already selected, nothing else to do

        # set selection properties for the selected square
        self.selected_square = pos
        self.selection.color = self.color_scheme['selection_color']
        self.selection.position = self.get_screen_position(pos)

        # make the piece displayed on top of everything else
        piece = self.get_piece(self.selected_square)
        self.piece_sprite_list.remove(piece)
        self.active_piece = piece

        self.show_moves()

    def deselect_piece(self) -> None:
        self.selection.color = (0, 0, 0, 0)
        self.square_was_clicked = False
        self.piece_was_selected = False
        self.clicked_square = None

        if self.nothing_selected():
            return

        # move the piece to general piece node
        piece, self.active_piece = self.active_piece, None
        self.reset_position(piece)
        self.piece_sprite_list.append(piece)

        self.selected_square = None
        self.show_moves()

    def reset_board(self, update: bool | None = True, log: bool = True) -> None:
        self.save_interval = 0

        self.deselect_piece()
        self.clear_relay_markers()
        self.clear_en_passant_markers()
        self.clear_auto_capture_markers()
        self.reset_captures()

        self.end_data = {
            side: {
                condition: {
                    group: 0 for group in data
                } for condition, data in rules.items()
            } for side, rules in self.end_data.items()
        }
        self.end_value = 0
        self.end_group = None
        self.end_condition = None
        self.win_side = Side.NONE
        self.game_over = False
        self.edit_mode = False
        self.chain_start = None
        self.promotion_piece = None
        self.action_count = 0
        self.ply_count = 0
        self.turn_side = Side.NONE
        self.turn_data = [0, Side.NONE, 0]

        for sprite_list in self.piece_sprite_list, self.promotion_piece_sprite_list, self.promotion_area_sprite_list:
            sprite_list.clear()
            for sprite in sprite_list:
                sprite_list.remove(sprite)

        self.piece_sets, self.piece_set_names = self.get_piece_sets()

        if self.chaos_mode:
            no_chaos = True
            for v in self.piece_set_ids.values():
                if v is None or v < 0:
                    no_chaos = False
                    break
            if no_chaos:
                self.chaos_mode = 0

        if log:
            self.log_armies()

        self.shift_ply(+1)

        if update is None:
            update = not self.move_history

        if update:
            self.edit_piece_set_id = self.board_config['edit_id']
            self.roll_history = []
            self.future_move_history = []
            self.probabilistic_piece_history = []
            self.reset_drops()
            self.reset_promotions()
            self.reset_edit_promotions()
            self.reset_penultima_pieces()
        else:
            self.future_move_history += self.move_history[::-1]

        if self.roll_rng is None:
            self.roll_rng = Random(self.roll_seed)
        elif update:
            if self.board_config['update_roll_seed']:
                self.roll_seed = self.roll_rng.randint(0, max_seed)
            self.roll_rng = Random(self.roll_seed)

        self.move_history = []

        self.pieces = []

        empty_row = [NoPiece] * self.board_width
        piece_row = ['piece'] * self.board_width
        pawn_row = ['pawn'] * self.board_width

        white_row = [Side.WHITE] * self.board_width
        black_row = [Side.BLACK] * self.board_width
        neutral_row = [Side.NONE] * self.board_width

        types = [piece_row, pawn_row] + [empty_row] * (self.board_height - 4) + [pawn_row, piece_row]
        sides = [white_row, white_row] + [neutral_row] * (self.board_height - 4) + [black_row, black_row]

        for row in range(self.board_height):
            self.pieces += [[]]

        for row, col in product(range(self.board_height), range(self.board_width)):
            if self.custom_layout:
                self.pieces[row].append(
                    copy(self.custom_layout[(row, col)])
                    if (row, col) in self.custom_layout
                    else NoPiece(self, pos=(row, col))
                )
            else:
                piece_type = types[row][col]
                piece_side = sides[row][col]
                if piece_type == 'piece':
                    if col < len(self.piece_sets[piece_side]):
                        piece_type = self.piece_sets[piece_side][col] or NoPiece
                    else:
                        piece_type = NoPiece
                elif piece_type == 'pawn':
                    custom_pawns = (
                        self.custom_pawns.get(piece_side)
                        if isinstance(self.custom_pawns, dict)
                        else self.custom_pawns
                    )
                    if custom_pawns is None:
                        piece_type = Pawn
                    elif len(custom_pawns) == 1:
                        piece_type = custom_pawns[0]
                    else:
                        piece_type = NoPiece
                elif isinstance(piece_type, str):
                    piece_type = NoPiece  # just in case.
                self.pieces[row].append(
                    piece_type(board=self, pos=(row, col), side=piece_side)
                )
            if not isinstance(self.pieces[row][col], (NoPiece, Obstacle)):
                self.update_piece(self.pieces[row][col])
                self.pieces[row][col].set_color(
                    self.color_scheme.get(
                        f"{self.pieces[row][col].side.key()}piece_color",
                        self.color_scheme['piece_color']
                    ),
                    self.color_scheme['colored_pieces']
                )
            self.pieces[row][col].scale = self.square_size / self.pieces[row][col].texture.width
            self.piece_sprite_list.append(self.pieces[row][col])

        self.unload_end_data()
        self.load_pieces()
        self.load_check()
        self.update_end_data()
        self.load_moves()
        self.reload_end_data()
        self.update_status()

    def dump_board(self, partial: bool = False) -> str:
        wh = self.board_width, self.board_height
        whn = *wh, {}
        whc = *wh, {k: v for k, v in self.custom_areas.items() if isinstance(v, set)}
        wha = defaultdict(lambda: whn, {side: (*wh, self.areas.get(side) or {}) for side in (Side.WHITE, Side.BLACK)})
        data = {
            'variant': self.variant,
            'board_size': [*wh],
            'borders': [toa((-1, col)) for col in self.border_cols] + [toa((row, -1)) for row in self.border_rows],
            'areas': {
                name: {
                    side.value: unpack(list(tom(area, *whn))) for side, area in data.items()
                } if isinstance(data, dict) else unpack(list(tom(data, *whn)))
                for name, data in self.custom_areas.items()
            },
            'window_size': list(self.windowed_size),
            'square_size': self.windowed_square_size,
            'flip_mode': self.flip_mode,
            'color_index': self.color_index,
            'color_scheme': {
                k: list(v) if isinstance(v, tuple) else v
                for k, v in (colors[self.color_index] if self.color_index is not None else self.color_scheme).items()
            },
            'selection': toa(self.selected_square) if self.selected_square else None,
            'set_blocklist': self.board_config['block_ids'],
            'chaos_blocklist': self.board_config['block_ids_chaos'],
            'set_ids': {side.value: piece_set_id for side, piece_set_id in self.piece_set_ids.items()},
            'sets': {
                side.value: [save_piece_type(t) if t is not NoPiece else '' for t in piece_set]
                for side, piece_set in self.piece_sets.items()
            },
            'groups': {k: unpack([save_piece_type(t) for t in v]) for k, v in self.piece_groups.items()},
            'limits': {
                k.value if isinstance(k, Side) else k: {g: v for g, v in d.items()} if isinstance(k, Side) else d
                for k, d in self.piece_limits.items()
            },
            'pawn': {
                k.value: unpack([save_piece_type(t) for t in v]) for k, v in self.custom_pawns.items()
            } if isinstance(self.custom_pawns, dict) else
            unpack([save_piece_type(t) for t in self.custom_pawns]) if self.custom_pawns is not None else None,
            'pieces': cnd_alg({
                p.board_pos: save_piece(p.on(None))
                for pieces in [*self.movable_pieces.values(), self.obstacles] for p in pieces
            }, *whc),
            'custom': {k: save_custom_type(v) for k, v in self.custom_pieces.items()},
            'layout': cnd_alg({pos: save_piece(p.on(None)) for pos, p in self.custom_layout.items()}, *whc),
            'promotions': {
                side.value: {
                    save_piece_type(f): cnd_alg({
                        p: unpack([
                            (save_piece if isinstance(t, Piece) else save_piece_type)(t) for t in l
                        ]) for p, l in s.items()
                    }, *wha[side]) for f, s in d.items()
                } for side, d in self.custom_promotions.items()
            },
            'drops': {
                side.value: {
                    save_piece_type(f): cnd_alg({
                        p: unpack([
                            (save_piece if isinstance(t, Piece) else save_piece_type)(t) for t in l
                        ]) for p, l in s.items()
                    }, *wha[side]) for f, s in d.items()
                } for side, d in self.custom_drops.items()
            },
            'extra': {
                side.value: [save_piece_type(p) for p in pieces]
                for side, pieces in self.custom_extra_drops.items()
            },
            'captured': {
                side.value: [save_piece_type(p) for p in pieces]
                for side, pieces in self.captured_pieces.items() if pieces
            },
            'moves': [save_move(m) for m in self.move_history],
            'future': [save_move(m) for m in self.future_move_history[::-1]],
            'rolls': {n: {toa(pos): d[pos] for pos in sorted(d)} for n, d in enumerate(self.roll_history) if d},
            'roll_piece_history': {
                n: {toa(pos): save_piece_type(t) for pos, t in sorted(d, key=lambda x: x[0])}
                for n, d in enumerate(self.probabilistic_piece_history) if d
            },
            'promotion': save_piece(self.promotion_piece),
            'chain_start': save_move(self.chain_start),
            'chain_moves': [
                save_move(m)
                for to, moves in self.moves[self.chain_start.piece.side][self.chain_start.piece.board_pos].items()
                for m in moves
            ] if self.chain_start else [],
            'ply': self.ply_count,
            'turn': [self.turn_data[0], self.turn_data[1].value, self.turn_data[2]],
            'order': [
                side[0].value if side[1] is None else
                [side[0].value, unpack([{k: v for k, v in {
                    'order': d.get('order'),
                    'state': d.get('state', 0),
                    'last': unpack([i for i in d.get('last', [])]),
                    'piece': unpack([t for t in d.get('piece', [])]),
                    'type': unpack([t for t in d.get('type', [])]),
                    'action': unpack([t for t in d.get('action', [])]),
                    'check': d.get('check', 0),
                }.items() if v} for d in side[1]])]
                for side in self.custom_turn_order
            ],
            'end': {
                (side.value if isinstance(side, Side) else side): {
                    group: value for group, value in rules.items()
                } if isinstance(rules, dict) else rules
                for side, rules in self.custom_end_rules.items()
            },
            'count': {
                side.value: short_side_data for side, side_data in self.end_data.items() if (short_side_data := {
                    word: data for word in self.custom_end_rules.get(side, self.custom_end_rules) if (data := {
                        group: v for group, v in side_data.get(end_types.get(word), {}).items() if v and (
                            (condition := end_types.get(word)) in {'check', 'capture'} or condition == 'checkmate'
                            and ((need := self.end_rules.get(side, {}).get(condition, {}).get(group, 0))
                            and isinstance(need, int) and abs(need) > 1)
                        )
                    })
                })
            },
            'edit': self.edit_mode,
            'edit_promotion': self.edit_piece_set_id,
            'hide_pieces': self.hide_pieces,
            'hide_moves': self.hide_move_markers,
            'use_drops': self.use_drops,
            'chaos_mode': self.chaos_mode,
            'chaos_seed': self.chaos_seed,
            'set_seed': self.set_seed,
            'roll_seed': self.roll_seed,
            'roll_update': self.board_config['update_roll_seed'],
        }
        for k, v in {
            'chaos': (self.chaos_seed, self.chaos_rng),
            'set': (self.set_seed, self.set_rng),
            'roll':  (self.roll_seed, self.roll_rng),
        }.items():
            seed, rng = v
            new_rng = Random(seed)
            if rng.getstate() != new_rng.getstate():
                data[f"{k}_state"] = save_rng(rng)
        if partial and self.load_dict is not None:
            data = {k: v for k, v in data.items() if k in self.load_dict}
        if self.alias_dict:
            data = {'alias': self.alias_dict, **condense(data, self.alias_dict, self.board_config['recursive_aliases'])}
        indent = self.board_config['save_indent']
        if indent is None:
            return dumps(data, separators=(',', ':'), ensure_ascii=False)
        else:
            return dumps(data, indent=indent, ensure_ascii=False)

    def load_board(self, dump: str, with_history: bool = False) -> bool:
        try:
            data = loads(dump)
        except JSONDecodeError:
            self.log("Error: Malformed save data")
            print_exc()
            return False

        if not isinstance(data, dict):
            self.log(f"Error: Invalid save format (expected dict, but got {type(data)})")
            return False

        if self.chain_start or self.promotion_piece:
            self.undo_last_finished_move()
            self.update_caption()

        old_pieces = {
            p.board_pos: save_piece(p.on(None))
            for pieces in [*self.movable_pieces.values(), self.obstacles] for p in pieces
        }

        self.save_interval = 0
        self.save_loaded = False
        success = True

        self.deselect_piece()
        self.clear_relay_markers()
        self.clear_en_passant_markers()
        self.clear_auto_capture_markers()
        self.end_value = 0
        self.end_group = None
        self.end_condition = None
        self.win_side = Side.NONE
        self.game_over = False
        self.action_count = 0

        self.alias_dict = data.get('alias', {})
        if 'alias' in data:
            del data['alias']
        if self.alias_dict:
            data = expand(data, self.alias_dict, self.board_config['recursive_aliases'])

        subs_dict = {}
        for side, piece_set in self.piece_sets.items():
            value = side.value
            subs_dict[value] = {}
            i = 0
            for piece_type in piece_set:
                if piece_type and not issubclass(piece_type, NoPiece):
                    i += 1
                    subs_dict[value][i] = save_piece_type(piece_type)
            if isinstance(self.custom_pawns, dict):
                pawns = self.custom_pawns.get(value)
            else:
                pawns = self.custom_pawns
            if pawns is None:
                pawns = {0: Pawn}
            elif isinstance(pawns, list):
                pawns = {i: Pawn for i in range(len(pawns))}
            for i, pawn in pawns.items():
                subs_dict[value][-i] = save_piece_type(pawn)
        for i in {x for side_dict in subs_dict.values() for x in side_dict.keys()}:
            value = None
            for side, side_dict in subs_dict.items():
                if value is None:
                    value = side_dict.get(i)
                elif value != side_dict.get(i):
                    value = None
                    break
            if value is not None:
                subs_dict.setdefault(Side.NONE.value, {})[i] = value
        data = substitute(data, subs_dict)

        self.variant = data.get('variant', '')

        # might have to add more error checking to saving/loading, even if at the cost of slight redundancy.
        # who knows when someone decides to introduce a breaking change and absolutely destroy all the saves
        board_size = tuple(data.get('board_size', (self.board_width, self.board_height)))
        borders = [fra(t) for t in data.get('borders', [])]
        borders = [t[1] for t in borders if t[0] == -1], [t[0] for t in borders if t[1] == -1]
        self.resize_board(*board_size, *borders, update=False)

        wh = self.board_width, self.board_height
        whn = *wh, {}
        self.custom_areas = {
            name: {
                Side(int(side)): set(frm(repack(area), *whn)) for side, area in data.items()
            } if isinstance(data, dict) else set(frm(repack(data), *whn))
            for name, data in data.get('areas', {}).items()
        }
        self.reset_areas()
        whc = *wh, {k: v for k, v in self.custom_areas.items() if isinstance(v, set)}
        wha = defaultdict(lambda: whn, {side: (*wh, self.areas.get(side) or {}) for side in (Side.WHITE, Side.BLACK)})

        window_size = data.get('window_size')
        square_size = data.get('square_size')
        if window_size is not None:
            self.resize(*window_size)
        elif square_size is not None:
            self.resize(
                round((self.visual_board_width + 2) * square_size),
                round((self.visual_board_height + 2) * square_size)
            )
        old_flip_mode = self.flip_mode
        new_flip_mode = data.get('flip_mode', self.flip_mode)
        if new_flip_mode != old_flip_mode:
            self.flip_board()
        new_square_size = min(self.width / (self.visual_board_width + 2), self.height / (self.visual_board_height + 2))
        if window_size is not None and square_size is not None and new_square_size != square_size:
            self.log(f"Error: Square size does not match (was {square_size}, but is {new_square_size})")

        self.color_index = data.get('color_index', self.color_index)
        self.color_scheme = colors[self.color_index] if self.color_index is not None else default_colors
        old_color_scheme = data.get('color_scheme', self.color_scheme)
        for k, v in self.color_scheme.items():
            old = old_color_scheme.get(k)
            old = None if old is None else tuple(old) if isinstance(v, tuple) else old
            if v != old:
                self.color_scheme[k] = v if old is None else old  # first time when we attempt to fully restore old data
                # in all cases before we had to pick one or the other, but here we can try to reload the save faithfully
                if self.color_index is not None:  # show warning if the defined color scheme doesn't match the saved one
                    old = 'undefined' if old is None else old
                    self.log(f"Error: Color scheme doesn't match ({k} was {old}, but is {v})")
        for k, old in old_color_scheme.items():
            if k not in self.color_scheme:
                self.color_scheme[k] = old
                if self.color_index is not None:
                    v = 'undefined'
                    self.log(f"Error: Color scheme doesn't match ({k} was {old}, but is {v})")

        self.board_config['block_ids'] = data.get('set_blocklist', self.board_config['block_ids'])
        self.board_config['block_ids_chaos'] = data.get('chaos_blocklist', self.board_config['block_ids_chaos'])

        self.hide_pieces = data.get('hide_pieces', self.hide_pieces)
        self.hide_move_markers = data.get('hide_moves', self.hide_move_markers)
        self.use_drops = data.get('use_drops', self.use_drops)
        self.chaos_mode = data.get('chaos_mode', self.chaos_mode)
        self.edit_mode = data.get('edit', self.edit_mode)
        self.edit_piece_set_id = data.get('edit_promotion', self.edit_piece_set_id)

        chaos_seed = data.get('chaos_seed')
        if chaos_seed is not None:
            self.chaos_seed = chaos_seed
            self.chaos_rng = Random(self.chaos_seed)
        set_seed = data.get('set_seed')
        if set_seed is not None:
            self.set_seed = set_seed
            self.set_rng = Random(self.set_seed)
        roll_seed = data.get('roll_seed')
        if roll_seed is not None:
            self.roll_seed = roll_seed
            self.roll_rng = Random(self.roll_seed)
        self.board_config['update_roll_seed'] = data.get('roll_update', self.board_config['update_roll_seed'])

        self.past_custom_pieces = {**self.past_custom_pieces, **self.custom_pieces}
        custom_data = data.get('custom', {})
        self.custom_pieces = {k: load_custom_type(v, k) for k, v in custom_data.items()}
        c = self.custom_pieces
        self.piece_groups = {
            k: [load_piece_type(t, c) for t in repack(v)] for k, v in data.get('groups', {}).items()
        }
        for group, piece_list in self.piece_groups.items():
            for piece_type in piece_list:
                piece_type.group_str = group
        self.piece_limits = {
            Side(int(k)) if k.isdigit() else k: {g: v for g, v in d.items()} if k.isdigit() else d
            for k, d in data.get('limits', {}).items()
        }
        custom_pawns = data.get('pawn')
        self.custom_pawns = ({
            Side(int(v)): [load_piece_type(t, c) for t in repack(l)] for v, l in custom_pawns.items()
        } if isinstance(custom_pawns, dict) else
        [load_piece_type(t, c) for t in repack(custom_pawns)] if custom_pawns is not None else None)
        self.custom_promotions = {
            Side(int(v)): {
                load_piece_type(f, c): {
                    p: [
                        (load_piece_type(t, c) if isinstance(t, str) else load_piece(t, self, c)) for t in repack(l)
                    ] for p, l in exp_alg(s, *wha[Side(int(v))]).items()
                } for f, s in d.items()
            } for v, d in data.get('promotions', {}).items()
        }
        self.custom_drops = {
            Side(int(v)): {
                load_piece_type(f, c): {
                    p: [
                        (load_piece_type(t, c) if isinstance(t, str) else load_piece(t, self, c)) for t in repack(l)
                    ] for p, l in exp_alg(s, *wha[Side(int(v))]).items()
                } for f, s in d.items()
            } for v, d in data.get('drops', {}).items()
        }
        self.custom_extra_drops = {
            Side(int(v)): [load_piece_type(t, c) for t in l] for v, l in data.get('extra', {}).items()
        }
        if 'captured' in data:
            self.captured_pieces = {
                Side(int(v)): [load_piece_type(t, c) for t in l] for v, l in data.get('captured', {}).items()
            }
            for side in (Side.WHITE, Side.BLACK):
                if side not in self.captured_pieces:
                    self.captured_pieces[side] = []
        else:
            self.reset_captures()

        self.chaos_sets = {}
        self.piece_set_ids |= {Side(int(k)): v for k, v in data.get('set_ids', {}).items()}
        self.piece_sets, self.piece_set_names = self.get_piece_sets()
        saved_piece_sets = {
            Side(int(v)): [load_piece_type(t, c) or NoPiece for t in d] for v, d in data.get('sets', {}).items()
        } or self.piece_sets
        update_sets = False
        for side in self.piece_sets:
            if self.piece_set_ids[side] is None:
                self.piece_sets[side] = saved_piece_sets[side]
                self.piece_set_names[side] = get_set_name(self.piece_sets[side], True)
                continue
            for i, pair in enumerate(zip_longest(saved_piece_sets[side], self.piece_sets[side], fillvalue=NoPiece)):
                if pair[0] != pair[1]:
                    # this can mean a few things, namely the RNG implementation changing or new sets/pieces being added.
                    # either way, we should at least try to load the old pieces defined in the save to recreate the game
                    self.log(
                        "Error: Piece set does not match "
                        f"({side}: {toa(((0 if side == Side.WHITE else 7), i))} "
                        f"was {pair[0].name}, but is {pair[1].name})"
                    )
                    update_sets = True
        if update_sets:
            self.piece_sets = {side: saved_piece_sets[side] for side in self.piece_sets}
            self.piece_set_names = {
                side: get_set_name(self.piece_sets[side], self.piece_set_ids[side] is None) for side in self.piece_sets
            }

        self.custom_layout = {p: load_piece(v, self, c).on(p) for p, v in exp_alg(data.get('layout', {}), *whc).items()}

        ply_count = data.get('ply', self.ply_count)
        if ply_count <= 0:
            self.log(f"Error: Invalid ply count ({ply_count})")
            ply_count = 1
        self.custom_turn_order = [
            (Side(int(side[0])), [{k: v for k, v in {
                'order': d.get('order', 0),
                'state': d.get('state', 0),
                'last': [t for t in repack(d.get('last', []))],
                'piece': [t for t in repack(d.get('piece', []))],
                'type': [t for t in repack(d.get('type', []))],
                'action': [t for t in repack(d.get('action', []))],
                'check': d.get('check', 0),
            }.items() if v} for d in repack(side[1])])
            if isinstance(side, list) and len(side) > 1 else (Side(int(side)), None)
            for side in data.get('order', [])
        ]
        self.reset_turn_order()
        self.custom_end_rules = {
            (Side(int(side)) if side.isdigit() else side): {
                group: value for group, value in rules.items()
            } if isinstance(rules, dict) else rules
            for side, rules in data.get('end', {}).items()
        }
        self.reset_end_rules()
        end_data = data.get('count', {})
        for s in end_data:
            side = Side(int(s))
            if side not in self.end_data:
                continue
            for c in end_data[s]:
                condition = end_types.get(c, c)
                if condition not in self.end_data[side]:
                    continue
                for g in end_data[s][c]:
                    group = g
                    if group not in self.end_data[side][condition]:
                        continue
                    self.end_data[side][condition][group] = end_data[s][c][g]

        self.reset_drops()
        self.reset_promotions()
        self.reset_edit_promotions()
        self.reset_penultima_pieces()

        self.move_history = [load_move(d, self, c) for d in data.get('moves', [])]
        self.future_move_history = [load_move(d, self, c) for d in data.get('future', [])[::-1]]

        rolls = data.get('rolls', {})
        self.roll_history = [
            ({fra(s): v for s, v in rolls[str(n)].items()} if str(n) in rolls else {}) for n in range(ply_count)
        ]
        rph = data.get('roll_piece_history', {})
        self.probabilistic_piece_history = [
            ({(fra(k), load_piece_type(v, c)) for k, v in rph[str(n)].items()} if str(n) in rph else set())
            for n in range(ply_count)
        ]

        self.chain_start = load_move(data.get('chain_start'), self, c)
        if self.move_history and self.move_history[-1] and self.move_history[-1].matches(self.chain_start):
            self.chain_start = self.move_history[-1]
        chained_move = self.chain_start
        poss = []
        while chained_move:
            poss.extend((chained_move.pos_from, chained_move.pos_to))
            chained_move = chained_move.chained_move
        self.chain_moves = {
            self.chain_start.piece.side: {
                (tuple(poss)): [load_move(m, self, c) for m in data.get('chain_moves', [])]
            }, self.chain_start.piece.side.opponent(): {}
        } if self.chain_start else {Side.WHITE: {}, Side.BLACK: {}}

        if 'chaos_state' in data:
            self.chaos_rng = load_rng(data['chaos_state'])
        if 'set_state' in data:
            self.set_rng = load_rng(data['set_state'])
        if 'roll_state' in data:
            self.roll_rng = load_rng(data['roll_state'])

        if self.roll_rng is None:
            self.roll_rng = Random(self.roll_seed)

        pieces = exp_alg(data.get('pieces', {}), *whc) or old_pieces

        for sprite_list in (
            self.piece_sprite_list,
            self.promotion_piece_sprite_list,
            self.promotion_area_sprite_list
        ):
            sprite_list.clear()
            for sprite in sprite_list:
                sprite_list.remove(sprite)

        self.pieces = []

        for row in range(self.board_height):
            self.pieces += [[]]

        for row, col in product(range(self.board_height), range(self.board_width)):
            piece_data = pieces.get((row, col))
            self.pieces[row].append(
                NoPiece(self, pos=(row, col)) if piece_data is None
                else load_piece(piece_data, self, c).on((row, col))
            )
            self.pieces[row][col].scale = self.square_size / self.pieces[row][col].texture.width
            self.piece_sprite_list.append(self.pieces[row][col])

        self.promotion_piece = load_piece(data.get('promotion'), self, c)

        self.load_pieces()
        self.update_pieces()
        self.update_colors()
        for side in self.auto_ranged_pieces:
            if self.auto_ranged_pieces[side]:
                self.load_auto_capture_markers(side)

        starting = 'Starting new' if with_history else 'Resuming saved'
        if self.variant:
            self.log(f"Info: {starting} game (with custom variant)")
        elif self.custom_layout:
            self.log(f"Info: {starting} game (with custom starting layout)")
        elif None in self.piece_set_ids.values():
            self.log(f"Info: {starting} game (with custom piece sets)")
        else:
            some = 'regular' if not self.chaos_mode else 'chaotic'
            same = self.piece_set_ids[Side.WHITE] == self.piece_set_ids[Side.BLACK]
            if self.chaos_mode in {3, 4}:
                some = f"extremely {some}"
            if self.chaos_mode in {2, 4}:
                some = f"asymmetrical {some}"
            if same:
                some = f"a{'' if self.chaos_mode in {0, 1} else 'n'} {some}"
            sets = 'set' if same else 'sets'
            self.log(f"Info: {starting} game (with {some} piece {sets})")
        if with_history:
            self.ply_count = 0
            self.turn_side = Side.NONE
            self.turn_data = [0, Side.NONE, 0]
            self.turn_rules = None
        else:
            turn_data = data.get('turn')
            if turn_data is None:
                turn_data = self.turn_data
            else:
                turn_data[1] = Side(turn_data[1])
            self.ply_count = ply_count
            self.turn_data = turn_data
            self.load_turn_rules()
            if self.turn_side != turn_data[1]:
                self.log(f"Error: Turn side does not match ({ self.turn_side} was {turn_data[1]})")
                self.turn_side = turn_data[1]
        self.log_armies()
        self.log_info()
        if with_history:
            self.shift_ply(+1)
        self.log_special_modes()
        if with_history:
            success = self.reload_history()
            if not success:
                self.log("Error: Failed to reload history!")
        else:
            if self.move_history:
                last_move = self.move_history[-1]
                if last_move and last_move.is_edit != 1 and last_move.movement_type != DropMovement:
                    last_move.piece.movement.reload(last_move, last_move.piece)
            self.reload_en_passant_markers()
            self.log(f"Info: {self.turn_side} to move", False)
        if self.edit_mode:
            self.log("Mode: EDIT", False)
            self.moves = {side: {} for side in self.moves}
            self.chain_moves = {side: {} for side in self.chain_moves}
            self.theoretical_moves = {side: {} for side in self.theoretical_moves}
            self.show_moves()

        if self.promotion_piece:
            piece = self.promotion_piece
            self.end_promotion()
            if self.move_history and self.move_history[-1]:
                if self.move_history[-1].is_edit == 1:
                    self.start_promotion(piece, self.edit_promotions[self.get_promotion_side(piece)])
                elif self.move_history[-1].piece.board_pos == piece.board_pos:
                    if isinstance(piece, NoPiece):
                        self.try_drop(self.move_history[-1])
                    else:
                        self.try_promotion(self.move_history[-1])
        else:
            if not with_history and not self.edit_mode:
                self.unload_end_data()
                self.load_pieces()
                self.load_check()
                self.load_moves()
                self.reload_end_data()
                self.update_status()
            selection = data.get('selection')
            if selection:
                self.select_piece(fra(selection))

        self.load_data = dump
        self.load_dict = data
        self.save_loaded = True

        return success

    def empty_board(self) -> None:
        self.save_interval = 0

        self.deselect_piece()
        self.clear_relay_markers()
        self.clear_en_passant_markers()
        self.clear_auto_capture_markers()
        self.reset_captures()

        self.end_data = {
            side: {
                condition: {
                    group: 0 for group in data
                } for condition, data in rules.items()
            } for side, rules in self.end_data.items()
        }
        self.end_value = 0
        self.end_group = None
        self.end_condition = None
        self.win_side = Side.NONE
        self.game_over = False
        self.chain_start = None
        self.promotion_piece = None
        self.action_count = 0
        self.ply_count = 0
        self.turn_side = Side.NONE
        self.turn_data = [0, Side.NONE, 0]

        for sprite_list in self.piece_sprite_list, self.promotion_piece_sprite_list, self.promotion_area_sprite_list:
            sprite_list.clear()
            for sprite in sprite_list:
                sprite_list.remove(sprite)

        self.log("Info: Board cleared")
        self.shift_ply(+1)
        if not self.edit_mode:
            self.log("Mode: EDIT", False)
        self.edit_mode = True

        self.edit_piece_set_id = self.board_config['edit_id']
        self.roll_history = []
        self.future_move_history = []
        self.probabilistic_piece_history = []
        self.reset_drops()
        self.reset_promotions()
        self.reset_edit_promotions()
        self.reset_penultima_pieces()

        if self.board_config['update_roll_seed']:
            self.roll_seed = self.roll_rng.randint(0, max_seed)
        self.roll_rng = Random(self.roll_seed)

        self.move_history = []

        self.pieces = []

        for row in range(self.board_height):
            self.pieces += [[]]

        for row, col in product(range(self.board_height), range(self.board_width)):
            self.pieces[row].append(NoPiece(self, pos=(row, col)))
            self.pieces[row][col].scale = self.square_size / self.pieces[row][col].texture.width
            self.piece_sprite_list.append(self.pieces[row][col])

        self.unload_end_data()
        self.load_pieces()
        self.load_check()
        self.update_end_data()
        self.load_moves()
        self.reload_end_data()
        self.update_status()

    def reset_custom_data(self, rollback: bool = False) -> None:
        if rollback:
            self.custom_pieces = self.past_custom_pieces
        else:
            self.past_custom_pieces = {**self.past_custom_pieces, **self.custom_pieces}
        self.save_info = [None]
        self.variant = ''
        self.alias_dict = {}
        self.custom_areas = {}
        self.custom_drops = {}
        self.custom_pawns = None
        self.custom_pieces = {}
        self.custom_layout = {}
        self.custom_promotions = {}
        self.custom_extra_drops = {}
        self.custom_turn_order = []
        self.custom_end_rules = {}
        for group, piece_list in self.piece_groups.items():
            for piece_type in piece_list:
                piece_type.group_str = None
        self.piece_groups = {}
        self.piece_limits = {}
        if self.color_index is None:
            self.color_index = 0
        self.color_scheme = colors[self.color_index]
        for side in self.piece_set_ids:
            if self.piece_set_ids[side] is None:
                self.piece_set_ids[side] = 0
        self.reset_areas()
        self.reset_turn_order()
        self.reset_end_rules()

    def reset_captures(self) -> None:
        self.captured_pieces = {Side.WHITE: [], Side.BLACK: []}
        for side in self.captured_pieces:
            if side in self.custom_extra_drops:
                self.captured_pieces[side].extend(self.custom_extra_drops[side])

    def reset_drops(self, piece_sets: dict[Side, list[type[Piece]]] | None = None) -> None:
        if self.custom_drops:
            self.drops = deepcopy(self.custom_drops)
            return
        if piece_sets is None:
            piece_sets = self.piece_sets
        self.drops = {}
        drop_squares = [(i, j) for i in range(self.board_height) for j in range(self.board_width)]
        pawn_drop_squares = [(i, j) for i in range(1, self.board_height - 1) for j in range(self.board_width)]
        custom_pawns = {
            side: self.custom_pawns.get(side)
            if isinstance(self.custom_pawns, dict)
            else self.custom_pawns for side in piece_sets
        }
        for drop_side in piece_sets:
            drops = {}
            pawns = custom_pawns[drop_side]
            for pawn in (pawns if pawns is not None else [Pawn]):
                drops[pawn] = {pos: [pawn] for pos in pawn_drop_squares}
            for side in (drop_side, drop_side.opponent()):
                if not piece_sets[side]:
                    continue
                trimmed_set = piece_sets[side].copy()
                while issubclass(trimmed_set[0], NoPiece):
                    trimmed_set.pop(0)
                    if not trimmed_set:
                        break
                if not trimmed_set:
                    continue
                while issubclass(trimmed_set[-1], NoPiece):
                    trimmed_set.pop()
                    if not trimmed_set:
                        break
                if not trimmed_set:
                    continue
                for i, piece_type in enumerate(trimmed_set):
                    if piece_type not in drops and not issubclass(piece_type, NoPiece):
                        is_royal = self.is_royal(piece_type, drop_side)
                        if is_royal and is_royal not in {'+', '-'}:
                            continue
                        has_moved = i in {0, len(trimmed_set) - 1}
                        if has_moved:
                            piece = piece_type(self)
                            piece.movement.set_moves(1)
                            drops[piece_type] = {pos: [piece] for pos in drop_squares}
                        else:
                            drops[piece_type] = {pos: [piece_type] for pos in drop_squares}
            self.drops[drop_side] = drops

    def reset_promotions(self, piece_sets: dict[Side, list[type[Piece]]] | None = None) -> None:
        if self.custom_promotions:
            self.promotions = deepcopy(self.custom_promotions)
            return
        if piece_sets is None:
            piece_sets = self.piece_sets
        self.promotions = {}
        promotion_squares = {
            Side.WHITE: [(self.board_height - 1, i) for i in range(self.board_width)],
            Side.BLACK: [(0, i) for i in range(self.board_width)],
        }
        split = {side: len(piece_sets[side]) // 2 for side in self.piece_sets}
        custom_pawns = {
            side: self.custom_pawns.get(side)
            if isinstance(self.custom_pawns, dict)
            else self.custom_pawns for side in piece_sets
        }
        for side in promotion_squares:
            promotions = []
            used_piece_set = set()
            for pieces in (
                piece_sets[side][split[side] - 1::-1], piece_sets[side.opponent()][split[side.opponent()] - 1::-1],
                piece_sets[side][split[side] + 1:], piece_sets[side.opponent()][split[side.opponent()] + 1:],
                [
                    *piece_sets[side.opponent()][split[side.opponent()]:split[side.opponent()] + 1],
                    *piece_sets[side][split[side]:split[side] + 1],
                ],
            ):
                promotion_types = []
                for piece_type in pieces:
                    if piece_type not in used_piece_set and not issubclass(piece_type, NoPiece):
                        is_royal = self.is_royal(piece_type, side)
                        if is_royal and is_royal not in {'+', '-'}:
                            continue
                        used_piece_set.add(piece_type)
                        promotion_types.append(piece_type)
                promotions.extend(promotion_types[::-1])
            self.promotions[side] = {}
            pawns = custom_pawns[side]
            for pawn in (pawns if pawns is not None else [Pawn]):
                self.promotions[side][pawn] = {pos: promotions.copy() for pos in promotion_squares[side]}

    def reset_edit_promotions(self, piece_sets: dict[Side, list[type[Piece]]] | None = None) -> None:
        if is_prefix_of('custom', self.edit_piece_set_id):
            self.edit_promotions = {
                side: [piece_type for _, piece_type in self.custom_pieces.items()]
                + [piece_type for k, piece_type in self.past_custom_pieces.items() if k not in self.custom_pieces]
                for side in self.edit_promotions
            }
            return
        if is_prefix_of('wall', self.edit_piece_set_id):
            blanks = [None] * (
                max(0, self.board_height // 2 - 3 if (self.board_height // 3 or self.board_height < 9) else 0)
            )
            self.edit_promotions = {side: list(chain.from_iterable(
                [piece(board=self, side=Side.WHITE), piece(board=self, side=Side.BLACK), piece(board=self)] + blanks
                for piece in (Void, Shield))) + [Block, Wall, Border] + blanks
            for side in self.edit_promotions}
            return
        if piece_sets is None:
            if self.edit_piece_set_id is None:
                piece_sets = self.piece_sets
            else:
                piece_sets = self.get_piece_sets(self.edit_piece_set_id)[0]
        self.edit_promotions = {side: [] for side in self.piece_sets}
        split = {side: len(piece_sets[side]) // 2 for side in self.piece_sets}
        for side in self.edit_promotions:
            used_piece_set = set()
            side_pawns = (
                self.custom_pawns.get(side)
                if isinstance(self.custom_pawns, dict)
                else self.custom_pawns
            )
            opponent_pawns = (
                self.custom_pawns.get(side.opponent())
                if isinstance(self.custom_pawns, dict)
                else self.custom_pawns
            )
            for pieces in (
                piece_sets[side][split[side] - 1::-1], piece_sets[side.opponent()][split[side.opponent()] - 1::-1],
                piece_sets[side][split[side] + 1:], piece_sets[side.opponent()][split[side.opponent()] + 1:],
                [
                    *piece_sets[side.opponent()][split[side.opponent()]:split[side.opponent()] + 1],
                    *(opponent_pawns if opponent_pawns is not None else [Pawn]),
                    *(side_pawns if side_pawns is not None else [Pawn]),
                    *piece_sets[side][split[side]:split[side] + 1],
                ],
            ):
                promotion_types = []
                for piece in pieces:
                    if piece not in used_piece_set and not issubclass(piece, NoPiece):
                        used_piece_set.add(piece)
                        promotion_types.append(piece)
                self.edit_promotions[side].extend(promotion_types[::-1])

    def reset_penultima_pieces(self, piece_sets: dict[Side, list[type[Piece]]] | None = None) -> None:
        if piece_sets is None:
            piece_sets = self.piece_sets
        self.penultima_pieces = {side: {} for side in self.penultima_pieces}
        for player_side in self.penultima_pieces:
            for piece_side in (player_side, player_side.opponent()):
                if not piece_sets[piece_side]:
                    continue
                trimmed_set = piece_sets[piece_side].copy()
                while issubclass(trimmed_set[0], NoPiece):
                    trimmed_set.pop(0)
                    if not trimmed_set:
                        break
                if not trimmed_set:
                    continue
                while issubclass(trimmed_set[-1], NoPiece):
                    trimmed_set.pop()
                    if not trimmed_set:
                        break
                if not trimmed_set:
                    continue
                textures = copy(penultima_textures)
                if len(trimmed_set) > len(textures):
                    continue
                if len(trimmed_set) < len(textures):
                    offset = (len(trimmed_set) - len(textures)) / 2
                    textures = textures[-floor(offset):ceil(offset)]
                for i, piece in enumerate(trimmed_set):
                    if textures[i]:
                        texture = textures[i]
                        if piece_side == player_side.opponent():
                            texture += 'O'
                        if i > 4 and piece != piece_sets[player_side][7 - i]:
                            texture += '|'
                        if piece not in self.penultima_pieces[player_side]:
                            self.penultima_pieces[player_side][piece] = texture

    def reset_areas(self) -> None:
        self.areas = {Side.WHITE: {}, Side.BLACK: {}}
        for side in self.areas:
            for name, area in self.custom_areas.items():
                if isinstance(area, dict):
                    if side not in area:
                        continue
                    area = area[side]
                if not area:
                    continue
                self.areas[side][name] = area
            if Pawn.name not in self.areas[side]:
                rows = range(2) if side == Side.WHITE else range(self.board_height - 2, self.board_height)
                self.areas[side][Pawn.name] = {(row, col) for row in rows for col in range(self.board_width)}

    def reset_turn_order(self) -> None:
        start_turns, loop_turns = [], []
        start_ended = False
        for i, turn in enumerate(self.custom_turn_order or [(Side.WHITE, None), (Side.BLACK, None)]):
            side, rules = turn[0], turn[1]
            if side == Side.NONE:
                start_ended = True
                continue
            (loop_turns if start_ended else start_turns).append((side, rules))
        if start_turns and not loop_turns and not start_ended:
            start_turns, loop_turns = loop_turns, start_turns
        self.initial_turns = len(start_turns)
        self.turn_order = start_turns + loop_turns

    def load_turn_rules(self, offset: int = 0, origin: int | None = None) -> None:
        turn = self.get_turn(offset, origin)
        side, rules = self.turn_order[turn]
        if rules is None:
            rules = []
        if isinstance(rules, list):
            to_act = lambda s: repack(action_types.get(s, list(s)))
            to_type = lambda s: t.__name__ if isinstance((t := load_movement_type(s) or s), type) else t
            from_iter = chain.from_iterable
            data = {}
            override_default = False
            for rule in ['default'] + (rules or []):
                order = 0
                if rule == 'default':
                    rule = {}
                elif isinstance(rule, dict):
                    order = int(rule.get('order', 0))
                    if order == 0 and not override_default:
                        override_default = True
                        del data[order]
                state = int(rule.get('state', 0))
                lasts = rule.get('last', '')
                allow_lasts = [to_type(s) for s in lasts if not s or s[0] != '!'] or ['*']
                block_lasts = [to_type(s[1:]) for s in lasts if s and s[0] == '!'] or [None]
                pieces = rule.get('piece', '')
                allow_pieces = [s for s in pieces if not s or s[0] != '!'] or ['*']
                block_pieces = [s[1:] for s in pieces if s and s[0] == '!'] or [None]
                move_types = rule.get('type', '')
                allow_types = [to_type(s) for s in move_types if not s or s[0] != '!'] or ['*']
                block_types = [to_type(s[1:]) for s in move_types if s and s[0] == '!'] or [None]
                actions = rule.get('action', ['!pass'])
                allow_actions = list(from_iter(to_act(s) for s in actions if not s or s[0] != '!')) or ['*']
                block_actions = list(from_iter(to_act(s[1:]) for s in actions if s and s[0] == '!')) or [None]
                check = int(rule.get('check', 0))
                data_order = data.setdefault(order, {})
                data_state = data_order.setdefault(state, {})
                for allow_last in allow_lasts:
                    data_allow_last = data_state.setdefault(allow_last, {})
                    for block_last in block_lasts:
                        data_block_last = data_allow_last.setdefault(block_last, {})
                        for allow_piece in allow_pieces:
                            data_allow_piece = data_block_last.setdefault(allow_piece, {})
                            for block_piece in block_pieces:
                                data_block_piece = data_allow_piece.setdefault(block_piece, {})
                                for allow_type in allow_types:
                                    data_allow_type = data_block_piece.setdefault(allow_type, {})
                                    for block_type in block_types:
                                        data_block_type = data_allow_type.setdefault(block_type, {})
                                        for allow_action in allow_actions:
                                            data_allow_action = data_block_type.setdefault(allow_action, {})
                                            for block_action in block_actions:
                                                data_allow_action.setdefault(block_action, check)
                                                # oh my god what have i done IT'S TIME FOR TESTING *~MAKING SCIENCE~*
            rules = data
            self.turn_order[turn] = side, rules
        self.turn_side, self.turn_rules = side, rules

    def reset_end_rules(self) -> None:
        self.end_rules = {}
        self.end_data = {}
        for side in [Side.WHITE, Side.BLACK] + ([Side.NONE] if Side.NONE in self.custom_end_rules else []):
            self.end_rules[side] = {}
            self.end_data[side] = {}
            side_rules = self.custom_end_rules.get(side, self.custom_end_rules) if self.custom_end_rules else {}
            for condition, rules in side_rules.items():
                if isinstance(condition, Side):
                    continue
                is_area = True
                if condition in end_types:
                    condition = end_types[condition]
                    is_area = False
                elif condition not in self.areas and not isa(condition):
                    continue
                if isinstance(rules, dict):
                    if condition == 'checkmate':
                        self.end_rules[side].setdefault(condition, {}).setdefault('', 1)
                        self.end_data[side].setdefault(condition, {}).setdefault('', 0)
                    for group, value in rules.items():
                        self.end_rules[side].setdefault(condition, {}).setdefault(group, value)
                        if not is_area:
                            self.end_data[side].setdefault(condition, {}).setdefault(group, 0)
                elif is_area:
                    self.end_rules.setdefault(side, {}).setdefault(condition, {}).setdefault('', rules)
                else:
                    self.end_rules.setdefault(side, {}).setdefault(condition, {}).setdefault('', rules)
                    self.end_data.setdefault(side, {}).setdefault(condition, {}).setdefault('', 0)
            if side is Side.NONE:
                continue
            if 'checkmate' not in self.end_rules[side] and 'capture' not in self.end_rules[side]:
                self.end_rules[side]['checkmate'] = {'': 1, "King": 1}
                self.end_data[side]['checkmate'] = {'': 0, "King": 0}
                if "Royal" in self.piece_groups:
                    self.end_rules[side]['checkmate']["Royal"] = 1
                    self.end_data[side]['checkmate']["Royal"] = 0
            if 'stalemate' not in self.end_rules[side]:
                self.end_rules[side]['stalemate'] = {'': 0}
                self.end_data[side]['stalemate'] = {'': 0}


    def get_piece_sets(
        self,
        piece_set_ids: dict[Side, int] | int | None = None
    ) -> tuple[dict[Side, list[type[Piece]]], dict[Side, str]]:
        if piece_set_ids is None:
            piece_set_ids = self.piece_set_ids
        elif isinstance(piece_set_ids, int):
            piece_set_ids = {side: piece_set_ids for side in self.piece_set_ids}  # type: ignore
        piece_sets = {Side.WHITE: [], Side.BLACK: []}
        piece_names = {Side.WHITE: '-', Side.BLACK: '-'}
        for side in piece_set_ids:
            if piece_set_ids[side] is None:
                piece_sets[side] = self.piece_sets[side].copy()
                piece_names[side] = self.piece_set_names[side]
            else:
                if piece_set_ids[side] < 0:
                    for i in range(-piece_set_ids[side]):
                        if i + 1 not in self.chaos_sets:
                            self.chaos_sets[i + 1] = self.get_chaos_set(side)
                    chaos_set = self.chaos_sets.get(-piece_set_ids[side], [[NoPiece] * self.board_width, '-'])
                    piece_sets[side] = chaos_set[0].copy()
                    piece_names[side] = chaos_set[1]
                else:
                    piece_group = piece_groups[piece_set_ids[side]]
                    piece_sets[side] = get_set_data(side, piece_set_ids[side]).copy()
                    piece_names[side] = piece_group.get('name', '-')
                if self.board_width != len(piece_sets[side]):
                    offset = (self.board_width - len(piece_sets[side])) / 2
                    if offset > 0:
                        piece_sets[side] = [NoPiece] * floor(offset) + piece_sets[side] + [NoPiece] * ceil(offset)
                    else:
                        piece_sets[side] = piece_sets[side][-floor(offset):ceil(offset)]
            if not piece_sets[side]:
                piece_sets[side] = [NoPiece] * self.board_width
                piece_names[side] = '-'
        return piece_sets, piece_names

    def get_random_set(self, side: Side, asymmetrical: bool = False) -> tuple[list[type[Piece]], str]:
        # random_set_poss: independent random choices
        # random_set_poss[]: unique randomly sampled armies
        # random_set_poss[][]: positions taken by the random army
        # this is important because in mode 2 same-type pieces have to be distinct to ensure there are no piece repeats!
        # also, the king type is determined by the queenside rook type because of colorbound castling. see colorbound.py
        if asymmetrical:
            random_set_poss = [[[0, 4], [7]], [[1], [6]], [[2], [5]], [[3]]]
        else:
            random_set_poss = [[[0, 4, 7]], [[1, 6]], [[2, 5]], [[3]]]
        blocked_ids = set(self.board_config['block_ids_chaos'])
        piece_set_ids = list(i for i in range(len(piece_groups)) if i not in blocked_ids)
        piece_set: list[type[Piece]] = [NoPiece] * default_board_width
        for i, group in enumerate(random_set_poss):
            random_set_ids = self.chaos_rng.sample(piece_set_ids, k=len(group))
            for j, poss in enumerate(group):
                for pos in poss:
                    piece_set[pos] = get_set_data(side, random_set_ids[j])[pos]
        return piece_set, get_set_name(piece_set)

    def get_extremely_random_set(self, side: Side, asymmetrical: bool = False) -> tuple[list[type[Piece]], str]:
        blocked_ids = set(self.board_config['block_ids_chaos'])
        piece_set_ids = list(i for i in range(len(piece_groups)) if i not in blocked_ids)
        piece_pos_ids = [i for i in range(4)] + [7]
        piece_poss = [
            (i, j) for i in piece_set_ids for j in piece_pos_ids
            if j < 4 or (set_data := get_set_data(side, i))[j] != set_data[7 - j]
        ]
        random_set_ids = self.chaos_rng.sample(piece_poss, k=7 if asymmetrical else 4)
        if asymmetrical:
            random_set_poss = [[i] for i in range(8) if i != 4]
        else:
            random_set_poss = [[0, 7], [1, 6], [2, 5], [3]]
        piece_set: list[type[Piece]] = [NoPiece] * default_board_width
        for i, group in enumerate(random_set_poss):
            set_id, set_pos = random_set_ids[i]
            for j, pos in enumerate(group):
                random_set = get_set_data(side, set_id)
                piece_set[pos] = random_set[set_pos]
                if self.chaos_mode == 3 and set_pos != 3 and j > 0:
                    if random_set[set_pos] != random_set[7 - set_pos]:
                        piece_set[pos] = random_set[7 - set_pos]
        piece_set[4] = CBKing if piece_set[0].is_colorbound() else King
        return piece_set, get_set_name(piece_set)

    def get_chaos_set(self, side: Side) -> tuple[list[type[Piece]], str]:
        asymmetrical = self.chaos_mode in {2, 4}
        if self.chaos_mode in {1, 2}:
            return self.get_random_set(side, asymmetrical)
        if self.chaos_mode in {3, 4}:
            return self.get_extremely_random_set(side, asymmetrical)

    def load_chaos_sets(self, mode: int, same: bool) -> None:
        chaotic = 'chaotic'
        if mode in {3, 4}:
            chaotic = f"extremely {chaotic}"
        if mode in {2, 4}:
            chaotic = f"asymmetrical {chaotic}"
        if same:
            chaotic = f"a{'' if mode == 1 else 'n'} {chaotic}"
        sets = 'set' if same else 'sets'
        self.log(f"Info: Starting new game (with {chaotic} piece {sets})")
        self.chaos_mode = mode
        self.chaos_sets = {}
        self.chaos_seed = self.chaos_rng.randint(0, max_seed)
        self.chaos_rng = Random(self.chaos_seed)
        self.piece_set_ids = {Side.WHITE: -1, Side.BLACK: -1 if same else -2}
        self.reset_custom_data()
        self.reset_board()

    def is_royal(self, piece: Piece | type[Piece], side: Side, conditions: set | None = None) -> int:
        return self.get_royal_state(piece, side, conditions)[0]

    def get_royal_group(self, piece: Piece | type[Piece], side: Side, conditions: set | None = None) -> str:
        return self.get_royal_state(piece, side, conditions)[1]

    def get_royal_state(self, piece: Piece | type[Piece], side: Side, conditions: set | None = None) -> tuple[int, str]:
        if conditions is not None and not conditions:
            return 0, ''
        if conditions is None:
            conditions = {'check', 'checkmate', 'capture'}
        opponent = side.opponent()
        end_rules = self.end_rules[opponent]
        if not end_rules:
            return 0, ''
        for condition in end_rules:
            if condition not in conditions:
                continue
            if condition == 'check':
                for group, value in end_rules.get(condition, {}).items():
                    if self.fits(group, piece):
                        return sign(value), group
            elif condition in {'checkmate', 'capture'}:
                for group, value in end_rules.get(condition, {}).items():
                    if self.fits(group, piece):
                        return value, group
        return 0, ''

    def in_area(self, area: str, pos: Position, side: Side) -> bool:
        if area == '*':  # all squares on the board, guaranteed to be True
            return True
        if side in self.areas:
            if area == '':  # any defined area on the board
                return any(pos in self.areas[side][a] for a in self.areas[side])
            if area in self.areas[side]:  # a specific area on the board
                return pos in self.areas[side][area]
        try:  # treating as notation (possibly generic)
            return all(i in {-1, j} for i, j in zip(fra(area), pos))
        except ValueError:  # if all else fails...
            return False

    def get_area_groups(self, piece: Piece, side: Side) -> list[tuple[str, str]]:
        end_rules = self.end_rules[side]
        groups = []
        for condition in end_rules:
            if condition in {'check', 'checkmate', 'capture', 'stalemate'}:
                continue
            if not self.in_area(condition, piece.board_pos, side):
                continue
            for group, value in end_rules.get(condition, {}).items():
                if group == '' or self.fits(group, piece):
                    groups.append((condition, group))
        return groups

    def get_new_area_count(self, area: str, group: str, side: Side, max_count: int = 0) -> int:
        if not self.move_history:
            return 0
        index = 1
        last_moves = []
        for move in self.move_history[::-1]:
            if self.get_turn_side(-index) != side:
                break
            if not move:
                last_moves.append(move)
                continue
            if move.is_edit:
                last_moves.append(move)
                continue
            move_chain = [move]
            while move_chain[-1].chained_move:
                move_chain.append(move_chain[-1].chained_move)
            last_moves.extend(move_chain[::-1])
            index += 1
        count = 0
        for move in last_moves[::-1]:
            piece = move.promotion or move.piece
            moved = move.promotion or move.pos_to != move.pos_from
            if not moved or not piece or piece.side != side:
                continue
            if self.in_area(area, move.pos_to, side):
                if self.fits(group, piece):
                    count += 1
                    if max_count and count >= max_count:
                        break
        return count

    def load_pieces(self):
        self.movable_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.piece_counts = {Side.WHITE: {}, Side.BLACK: {}}
        self.area_groups = {Side.WHITE: {}, Side.BLACK: {}}
        self.royal_groups = {Side.WHITE: {}, Side.BLACK: {}}
        self.royal_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.royal_markers = {Side.WHITE: set(), Side.BLACK: set()}
        self.anti_royal_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.anti_royal_markers = {Side.WHITE: set(), Side.BLACK: set()}
        self.probabilistic_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.auto_ranged_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.obstacles = []
        royal_group_values = {Side.WHITE: {}, Side.BLACK: {}}
        for row, col in product(range(self.board_height), range(self.board_width)):
            piece = self.get_piece((row, col))
            side = piece.side
            if side in self.movable_pieces and not isinstance(piece, NoPiece):
                self.movable_pieces[side].append(piece)
                for group in self.piece_limits.get(side, self.piece_limits):
                    if self.fits(group, piece):
                        self.piece_counts[side][group] = self.piece_counts[side].get(group, 0) + 1
                for area, group in self.get_area_groups(piece, side):
                    self.area_groups[side].setdefault(area, {}).setdefault(group, []).append(piece)
                is_royal, royal_group = self.get_royal_state(piece, side)
                if is_royal:
                    self.royal_groups[side].setdefault(royal_group, []).append(piece)
                    royal_group_values[side][royal_group] = is_royal
                if isinstance(piece.movement, ProbabilisticMovement):
                    self.probabilistic_pieces[side].append(piece)
                if isinstance(piece.movement, AutoRangedAutoCaptureRiderMovement):
                    self.auto_ranged_pieces[side].append(piece)
            elif isinstance(piece, Obstacle):
                self.obstacles.append(piece)
        for side, data in self.royal_groups.items():
            for group, pieces in data.items():
                value = royal_group_values[side][group]
                if len(pieces) == 1:
                    if value == '+':
                        self.royal_pieces[side].extend(pieces)
                    elif value == '-':
                        self.anti_royal_pieces[side].extend(pieces)
                if isinstance(value, int):
                    if value > 0:
                        self.royal_pieces[side].extend(pieces)
                    elif value < 0:
                        self.anti_royal_pieces[side].extend(pieces)
        for side in (Side.WHITE, Side.BLACK):
            self.royal_markers[side] = {piece.board_pos for piece in self.royal_pieces[side]}
            self.anti_royal_markers[side] = {piece.board_pos for piece in self.anti_royal_pieces[side]}
        if self.ply_count == 1:
            for side in self.auto_ranged_pieces:
                if self.auto_ranged_pieces[side] and not self.auto_capture_markers[side]:
                    self.load_auto_capture_markers(side)

    def get_royal_loss(self, side: Side, move: Move, conditions: set) -> set:
        if not move or move.is_edit or not conditions:
            return set()
        piece_loss = set()
        piece_gain = set()
        royal_groups = self.royal_groups.get(side, {})
        while move:
            if move.captured_piece and move.captured_piece.side == side:
                is_royal, royal_group = self.get_royal_state(move.captured_piece, side, conditions)
                if royal_group and (isinstance(is_royal, int) or not royal_groups.get(royal_group)):
                    piece_loss.add(royal_group)
            if move.promotion:
                if move.piece and move.piece.side == side:
                    is_royal, royal_group = self.get_royal_state(move.piece, side, conditions)
                    if royal_group and (isinstance(is_royal, int) or not royal_groups.get(royal_group)):
                        piece_loss.add(royal_group)
                if move.promotion and move.promotion.side == side:
                    is_royal, royal_group = self.get_royal_state(move.promotion, side, conditions)
                    if royal_group and (isinstance(is_royal, int) or not royal_groups.get(royal_group)):
                        piece_gain.add(royal_group)
                if move.promotion and move.placed_piece:
                    is_royal, royal_group = self.get_royal_state(move.placed_piece, side, conditions)
                    if royal_group and (isinstance(is_royal, int) or not royal_groups.get(royal_group)):
                        piece_loss.add(royal_group)
            move = move.chained_move
        if move is Unset:
            return set()  # the chain has not finished yet. who knows, maybe we will gain a new royal piece later on
        piece_loss.difference_update(piece_gain)
        return piece_loss

    def load_check(self, side: Side | None = None):
        # Can any of the side's royal pieces be captured by the opponent?
        # When side is not specified, checks for the side that moves now.
        if side is None:
            side = self.turn_side
        self.check_side = Side.NONE
        self.check_groups = set()
        if self.edit_mode:
            return
        if not {'check', 'checkmate'}.intersection(self.end_rules[side.opponent()]):
            return
        if (
            'check' not in self.end_rules[side.opponent()]
            and not (self.royal_pieces[side] or self.anti_royal_pieces[side])
        ):
            return
        end_rules = self.end_rules[side.opponent()]
        end_data = self.end_data.get(side.opponent())
        royal_groups = [
            group for group in self.royal_groups[side]
            if end_rules.get('check', {}).get(group, 0)
            or (
                (need := end_rules.get('checkmate', {}).get(group, 0)) in {'+', '-'}
                or isinstance(need, int) and need * sign(need) - end_data.get('checkmate', {}).get(group, 0) <= 1
            )
        ]
        if not royal_groups:
            return
        royal_groups = deduplicate(royal_groups)
        safe_royal_groups = {
            group for group in royal_groups
            if ((check := end_rules.get('check', {}).get(group, 0)) == '+' or isinstance(check, int) and check > 0)
            or ((mate := end_rules.get('checkmate', {}).get(group, 0)) == '+' or isinstance(mate, int) and mate > 0)
        }
        safe_anti_royal_groups = {
            group for group in royal_groups
            if ((check := end_rules.get('check', {}).get(group, 0)) == '-' or isinstance(check, int) and check < 0)
            or ((mate := end_rules.get('checkmate', {}).get(group, 0)) == '-' or isinstance(mate, int) and mate < 0)
        }
        all_royal_groups = safe_royal_groups.copy()
        anti_royal_checks = {}
        royal_group = lambda x: self.get_royal_group(x, side, {'check', 'checkmate'})
        insert = lambda x, p: anti_royal_checks.setdefault(x, set()).add(p)
        self.ply_simulation += 1
        for piece in self.movable_pieces[side.opponent()]:
            if isinstance(piece.movement, ProbabilisticMovement):
                continue
            for move in piece.moves():
                chained_move = move
                while chained_move:
                    chained_move = copy(chained_move)
                    if chained_move.promotion and not chained_move.is_edit:
                        piece = chained_move.promotion
                        if isinstance(piece.movement, AutoCaptureMovement):
                            piece.movement.generate_captures(chained_move, piece)
                    if not chained_move.swapped_piece:
                        if chained_move.pos_to in self.royal_markers[side]:
                            group = royal_group(self.get_piece(chained_move.pos_to))
                            if group in safe_royal_groups:
                                self.check_side = side
                                safe_royal_groups.discard(group)
                        elif chained_move.pos_to in self.anti_royal_markers[side]:
                            group = royal_group(self.get_piece(chained_move.pos_to))
                            if group in safe_anti_royal_groups:
                                insert(group, chained_move.pos_to)
                                if len(anti_royal_checks[group]) == len(self.royal_groups[side].get(group, ())):
                                    safe_anti_royal_groups.discard(group)
                        if not safe_royal_groups and not safe_anti_royal_groups:
                            break
                    if chained_move.captured_piece and chained_move.captured_piece.side == side:
                        if chained_move.captured_piece.board_pos in self.royal_markers[side]:
                            group = royal_group(chained_move.captured_piece)
                            if group in safe_royal_groups:
                                self.check_side = side
                                safe_royal_groups.discard(group)
                        elif chained_move.captured_piece.board_pos in self.anti_royal_markers[side]:
                            group = royal_group(chained_move.captured_piece)
                            if group in safe_anti_royal_groups:
                                insert(group, chained_move.captured_piece.board_pos)
                                if len(anti_royal_checks[group]) == len(self.royal_groups[side].get(group, ())):
                                    safe_anti_royal_groups.discard(group)
                        if not safe_royal_groups and not safe_anti_royal_groups:
                            break
                    chained_move = chained_move.chained_move
                if self.check_side:
                    break
            if self.check_side:
                break
        self.ply_simulation -= 1
        self.check_groups = [
            group for group in royal_groups
            if group in all_royal_groups.difference(safe_royal_groups)
            or group in safe_anti_royal_groups
        ]
        if self.check_groups:
            self.check_side = side

    def load_end_conditions(self, side: Side | None = None):
        # Did the side meet any of its win conditions?
        # By default, checks the last side that moved.
        if side is None:
            side = self.get_turn_side(-1) or self.turn_side.opponent()
        opponent = side.opponent()
        self.game_over = False
        self.end_value = 0
        self.end_group = None
        self.end_condition = None
        self.win_side = Side.NONE
        if self.edit_mode:
            return
        for condition in self.end_rules[side]:
            win_side, win_group, win_value = None, None, 0
            loss_side, loss_group, loss_value = None, None, 0
            draw = False
            for group in self.end_rules[side][condition]:
                side_needs = self.end_rules[side][condition][group]
                if condition in self.end_data[side]:
                    side_count = self.end_data[side][condition].get(group) or 0
                else:
                    side_count = len(self.area_groups[side].get(condition, {}).get(group) or ())
                    if isinstance(side_needs, str) and side_needs[-1:] == '!':
                        side_needs = side_needs[:-1] or '1'
                if side_needs in {'+', '-'}:
                    side_needs = int(side_needs + '1')
                if 0 < side_needs <= side_count:
                    win_side, win_value, win_group = side, side_needs, group
                if 0 > side_needs >= -side_count:
                    win_side, win_value, win_group = opponent, -side_needs, group
                if 0 == side_needs and side_count:
                    draw = True
                other_needs = self.end_rules[opponent].get(condition, {}).get(group, None)
                if other_needs is not None:
                    if condition in self.end_data[opponent]:
                        other_count = self.end_data[opponent][condition].get(group) or 0
                    else:
                        other_count = len(self.area_groups[opponent].get(condition, {}).get(group) or ())
                        if isinstance(other_needs, str) and other_needs[-1:] == '!':
                            other_needs = other_needs[:-1] or '1'
                    if other_needs in {'+', '-'}:
                        other_needs = int(other_needs + '1')
                    if 0 < other_needs <= other_count:
                        loss_side, loss_value, loss_group = side, other_needs, group
                    if 0 > other_needs >= -other_count:
                        loss_side, loss_value, loss_group = opponent, -other_needs, group
                    if 0 == other_needs and other_count:
                        draw = True
                if win_side and not loss_side and not draw:
                    if condition not in self.end_data[side]:
                        side_needs = self.end_rules[side][condition][group]
                        if isinstance(side_needs, str) and side_needs[-1:] == '!':
                            side_needs = side_needs[:-1] or '1'
                            if side_needs in {'+', '-'}:
                                side_needs = int(side_needs + '1')
                            if side_count >= side_needs:
                                win_side, win_group, win_value = None, None, 0
                                side_count -= self.get_new_area_count(
                                    condition, group, side, side_needs - side_count + 1
                                )
                                if 0 < side_needs <= side_count:
                                    win_side, win_value, win_group = side, side_needs, group
                                if 0 > side_needs >= -side_count:
                                    win_side, win_value, win_group = opponent, -side_needs, group
                                if 0 == side_needs and side_count:
                                    draw = True
            resolution_rules = self.end_rules.get(side, {}).get(condition, {})
            if win_side and loss_side and win_side != loss_side.opponent():
                if win_value > loss_value:
                    loss_side = None
                if loss_value > win_value:
                    win_side = None
                if win_value == loss_value:
                    resolution = 0
                    if win_group == loss_group:
                        resolution = resolution_rules.get(win_group)
                    resolution = resolution or resolution_rules.get('') or 0
                    if resolution >= 0:
                        loss_side = None
                    if resolution <= 0:
                        win_side = None
                    if resolution == 0:
                        draw = True
            if win_side and draw or loss_side and draw:
                resolution = 0
                if win_group == loss_group:
                    resolution = resolution_rules.get(win_group)
                resolution = resolution or resolution_rules.get('') or 0
                if resolution >= 0:
                    loss_side = None
                    draw = False
                if resolution <= 0:
                    win_side = None
                    draw = False
            if win_side or loss_side or draw:
                self.game_over, self.end_condition = True, condition
                if win_side:
                    self.win_side, self.end_group, self.end_value = win_side, win_group, win_value
                elif loss_side:
                    self.win_side, self.end_group, self.end_value = loss_side.opponent(), loss_group, loss_value
                return

    def load_moves(
        self,
        force_reload: bool = True,
        moves_for: Side | None = None,
        theoretical_moves_for:  Side | None = None
    ) -> None:
        if self.edit_mode:
            self.game_over = False
            self.end_value = 0
            self.end_group = None
            self.end_condition = None
            self.win_side = Side.NONE
            self.moves = {side: {} for side in self.moves}
            self.chain_moves = {side: {} for side in self.chain_moves}
            self.theoretical_moves = {side: {} for side in self.theoretical_moves}
            return
        if force_reload:
            self.game_over = False
            self.end_value = 0
            self.end_group = None
            self.end_condition = None
            self.win_side = Side.NONE
            self.moves_queried = {side: False for side in self.moves_queried}
            self.theoretical_moves_queried = {side: False for side in self.theoretical_moves_queried}
            self.load_end_conditions()
            if self.game_over and self.win_side is not Side.NONE:
                losing_side = self.win_side.opponent()
                self.moves[losing_side] = {}
                self.moves_queried[losing_side] = True
        movable_pieces = {side: self.movable_pieces[side].copy() for side in self.movable_pieces}
        piece_counts = {side: self.piece_counts[side].copy() for side in self.piece_counts}
        area_groups = {side: self.area_groups[side].copy() for side in self.area_groups}
        royal_groups = {side: self.royal_groups[side].copy() for side in self.royal_groups}
        royal_pieces = {side: self.royal_pieces[side].copy() for side in self.royal_pieces}
        royal_markers = {side: self.royal_markers[side].copy() for side in self.royal_markers}
        anti_royal_pieces = {side: self.anti_royal_pieces[side].copy() for side in self.anti_royal_pieces}
        anti_royal_markers = {side: self.anti_royal_markers[side].copy() for side in self.anti_royal_markers}
        probabilistic_pieces = {side: self.probabilistic_pieces[side].copy() for side in self.probabilistic_pieces}
        auto_ranged_pieces = {side: self.auto_ranged_pieces[side].copy() for side in self.auto_ranged_pieces}
        auto_capture_markers = deepcopy(self.auto_capture_markers)
        en_passant_targets = deepcopy(self.en_passant_targets)
        en_passant_markers = deepcopy(self.en_passant_markers)
        royal_ep_targets = deepcopy(self.royal_ep_targets)
        royal_ep_markers = deepcopy(self.royal_ep_markers)
        end_data = deepcopy(self.end_data)
        opponent = self.turn_side.opponent()
        check_side = self.check_side
        check_sides = {check_side: True if check_side and check_side is not Side.NONE else False}
        last_chain_move = self.chain_start
        if last_chain_move:
            chained_move = last_chain_move
            while chained_move.chained_move:
                if not (
                    issubclass(chained_move.movement_type, (CastlingPartnerMovement, CloneMovement)) or
                    chained_move.piece and isinstance(chained_move.piece.movement, AutoCaptureMovement)
                ):
                    last_chain_move = chained_move
                chained_move = chained_move.chained_move
        if moves_for is None:
            moves_for = self.turn_side
        if moves_for == Side.ANY:
            turn_sides = [self.turn_side, opponent]
        elif moves_for == Side.NONE:
            turn_sides = []
        else:
            turn_sides = [moves_for]
        self.display_moves = {side: False for side in self.display_moves}
        for turn_side in turn_sides:
            self.display_moves[turn_side] = True
            if self.moves_queried.get(turn_side, False):
                continue
            if last_chain_move:
                chained_move = self.chain_start
                poss = []
                while chained_move:
                    poss.extend((chained_move.pos_from, chained_move.pos_to))
                    chained_move = chained_move.chained_move
                chain_moves = self.chain_moves.get(turn_side, {}).get(tuple(poss))
            else:
                chain_moves = None
            self.moves[turn_side] = {}
            self.chain_moves[turn_side] = {}
            while len(self.roll_history) < self.ply_count:
                self.roll_history.append({})
            while len(self.probabilistic_piece_history) < self.ply_count:
                self.probabilistic_piece_history.append(set())
            if turn_side == self.turn_side and probabilistic_pieces[turn_side]:
                signature = set()
                for piece in probabilistic_pieces[turn_side]:
                    signature |= {(piece.board_pos, type(piece))}
                old_signature = self.probabilistic_piece_history[self.ply_count - 1]
                if signature != old_signature:
                    self.clear_future_history(self.ply_count)
                    removed = old_signature.difference(signature)
                    for pos, piece_type in sorted(removed, key=lambda x: x[0]):
                        if pos in self.roll_history[self.ply_count - 1]:
                            del self.roll_history[self.ply_count - 1][pos]
                    added = signature.difference(old_signature)
                    for pos, piece_type in sorted(added, key=lambda x: x[0]):
                        if pos not in self.roll_history[self.ply_count - 1]:
                            piece = self.get_piece(pos)
                            if isinstance(piece.movement, ProbabilisticMovement):
                                self.roll_history[self.ply_count - 1][pos] = piece.movement.roll()
                    self.probabilistic_piece_history[self.ply_count - 1] = signature
            limits = self.piece_limits.get(turn_side, self.piece_limits)
            limit_groups = {}
            limit_hits = {}
            for order in self.get_order():
                order_rules = self.turn_rules.get(order, {})
                if {'check', 'checkmate'}.intersection(self.end_rules[turn_side]):
                    old_check_side = self.check_side
                    if opponent not in check_sides:
                        if opponent.value in order_rules or -opponent.value in order_rules:
                            self.load_pieces()
                            self.load_check(opponent)
                            if self.check_side == opponent:
                                check_sides[opponent] = True
                    self.check_side = old_check_side
                state_rules = [rules for rules in (
                    order_rules.get(0),
                    order_rules.get(-1 if check_sides.get(Side.WHITE, False) else 1),
                    order_rules.get(-2 if check_sides.get(Side.BLACK, False) else 2),
                ) if rules]
                last_history_to = set()
                last_history_fro = set()
                last_history_tags = set()
                last_history_types = set()
                last_history_pieces = set()
                last_history_partial = set()
                if self.move_history:
                    for i, last_history_move in enumerate(self.move_history[::-1], start=int(not self.chain_start)):
                        move_turn_side = self.get_turn_side(-i)
                        if move_turn_side != turn_side:
                            break
                        if last_history_move and not last_history_move.is_edit:
                            move_chain = []
                            while last_history_move:
                                valid = True
                                if last_history_move.is_edit:
                                    valid = False
                                if valid and (last_history_move.promotion or last_history_move.piece).side != turn_side:
                                    valid = False
                                if valid:
                                    move_chain.append(last_history_move)
                                last_history_move = last_history_move.chained_move
                            for last_history_chain_move in move_chain[::-1]:
                                last_history_to.add(last_history_chain_move.pos_to)
                                last_history_fro.add(last_history_chain_move.pos_from)
                                partial = False
                                if issubclass(last_history_chain_move.movement_type, CastlingPartnerMovement):
                                    partial = True
                                if not partial:
                                    if last_history_chain_move.movement_type:
                                        last_history_types.add(last_history_chain_move.movement_type.__name__)
                                    if last_history_chain_move.tag:
                                        last_history_types.add(last_history_chain_move.tag)
                                        last_history_tags.add(last_history_chain_move.tag)
                                board_piece = self.get_piece(last_history_chain_move.pos_to)
                                if isinstance(board_piece, NoPiece):
                                    continue
                                moved_piece = last_history_chain_move.promotion or last_history_chain_move.piece
                                if not board_piece.matches(moved_piece):
                                    continue
                                (last_history_partial if partial else last_history_pieces).add(board_piece.board_pos)
                                if not partial:
                                    piece_type = type(board_piece)
                                    last_history_types.update({piece_type.group(), piece_type.name, piece_type.type()})
                allow_last_rules = [
                    rules[k] for rules in state_rules for k in rules if
                    k == '*' or k in last_history_types or ('*' in k and fits(k, last_history_types))
                    or k and k[0] == '>' and any(self.in_area(k[1:], pos, turn_side) for pos in last_history_to)
                    or k and k[-1] == '>' and any(self.in_area(k[:-1], pos, turn_side) for pos in last_history_fro)
                ]
                block_last_rules = [
                    rules[k] for rules in allow_last_rules for k in rules
                    if k is None or k not in last_history_types
                    and ('*' not in k or not fits(k, last_history_types))
                    and (not k or k[0] != '>' or not any(self.in_area(k[1:], p, turn_side) for p in last_history_to))
                    and (not k or k[-1] != '>' or not any(self.in_area(k[:-1], p, turn_side) for p in last_history_fro))
                ]
                if not self.chain_start and block_last_rules:
                    self.load_pieces()
                    allow_piece_rules = [rules.get('*', {}) for rules in block_last_rules]
                    block_piece_rules = [rules.get(None, {}) for rules in allow_piece_rules]
                    allow_type_rules = [rules.get('*', {}) for rules in block_piece_rules]
                    block_type_rules = [rules.get(None, {}) for rules in allow_type_rules]
                    allow_pass_rules = [rules.get(s, {}) for rules in block_type_rules for s in ('*', 'pass')]
                    block_pass_rules = [rules.get(s, {}) for rules in allow_pass_rules for s in rules if s != 'pass']
                    if 0 in block_pass_rules and self.check_side != turn_side:
                        self.moves[turn_side]['pass'] = True
                    elif {1, -1}.intersection(block_pass_rules):
                        old_check_side = self.check_side
                        if opponent not in check_sides:
                            self.load_check(opponent)
                            if self.check_side == opponent:
                                check_sides[opponent] = True
                        self.check_side = old_check_side
                        if self.check_side != turn_side:
                            conditions = {1 if check_sides.get(opponent, False) else -1}
                            if conditions.intersection(block_pass_rules):
                                self.moves[turn_side]['pass'] = True
                        self.check_side = check_side
                piece_rules, allow_last_piece_rules, block_last_piece_rules, chain_piece_rules = {}, {}, {}, {}
                if not self.chain_start and self.use_drops and turn_side in self.drops:
                    side_drops = self.drops[turn_side]
                    for piece_type in self.captured_pieces[turn_side]:
                        if piece_type not in side_drops:
                            continue
                        if piece_type not in piece_rules:
                            allow_piece_rules = [
                                rules[s] for rules in block_last_rules for s in rules if self.fits(s, piece_type)
                            ]
                            block_piece_rules = [
                                rules[s] for rules in allow_piece_rules for s in rules if not self.fits(s, piece_type)
                            ]
                            piece_rules[piece_type] = block_piece_rules
                        if not piece_rules[piece_type]:
                            continue
                        drop_type = DropMovement.__name__
                        for pos in side_drops[piece_type]:
                            allow_type_rules = [
                                rules[s] for rules in piece_rules[piece_type] for s in rules if self.fits(s, drop_type)
                                or s and s[0] == '>' and self.in_area(s[1:], pos, turn_side)
                                or s and s[-1] == '>' and self.in_area(s[:-1], pos, turn_side)
                            ]
                            block_type_rules = [
                                rules[s] for rules in allow_type_rules for s in rules if not self.fits(s, drop_type)
                                and (not s or s[0] != '>' or not self.in_area(s[1:], pos, turn_side))
                                and (not s or s[-1] != '>' or not self.in_area(s[:-1], pos, turn_side))
                            ]
                            allow_drop_rules = [
                                rules.get(s, {}) for rules in block_type_rules for s in ('drop', '*')
                            ]
                            block_drop_rules = [
                                rules.get(s, {}) for rules in allow_drop_rules for s in rules if s != 'drop'
                            ]
                            if not block_drop_rules:
                                continue
                            for drop in side_drops[piece_type][pos]:
                                drop_type = type(drop) if isinstance(drop, Piece) else drop
                                if drop_type not in limit_hits:
                                    if drop_type not in limit_groups:
                                        limit_groups[drop_type] = {g for g in limits if self.fits(g, drop_type)}
                                    limit_hits[drop_type] = False
                                    for g in limit_groups[drop_type]:
                                        if self.piece_counts[turn_side].get(g, 0) >= limits[g]:
                                            limit_hits[drop_type] = True
                                            break
                                if limit_hits[drop_type]:
                                    continue
                            if self.not_a_piece(pos):
                                self.moves[turn_side].setdefault('drop', {}).setdefault(pos, set()).add(piece_type)
                for piece in movable_pieces[turn_side] if chain_moves is None else [last_chain_move.piece]:
                    piece_type = type(piece)
                    if chain_moves is not None:
                        if piece_type not in chain_piece_rules:
                            allow_piece_rules = [
                                rules[s] for rules in block_last_rules for s in rules
                                if s == '' or self.fits(s, piece_type)
                            ]
                            block_piece_rules = [
                                rules[s] for rules in allow_piece_rules for s in rules
                                if s in {None, ''} or not self.fits(s, piece_type)
                            ]
                            chain_piece_rules[piece_type] = block_piece_rules
                        piece_rule_list = chain_piece_rules[piece_type]
                    elif piece.board_pos in last_history_pieces:
                        if piece_type not in allow_last_piece_rules:
                            allow_piece_rules = [
                                rules[s] for rules in block_last_rules for s in rules
                                if s == '' or self.fits(s, piece_type)
                            ]
                            block_piece_rules = [
                                rules[s] for rules in allow_piece_rules for s in rules
                                if s is None or s and not self.fits(s, piece_type)
                            ]
                            allow_last_piece_rules[piece_type] = block_piece_rules
                        piece_rule_list = allow_last_piece_rules[piece_type]
                    elif piece.board_pos not in last_history_partial:
                        if piece_type not in block_last_piece_rules:
                            allow_piece_rules = [
                                rules[s] for rules in block_last_rules for s in rules
                                if self.fits(s, piece_type)
                            ]
                            block_piece_rules = [
                                rules[s] for rules in allow_piece_rules for s in rules
                                if s in {None, ''} or not self.fits(s, piece_type)
                            ]
                            block_last_piece_rules[piece_type] = block_piece_rules
                        piece_rule_list = block_last_piece_rules[piece_type]
                    else:
                        if piece_type not in piece_rules:
                            allow_piece_rules = [
                                rules[s] for rules in block_last_rules for s in rules
                                if self.fits(s, piece_type)
                            ]
                            block_piece_rules = [
                                rules[s] for rules in allow_piece_rules for s in rules
                                if s is None or s and not self.fits(s, piece_type)
                            ]
                            piece_rules[piece_type] = block_piece_rules
                        piece_rule_list = piece_rules[piece_type]
                    if not piece_rule_list:
                        continue
                    type_rule_dict = {}
                    for move in piece.moves() if chain_moves is None else chain_moves:
                        move_type = move.tag or (move.movement_type.__name__ if move.movement_type else '')
                        if move_type not in type_rule_dict:
                            allow_type_rules = [
                                rules[s] for rules in piece_rule_list for s in rules
                                if s == '*' or s == move_type
                                or s == '' and move.tag in last_history_tags
                                or ('*' in s and fits(s, move_type))
                                or s and s[0] == '>' and self.in_area(s[1:], move.pos_to, turn_side)
                                or s and s[-1] == '>' and self.in_area(s[:-1], move.pos_from, turn_side)
                            ]
                            block_type_rules = [
                                rules[s] for rules in allow_type_rules for s in rules
                                if s is None or s != move_type
                                and (s != '' or move.tag not in last_history_tags)
                                and ('*' not in s or not fits(s, move_type))
                                and (not s or s[0] != '>' or not self.in_area(s[1:], move.pos_to, turn_side))
                                and (not s or s[-1] != '>' or not self.in_area(s[:-1], move.pos_from, turn_side))
                            ]
                            type_rule_dict[move_type] = block_type_rules
                        type_rule_list = type_rule_dict[move_type]
                        if not type_rule_list:
                            continue
                        self.update_move(move)
                        if (
                            move.captured_piece
                            and move.piece.skips(move.captured_piece)
                            and not move.piece.captures(move.captured_piece)
                        ):
                            continue
                        # NB: The logic below considers one promotion per move, and does not keep track of piece amounts
                        # during the move analysis. Very complex moves can break this. Might need to rethink this later.
                        move_data = {
                            'move': True,
                            'capture': False,
                            'promotion': False
                        }
                        promotion = None
                        chained_move = move
                        while chained_move and chained_move.chained_move and (
                            issubclass(chained_move.movement_type, CastlingMovement) or
                            isinstance(chained_move.piece.movement, AutoCaptureMovement) or
                            issubclass(chained_move.chained_move.movement_type, CloneMovement)
                        ):
                            move_data['move'] = move_data['move'] and not chained_move.captured_piece
                            move_data['capture'] = move_data['capture'] or bool(chained_move.captured_piece)
                            move_data['promotion'] = move_data['promotion'] or bool(chained_move.promotion)
                            promotion = promotion or chained_move.promotion
                            chained_move = chained_move.chained_move
                        if chained_move:
                            move_data['move'] = move_data['move'] and not chained_move.captured_piece
                            move_data['capture'] = move_data['capture'] or bool(chained_move.captured_piece)
                            move_data['promotion'] = move_data['promotion'] or bool(chained_move.promotion)
                            promotion = promotion or chained_move.promotion
                        if promotion:
                            promotion_type = type(promotion) if isinstance(promotion, Piece) else promotion
                            if promotion_type not in limit_hits:
                                if promotion_type not in limit_groups:
                                    limit_groups[promotion_type] = {g for g in limits if self.fits(g, promotion_type)}
                                limit_hits[promotion_type] = False
                                for g in limit_groups[promotion_type]:
                                    if self.piece_counts[turn_side].get(g, 0) >= limits[g]:
                                        limit_hits[promotion_type] = True
                                        break
                            if limit_hits[promotion_type]:
                                continue
                        move_actions = {k: [] for k, v in move_data.items() if v}
                        allow_action_rules = [
                            rules[s] for rules in type_rule_list for s in rules if s == '*' or s in move_actions
                        ]
                        block_action_rules = [
                            rules[s] for rules in allow_action_rules for s in rules if s not in move_actions
                        ]
                        pass_actions = {'pass': not self.chain_start and 'pass' not in self.moves[turn_side],}
                        allow_pass_rules = [
                            rules[s] for rules in type_rule_list for s in rules if s == '*' or s in pass_actions
                        ]
                        block_pass_rules = [
                            rules[s] for rules in allow_pass_rules for s in rules if s not in pass_actions
                        ]
                        if not (block_action_rules or block_pass_rules):
                            continue
                        if block_pass_rules:
                            old_check_side = self.check_side
                            if opponent not in check_sides:
                                if {1, -1}.intersection(block_pass_rules):
                                    self.load_pieces()
                                    self.load_check(opponent)
                                    if self.check_side == opponent:
                                        check_sides[opponent] = True
                            self.check_side = old_check_side
                            if self.check_side != turn_side:
                                conditions = {0, 1 if check_sides.get(opponent, False) else -1}
                                if conditions.intersection(block_pass_rules):
                                    self.moves[turn_side]['pass'] = True
                            self.check_side = check_side
                        if block_action_rules:
                            self.update_auto_capture_markers(move, True)
                            self.update_auto_captures(move, turn_side.opponent())
                            self.move(move)
                            if isinstance(move.promotion, Piece):
                                self.promotion_piece = True
                                self.replace(move.piece, move.promotion)
                                self.update_promotion_auto_captures(move)
                                self.promotion_piece = None
                            move_chain = [move]
                            chained_move = move.chained_move
                            skipped = False
                            legal = True
                            self.load_pieces()
                            if (
                                {'check', 'checkmate'}.intersection(self.end_rules[turn_side.opponent()])
                                and chained_move and issubclass(type(move.piece), Slow)
                                and move.piece.board_pos in self.royal_markers[turn_side]
                            ):
                                self.load_check(turn_side)
                                if self.check_side == turn_side:
                                    legal = False
                            while legal and chained_move:
                                self.update_move(chained_move)
                                if (
                                    chained_move.captured_piece
                                    and chained_move.piece.skips(chained_move.captured_piece)
                                    and not chained_move.piece.captures(chained_move.captured_piece)
                                ):
                                    skipped = True
                                    legal = False
                                    break
                                self.move(chained_move)
                                if isinstance(chained_move.promotion, Piece):
                                    self.promotion_piece = True
                                    self.replace(chained_move.piece, chained_move.promotion)
                                    self.update_promotion_auto_captures(chained_move)
                                    self.promotion_piece = None
                                else:
                                    self.update_auto_capture_markers(chained_move)
                                move_chain.append(chained_move)
                                self.load_pieces()
                                if (
                                    {'check', 'checkmate'}.intersection(self.end_rules[turn_side.opponent()])
                                    and chained_move.chained_move and issubclass(type(chained_move.piece), Slow)
                                    and chained_move.piece.board_pos in self.royal_markers[turn_side]
                                ):
                                    self.load_check(turn_side)
                                    if self.check_side == turn_side:
                                        legal = False
                                if legal:
                                    chained_move = chained_move.chained_move
                            if legal:
                                self.load_pieces()
                                self.load_check(turn_side)
                                if self.check_side == turn_side:
                                    legal = False
                            loss_conditions = {'check', 'checkmate', 'capture'}
                            if legal:
                                if loss_conditions.intersection(self.end_rules[turn_side.opponent()]):
                                    for g in self.get_royal_loss(turn_side, move, loss_conditions):
                                        for condition in self.end_rules.get(turn_side.opponent(), {}):
                                            if condition in loss_conditions:
                                                need = self.end_rules[turn_side.opponent()][condition].get(g, 0)
                                                vals = self.end_data.get(turn_side.opponent(), {}).get(condition, {})
                                                if need == '+':
                                                    legal = False
                                                elif isinstance(need, int) and need > 0 and need - vals.get(g, 0) <= 1:
                                                    legal = False
                                            if not legal:
                                                break
                                        if not legal:
                                            break
                            if legal:
                                if loss_conditions.intersection(self.end_rules[turn_side]):
                                    for g in self.get_royal_loss(turn_side.opponent(), move, loss_conditions):
                                        for condition in self.end_rules.get(turn_side, {}):
                                            if condition in loss_conditions:
                                                need = self.end_rules[turn_side][condition].get(g, 0)
                                                vals = self.end_data.get(turn_side, {}).get(condition, {})
                                                if need == '-':
                                                    legal = False
                                                elif isinstance(need, int) and need < 0 and need + vals.get(g, 0) >= -1:
                                                    legal = False
                                            if not legal:
                                                break
                                        if not legal:
                                            break
                            loss_conditions = {'check', 'checkmate'}
                            if not skipped and not end_data[self.turn_side].get('checkmate', {}).get('', 0):
                                if loss_conditions.intersection(self.end_rules[self.turn_side]):
                                    for g in self.get_royal_loss(opponent, move, loss_conditions):
                                        for condition in self.end_rules.get(self.turn_side, {}):
                                            if condition in loss_conditions:
                                                need = self.end_rules[self.turn_side][condition].get(g, 0)
                                                vals = self.end_data.get(self.turn_side, {}).get(condition, {})
                                                in_check = False
                                                if need == '+':
                                                    in_check = True
                                                elif isinstance(need, int) and need > 0 and need - vals.get(g, 0) <= 1:
                                                    in_check = True
                                                if in_check:
                                                    self.moves[opponent] = {}
                                                    self.moves_queried[opponent] = True
                                                    end_data[self.turn_side]['checkmate'][''] = 1
                            if not skipped and not end_data[self.turn_side].get('checkmate', {}).get('', 0):
                                if loss_conditions.intersection(self.end_rules[opponent]):
                                    for g in self.get_royal_loss(self.turn_side, move, loss_conditions):
                                        for condition in self.end_rules.get(opponent, {}):
                                            if condition in loss_conditions:
                                                need = self.end_rules[opponent][condition].get(g, 0)
                                                vals = self.end_data.get(opponent, {}).get(condition, {})
                                                in_check = False
                                                if need == '-':
                                                    in_check = True
                                                elif isinstance(need, int) and need < 0 and need + vals.get(g, 0) >= -1:
                                                    in_check = True
                                                if in_check:
                                                    self.moves[opponent] = {}
                                                    self.moves_queried[opponent] = True
                                                    end_data[self.turn_side]['checkmate'][''] = 1
                            if legal:
                                old_check_side = self.check_side
                                new_check_side = Side.NONE
                                if {1, -1}.intersection(block_action_rules):
                                    self.load_pieces()
                                    self.load_check(opponent)
                                    new_check_side = self.check_side
                                self.check_side = old_check_side
                                conditions = {0, 1 if new_check_side == opponent else -1}
                                if conditions.intersection(block_action_rules):
                                    pos_from, pos_to = move.pos_from, move.pos_to or move.pos_from
                                    if pos_from == pos_to and move.captured_piece is not None:
                                        pos_to = move.captured_piece.board_pos
                                    self.moves[turn_side].setdefault(pos_from, {}).setdefault(pos_to, []).append(move)
                                    chained_move = self.chain_start
                                    poss = []
                                    while chained_move:
                                        poss.extend((chained_move.pos_from, chained_move.pos_to))
                                        chained_move = chained_move.chained_move
                                    chained_move = move
                                    while chained_move and chained_move.chained_move and (
                                        issubclass(chained_move.movement_type, CastlingMovement) or
                                        isinstance(chained_move.piece.movement, AutoCaptureMovement) or
                                        issubclass(chained_move.chained_move.movement_type, CloneMovement)
                                    ):
                                        poss.extend((chained_move.pos_from, chained_move.pos_to))
                                        chained_move = chained_move.chained_move
                                    poss.extend((chained_move.pos_from, chained_move.pos_to))
                                    if chained_move.chained_move:
                                        self.chain_moves[turn_side].setdefault(tuple(poss), []).append(
                                            chained_move.chained_move
                                        )
                            for chained_move in move_chain[::-1]:
                                self.undo(chained_move)
                                self.revert_auto_capture_markers(chained_move)
                            self.en_passant_targets = deepcopy(en_passant_targets)
                            self.en_passant_markers = deepcopy(en_passant_markers)
                            self.royal_ep_targets = deepcopy(royal_ep_targets)
                            self.royal_ep_markers = deepcopy(royal_ep_markers)
                            self.end_data = deepcopy(end_data)
                            self.check_side = check_side
                if self.moves[turn_side]:
                    self.moves_queried[turn_side] = True
                    break
            else:
                self.moves_queried[turn_side] = True
        if theoretical_moves_for is None:
            self.end_data = deepcopy(end_data)
            self.load_end_conditions()
            if self.game_over and self.win_side == self.turn_side:
                theoretical_moves_for = Side.NONE
            else:
                theoretical_moves_for = opponent
        if theoretical_moves_for == Side.ANY:
            turn_sides = [self.turn_side, opponent]
        elif theoretical_moves_for == Side.NONE:
            turn_sides = []
        else:
            turn_sides = [theoretical_moves_for]
        self.display_theoretical_moves = {side: False for side in self.display_theoretical_moves}
        for turn_side in turn_sides:
            self.display_theoretical_moves[turn_side] = True
            if self.theoretical_moves_queried.get(turn_side, False):
                continue
            self.theoretical_moves[turn_side] = {}
            for piece in movable_pieces[turn_side]:
                for move in piece.moves(theoretical=True):
                    pos_from, pos_to = move.pos_from, move.pos_to or move.pos_from
                    self.theoretical_moves[turn_side].setdefault(pos_from, {}).setdefault(pos_to, []).append(move)
            self.theoretical_moves_queried[turn_side] = True
        self.movable_pieces = movable_pieces
        self.piece_counts = piece_counts
        self.area_groups = area_groups
        self.royal_groups = royal_groups
        self.royal_pieces = royal_pieces
        self.royal_markers = royal_markers
        self.anti_royal_pieces = anti_royal_pieces
        self.anti_royal_markers = anti_royal_markers
        self.probabilistic_pieces = probabilistic_pieces
        self.auto_ranged_pieces = auto_ranged_pieces
        self.auto_capture_markers = auto_capture_markers
        self.en_passant_targets = en_passant_targets
        self.en_passant_markers = en_passant_markers
        self.royal_ep_targets = royal_ep_targets
        self.royal_ep_markers = royal_ep_markers
        self.check_side = check_side
        self.end_data = end_data

    def unique_moves(self, side: Side | None = None) -> dict[Side, dict[Position, list[Move]]]:
        if side is None:
            side = self.turn_side
        display_moves = copy(self.display_moves)
        display_theoretical_moves = copy(self.display_theoretical_moves)
        self.load_moves(False, moves_for=side)
        self.display_moves = display_moves
        self.display_theoretical_moves = display_theoretical_moves
        if side == Side.ANY:
            turn_sides = [Side.WHITE, Side.BLACK]
        elif side == Side.NONE:
            turn_sides = []
        else:
            turn_sides = [side]
        moves = {}
        for turn_side in turn_sides:
            moves[turn_side] = {}
            move_data_set = set()
            for move in sum((
                sum(v.values(), []) for k, v in self.moves.get(self.turn_side, {}).items() if not isinstance(k, str)
            ), []):
                move_data = [move.pos_from]
                if move.pos_from == move.pos_to and move.captured_piece:
                    move_data.append(move.captured_piece.board_pos)
                else:
                    move_data.append(move.pos_to)
                if move.promotion is not None:
                    move_data.append(type(move.promotion))
                move_data = tuple(move_data)
                if move_data not in move_data_set:
                    move_data_set.add(move_data)
                    move = copy(move)
                    chained_move = self.chain_start
                    poss = []
                    while chained_move:
                        poss.extend((chained_move.pos_from, chained_move.pos_to))
                        chained_move = chained_move.chained_move
                    chained_move = move
                    while chained_move and chained_move.chained_move and (
                        issubclass(chained_move.movement_type, CastlingMovement) or
                        isinstance(chained_move.piece.movement, AutoCaptureMovement) or
                        issubclass(chained_move.chained_move.movement_type, CloneMovement)
                    ):
                        poss.extend((chained_move.pos_from, chained_move.pos_to))
                        chained_move = chained_move.chained_move
                    poss.extend((chained_move.pos_from, chained_move.pos_to))
                    if chained_move.chained_move or self.chain_moves.get(self.turn_side, {}).get(tuple(poss)):
                        chained_move.chained_move = Unset  # do not chain moves, we are only counting one-move sequences
                    moves[turn_side].setdefault(move.pos_from, []).append(move)
        return moves

    def find_move(self, pos_from: Position, pos_to: Position) -> Move | None:
        if self.turn_side in self.moves:
            if pos_from in (side_moves := self.moves[self.turn_side]):
                if pos_to in (from_moves := side_moves[pos_from]):
                    if to_moves := from_moves[pos_to]:
                        return copy(to_moves[0])
        return None

    def show_moves(self, with_markers: bool = True) -> None:
        self.hide_moves()
        self.update_caption()
        move_sprites = dict()
        with_move = True
        if self.hide_move_markers:
            with_markers = False
        pos = self.selected_square or self.hovered_square
        if not pos and self.is_active:
            pos = self.highlight_square
        if self.on_board(pos) and with_markers:
            piece = self.get_piece(pos)
            if self.hide_move_markers is False or not piece.is_hidden and not isinstance(piece, NoPiece):
                move_dict = {}
                use_type_markers = self.move_type_markers
                if self.display_theoretical_moves.get(piece.side, False):
                    move_dict = self.theoretical_moves.get(piece.side, {})
                elif self.display_moves.get(piece.side, False):
                    move_dict = self.moves.get(piece.side, {})
                pos_dict = {k: v for k, v in move_dict.get(pos, {}).items()}
                if  not use_type_markers and self.can_pass() and pos not in pos_dict:
                    pos_dict[pos] = [False]
                for pos_to, moves in pos_dict.items():
                    move_marker_list = []
                    move_marker_set = set()
                    move_marker_seven = ''
                    for move in moves:
                        if move is False:
                            move_marker_list.append(False)
                            move_marker_set.add(False)
                        elif not use_type_markers:
                            if not move.is_legal:
                                continue
                            if move_marker_set or move_marker_list:
                                break
                            move_marker_list.append(self.not_a_piece(pos_to))
                            move_marker_set.add(move_marker_list[-1])
                        else:
                            for mark in move.marks:
                                if mark in {'7', '/'}:
                                    move_marker_seven += mark
                                elif move_marker_seven:
                                    move_marker_list.append(move_marker_seven)
                                    move_marker_set.add(move_marker_seven)
                                    move_marker_seven = ''
                                if not move_marker_seven and mark not in move_marker_set:
                                    move_marker_list.append(mark)
                                    move_marker_set.add(mark)
                            if move_marker_seven:
                                move_marker_list.append(move_marker_seven)
                                move_marker_set.add(move_marker_seven)
                                move_marker_seven = ''
                    if not move_marker_list:
                        continue
                    if not use_type_markers:
                        mark = Sprite(f"assets/util/{'move' if move_marker_list[0] else 'capture'}.png")
                        mark.color = self.color_scheme[f"{'selection' if self.selected_square else 'highlight'}_color"]
                        mark.position = self.get_screen_position(pos_to)
                        mark.scale = self.square_size / mark.texture.width
                        self.move_sprite_list.append(mark)
                        move_sprites[pos_to] = mark
                    else:
                        move_sprites[pos_to] = []
                        area = len(move_marker_list)
                        width = 1 + isqrt(area - 1)
                        height = ceil(area / width)
                        diff = width * height - area
                        for i, mark_type in enumerate(move_marker_list):
                            xi, yi = i % width, i // width
                            diff_width = width - (diff if yi == height - 1 else 0)
                            square = self.get_screen_position(pos_to)
                            if mark_type[0] == '7':
                                mark_types = mark_type.split('/')
                                index, count = len(mark_types[0]) - 1, len(mark_types[1])
                                angle = index / count * 360
                                mark_type = '7'
                            else:
                                angle = 0
                            mark = Sprite(f"assets/move/{mark_type}.png")
                            mark.color = self.color_scheme["background_color"]
                            mark.position = (
                                square[0] + self.square_size * ((xi + 0.5) / diff_width - 0.5),
                                square[1] + self.square_size * (0.5 - (yi + 0.5) / height),
                            )
                            mark.scale = (self.square_size / width) / mark.texture.width * (2 if area > 1 else 1)
                            mark.angle = angle
                            self.type_sprite_list.append(mark)
                            move_sprites[pos_to].append(mark)
                        with_move = False
        if with_move and self.move_history and not self.edit_mode:
            move = self.move_history[-1]
            if move is not None and not move.is_edit:
                pos_from, pos_to = move.pos_from, move.pos_to
                last_move = move
                captures = []
                while last_move.chained_move:
                    if last_move.captured_piece:
                        captures.append(last_move.captured_piece.board_pos)
                    if last_move.pos_from == pos_to:
                        pos_to = last_move.pos_to
                    last_move = last_move.chained_move
                if last_move.pos_from == pos_to:
                    pos_to = last_move.pos_to
                pos_to = pos_to
                if last_move.captured_piece:
                    captures.append(last_move.captured_piece.board_pos)
                if pos_from is not None and pos_from != pos_to:
                    if pos_from in move_sprites and not self.not_a_piece(pos_from):
                        move_sprites[pos_from].color = self.color_scheme['selection_color']
                    else:
                        sprite = Sprite(f"assets/util/{'capture' if self.not_a_piece(pos_from) else 'selection'}.png")
                        sprite.color = self.color_scheme['selection_color']
                        sprite.position = self.get_screen_position(pos_from)
                        sprite.scale = self.square_size / sprite.texture.width
                        self.move_sprite_list.append(sprite)
                if pos_to is not None:
                    if pos_to in move_sprites:
                        move_sprites[pos_to].color = self.color_scheme['selection_color']
                    else:
                        sprite = Sprite(f"assets/util/{'capture' if self.not_a_piece(pos_to) else 'selection'}.png")
                        sprite.color = self.color_scheme['selection_color']
                        sprite.position = self.get_screen_position(pos_to)
                        sprite.scale = self.square_size / sprite.texture.width
                        self.move_sprite_list.append(sprite)
                for capture in captures:
                    if capture == pos_to:
                        continue
                    if capture in move_sprites:
                        move_sprites[capture].color = self.color_scheme['selection_color']
                    else:
                        sprite = Sprite(f"assets/util/{'capture' if self.not_a_piece(capture) else 'selection'}.png")
                        sprite.color = self.color_scheme['highlight_color']
                        sprite.position = self.get_screen_position(capture)
                        sprite.scale = self.square_size / sprite.texture.width
                        self.move_sprite_list.append(sprite)

    def hide_moves(self) -> None:
        self.move_sprite_list.clear()
        self.type_sprite_list.clear()

    def can_pass(self, side: Side = None) -> bool:
        return not self.game_over and self.moves.get(side or self.turn_side, {}).get('pass')

    def update_highlight(self, pos: Position | None) -> None:
        if self.clicked_square != pos:
            self.square_was_clicked = False
            self.clicked_square = None
        if pos is not None:
            self.highlight.position = self.get_screen_position(pos)
        if not self.is_active:
            return
        old_hovered_square = self.hovered_square
        if not self.is_active or self.not_on_board(pos):
            self.highlight.color = (0, 0, 0, 0)
            self.hovered_square = None
            if (self.selected_square is None and not self.move_history) or self.promotion_piece:
                self.hide_moves()
            else:
                self.show_moves()
        elif self.is_active:
            self.highlight.color = self.color_scheme['highlight_color']
            if self.hovered_square != pos:
                self.hovered_square = pos
                if self.selected_square is None and not self.promotion_piece:
                    self.show_moves()
                elif self.promotion_piece:
                    self.hide_moves()
        if self.hovered_square != old_hovered_square:
            self.update_caption()

    def update_move(self, move: Move) -> None:
        if move.pos_from:
            move.set(piece=self.get_piece(move.pos_from))
        elif not move.piece and move.pos_to:
            move.set(piece=self.get_piece(move.pos_to))
        new_piece = move.swapped_piece or move.captured_piece
        new_piece = self.get_piece(new_piece.board_pos if new_piece is not None else move.pos_to)
        if move.piece != new_piece and not isinstance(new_piece, NoPiece):
            if move.swapped_piece is not None:
                move.set(swapped_piece=new_piece)
            else:
                move.set(captured_piece=new_piece)

    def update_auto_captures(self, move: Move, side: Side) -> None:
        if move.is_edit:
            return
        while move.chained_move and not (
            issubclass(move.chained_move.movement_type, AutoCaptureMovement)
            and ((piece := move.chained_move.piece) and piece.side == side)
        ):
            move = move.chained_move
        if move.promotion is Unset:
            return  # and generate later
        if move.pos_to in self.auto_capture_markers[side]:
            piece_poss = self.auto_capture_markers[side][move.pos_to]
            piece_pos = sorted(list(piece_poss))[0]
            piece = self.get_piece(piece_pos)
            moved = self.get_piece(move.pos_to) if isinstance(move.piece, NoPiece) or move.promotion else move.piece
            if piece.side == side and piece.captures(moved):
                chained_move = Move(
                    piece=piece,
                    movement_type=AutoCaptureMovement,
                    pos_from=piece_pos,
                    pos_to=piece_pos,
                    captured_piece=moved,
                )
                move.chained_move = chained_move

    def update_promotion_auto_captures(self, move: Move) -> None:
        piece = self.get_piece(move.pos_to)
        last_move = move
        while last_move.chained_move and not issubclass(last_move.chained_move.movement_type, AutoCaptureMovement):
            last_move = last_move.chained_move
        last_move.chained_move = None
        if isinstance(piece.movement, AutoCaptureMovement):
            piece.movement.generate_captures(last_move, piece)
        self.update_auto_capture_markers(move, True)
        self.update_auto_captures(move, piece.side.opponent())

    def load_auto_capture_markers(self, side: Side = Side.ANY) -> None:
        for side in self.auto_ranged_pieces if side is Side.ANY else (side,):
            for piece in self.auto_ranged_pieces[side]:
                if isinstance(piece.movement, AutoRangedAutoCaptureRiderMovement):
                    piece.movement.mark(piece.board_pos, piece)

    def clear_auto_capture_markers(self, side: Side = Side.ANY) -> None:
        for side in self.auto_capture_markers if side is Side.ANY else (side,):
            self.auto_capture_markers[side].clear()

    def update_auto_capture_markers(self, move: Move, recursive: bool = False) -> None:
        while move:
            moved_piece = move.piece
            if move.promotion:
                if moved_piece and isinstance(moved_piece.movement, AutoRangedAutoCaptureRiderMovement):
                    moved_piece.movement.unmark(move.pos_to, moved_piece)
                moved_piece = self.get_piece(move.pos_to)
            if isinstance(moved_piece.movement, AutoRangedAutoCaptureRiderMovement):
                if move.pos_to is None or move.is_edit:
                    moved_piece.movement.unmark(move.pos_from, moved_piece)
                if move.pos_from is None or move.is_edit or move.promotion:
                    moved_piece.movement.mark(move.pos_to, moved_piece)
            if move.captured_piece is not None:
                if isinstance(move.captured_piece.movement, AutoRangedAutoCaptureRiderMovement):
                    move.captured_piece.movement.unmark(move.captured_piece.board_pos, move.captured_piece)
            if move.swapped_piece is not None:
                if isinstance(move.swapped_piece.movement, AutoRangedAutoCaptureRiderMovement):
                    move.swapped_piece.movement.unmark(move.pos_to, move.swapped_piece)
                    move.swapped_piece.movement.mark(move.pos_from, move.swapped_piece)
            if not recursive:
                return
            move = move.chained_move

    def revert_auto_capture_markers(self, move: Move, recursive: bool = False) -> None:
        move_list = []
        if recursive:
            while move:
                move_list.append(move)
                move = move.chained_move
        for move in (reversed(move_list) if recursive else [move]):
            if move.promotion:
                moved_piece = self.get_piece(move.pos_to)
                if isinstance(moved_piece.movement, AutoRangedAutoCaptureRiderMovement):
                    moved_piece.movement.unmark(move.pos_to, moved_piece)
            moved_piece = move.piece
            if isinstance(moved_piece.movement, AutoRangedAutoCaptureRiderMovement):
                if move.pos_from is None or move.is_edit:
                    moved_piece.movement.unmark(move.pos_to, moved_piece)
                if move.pos_to is None or move.is_edit or move.promotion:
                    moved_piece.movement.mark(move.pos_from, moved_piece)
            if move.captured_piece is not None:
                if isinstance(move.captured_piece.movement, AutoRangedAutoCaptureRiderMovement):
                    move.captured_piece.movement.mark(move.captured_piece.board_pos, move.captured_piece)
            if move.swapped_piece is not None:
                if isinstance(move.swapped_piece.movement, AutoRangedAutoCaptureRiderMovement):
                    move.swapped_piece.movement.unmark(move.pos_from, move.swapped_piece)
                    move.swapped_piece.movement.mark(move.pos_to, move.swapped_piece)

    def update_en_passant_markers(self, move: Move | None = None) -> None:
        for target_dict, marker_dict in (
            (self.en_passant_targets, self.en_passant_markers),
            (self.royal_ep_targets, self.royal_ep_markers),
        ):
            if not move or not move.is_edit:
                current_side = self.turn_side
                last_side = self.get_turn_side(-1)
                next_side = self.get_turn_side(+1)
                chain_end = not move or move.chained_move is None
                is_first_turn = current_side != last_side
                is_final_turn = current_side != next_side
                for side in {current_side, current_side.opponent()}:
                    side_target_dict, side_marker_dict = target_dict.get(side, {}), marker_dict.get(side, {})
                    for pos in list(side_target_dict):
                        if move and pos == move.pos_to:
                            continue
                        pos_target_set = side_target_dict.get(pos, ())
                        if 'skip' in pos_target_set:
                            pos_target_set.discard('skip')
                            continue
                        if Slow in pos_target_set:
                            if chain_end:
                                pos_target_set.discard(Slow)
                            continue
                        if Delayed1 in pos_target_set and not (side == last_side and is_first_turn):
                            continue
                        if Delayed in pos_target_set and not (side == next_side and is_final_turn and chain_end):
                            continue
                        markers = side_target_dict.pop(pos, ())
                        for marker in markers:
                            side_marker_dict.pop(marker, None)
            if move:
                if move.captured_piece is not None:
                    for pos in target_dict.get(move.captured_piece.side, {}).pop(move.captured_piece.board_pos, ()):
                        marker_dict.get(move.captured_piece.side, {}).pop(pos, None)
                for piece, old_pos in ((move.piece, move.pos_from), (move.swapped_piece, move.pos_to)):
                    if piece is None:
                        continue
                    pos_from, pos_to = old_pos, piece.board_pos
                    if pos_from == pos_to:
                        continue
                    if move.is_edit or not issubclass(type(piece), Slow):
                        for pos in target_dict.get(piece.side, {}).pop(pos_from, ()):
                            marker_dict.get(piece.side, {}).pop(pos, None)
                    else:
                        from_markers = target_dict.get(piece.side, {}).pop(pos_from, ())
                        if from_markers:
                            target_dict.get(piece.side, {}).setdefault(pos_to, set()).update(from_markers)
                            if piece.side in marker_dict:
                                side_marker_dict = marker_dict[piece.side]
                                for pos in from_markers:
                                    side_marker_dict[pos] = pos_to

    def reload_en_passant_markers(self) -> None:
        self.clear_en_passant_markers()
        if not self.move_history:
            return
        ply_count = self.ply_count
        last_side = self.get_turn_side()
        side_count = 0
        last_moves = []
        for move in self.move_history[::-1]:
            if move:
                move_chain = [move]
                while move_chain[-1].chained_move:
                    move_chain.append(move_chain[-1].chained_move)
                for chained_move in move_chain[::-1]:
                    if (
                        chained_move.is_edit != 1 and chained_move.movement_type and chained_move.piece.movement
                        and not issubclass(chained_move.movement_type, (CloneMovement, DropMovement))
                    ):
                        chained_move.piece.movement.undo(chained_move, chained_move.piece)
                if move.is_edit:
                    last_moves.append(move)
                    continue
            last_moves.append(move)
            self.shift_ply(-1)
            if self.turn_side != last_side:
                if side_count:
                    break
                side_count += 1
                last_side = self.turn_side
        for move in last_moves[::-1]:
            if (
                move and move.is_edit != 1 and move.movement_type and move.piece.movement
                and not issubclass(move.movement_type, (CloneMovement, DropMovement))
            ):
                move.piece.movement.update(move, move.piece)
            self.update_en_passant_markers(move)
            if move:
                chained_move = move.chained_move
                while chained_move:
                    if (
                        chained_move.is_edit != 1 and chained_move.movement_type and chained_move.piece.movement
                        and not issubclass(chained_move.movement_type, (CloneMovement, DropMovement))
                    ):
                        chained_move.piece.movement.update(chained_move, chained_move.piece)
                    self.update_en_passant_markers(chained_move)
                    chained_move = chained_move.chained_move
                if move.is_edit:
                    continue
            self.shift_ply(+1)
        if ply_count != self.ply_count:
            self.log(
                "Error: Ply count mismatch during en passant marker reload "
                f"(expected {ply_count}, got {self.ply_count})"
            )
            self.shift_ply(ply_count - self.ply_count)

    def clear_en_passant_markers(self) -> None:
        for target_dict, marker_dict in (
            (self.en_passant_targets, self.en_passant_markers),
            (self.royal_ep_targets, self.royal_ep_markers),
        ):
            for side in target_dict:
                target_dict[side].clear()
                marker_dict[side].clear()

    def update_relay_markers(self, move: Move | None = None):
        while move:
            if move.piece and move.pos_from != move.pos_to or move.promotion:
                markers = self.relay_markers.get(move.piece.side, {}).pop(move.pos_from, set())
                pieces = self.relay_pieces.get(move.piece.side, {})
                for group, pos in markers:
                    if group in pieces and pos in pieces[group]:
                        pieces[group].pop(pos, None)
            if move.captured_piece:
                markers = self.relay_markers.get(move.captured_piece.side, {}).pop(move.captured_piece.board_pos, set())
                pieces = self.relay_pieces.get(move.captured_piece.side, {})
                for group, pos in markers:
                    if group in pieces and pos in pieces[group]:
                        pieces[group].pop(pos, None)
            if move.swapped_piece:
                markers = self.relay_markers.get(move.swapped_piece.side, {}).pop(move.pos_to, set())
                pieces = self.relay_pieces.get(move.swapped_piece.side, {})
                for group, pos in markers:
                    if group in pieces and pos in pieces[group]:
                        pieces[group].pop(pos, None)
            move = move.chained_move

    def revert_relay_markers(self, move: Move | None = None):
        move_chain = []
        while move:
            move_chain.append(move)
            move = move.chained_move
        for move in move_chain[::-1]:
            if move.piece and move.pos_from != move.pos_to or move.promotion:
                piece = move.promotion or move.piece
                markers = self.relay_markers.get(piece.side, {}).pop(move.pos_to, set())
                pieces = self.relay_pieces.get(piece.side, {})
                for group, pos in markers:
                    if group in pieces and pos in pieces[group]:
                        pieces[group].pop(pos, None)
            if move.swapped_piece:
                markers = self.relay_markers.get(move.swapped_piece.side, {}).pop(move.pos_from, set())
                pieces = self.relay_pieces.get(move.swapped_piece.side, {})
                for group, pos in markers:
                    if group in pieces and pos in pieces[group]:
                        pieces[group].pop(pos, None)

    def clear_relay_markers(self) -> None:
        for target_dict in (self.relay_pieces, self.relay_markers):
            for side in target_dict:
                target_dict[side].clear()

    def update_end_data(self, move: Move | None = None) -> None:
        if self.edit_mode or (move and move.is_edit):
            return
        opponent = self.turn_side.opponent()
        if 'check' in self.end_rules[opponent] and self.check_side == self.turn_side:
            for group in ('', *self.check_groups):
                if group in self.end_data[opponent]['check']:
                    self.end_data[opponent]['check'][group] += 1
        if not move:
            return
        for side in {self.turn_side, self.turn_side.opponent()}:
            if 'checkmate' not in self.end_rules[side] and 'capture' not in self.end_rules[side]:
                continue
            if 'checkmate' in self.end_rules[side]:
                for group in self.get_royal_loss(side.opponent(), move, {'checkmate'}):
                    if group in self.end_data[side]['checkmate']:
                        self.end_data[side]['checkmate'][group] += 1
            if 'capture' in self.end_rules[side]:
                for group in self.get_royal_loss(side.opponent(), move, {'capture'}):
                    if group in self.end_data[side]['capture']:
                        self.end_data[side]['capture'][group] += 1

    def revert_end_data(self, move: Move | None = None) -> None:
        if self.edit_mode or (move and move.is_edit):
            return
        for side in {self.turn_side, self.turn_side.opponent()}:
            if 'checkmate' in self.end_rules[side]:
                self.end_data[side]['checkmate'][''] = 0
            if 'stalemate' in self.end_rules[side]:
                self.end_data[side]['stalemate'][''] = 0
        opponent = self.turn_side.opponent()
        if 'check' in self.end_rules[opponent] and self.check_side == self.turn_side:
            for group in ('', *self.check_groups):
                if group in self.end_data[opponent]['check']:
                    self.end_data[opponent]['check'][group] -= 1
        if not move:
            return
        for side in {self.turn_side, self.turn_side.opponent()}:
            if 'checkmate' not in self.end_rules[side] and 'capture' not in self.end_rules[side]:
                continue
            if 'checkmate' in self.end_rules[side]:
                for group in self.get_royal_loss(side.opponent(), move, {'checkmate'}):
                    if group in self.end_data[side]['checkmate']:
                        self.end_data[side]['checkmate'][group] -= 1
            if 'capture' in self.end_rules[side]:
                for group in self.get_royal_loss(side.opponent(), move, {'capture'}):
                    if group in self.end_data[side]['capture']:
                        self.end_data[side]['capture'][group] -= 1

    def reload_end_data(self, _: Move | None = None) -> None:
        if self.edit_mode:
            return
        opponent = self.turn_side.opponent()
        if not self.moves.get(self.turn_side) and self.moves_queried.get(self.turn_side, False):
            if 'checkmate' in self.end_rules[opponent] and self.check_side == self.turn_side:
                self.end_data[opponent]['checkmate'][''] = 1
            if 'stalemate' in self.end_rules[opponent] and self.check_side != self.turn_side:
                self.end_data[opponent]['stalemate'][''] = 1

    def unload_end_data(self, _: Move | None = None) -> None:
        for side in {self.turn_side, self.turn_side.opponent()}:
            if 'checkmate' in self.end_rules[side]:
                self.end_data[side]['checkmate'][''] = 0
            if 'stalemate' in self.end_rules[side]:
                self.end_data[side]['stalemate'][''] = 0

    def clear_future_history(self, since: int) -> None:
        self.future_move_history = []
        self.roll_history = self.roll_history[:since]
        self.probabilistic_piece_history = self.probabilistic_piece_history[:since]

    def compare_history(self) -> None:
        # check if the last move matches the first future move
        if self.future_move_history and self.move_history:  # if there are any moves to compare that is
            if (
                (self.move_history[-1] is None) == (self.future_move_history[-1] is None)
                and (self.move_history[-1] is None or self.move_history[-1].matches(self.future_move_history[-1]))
            ):
                self.future_move_history.pop()  # if it does, the other future moves are still makeable, so we keep them
            else:
                self.clear_future_history(self.ply_count - 1)  # otherwise, we cannot redo the future moves - clear them

    def reload_history(self) -> bool:
        edit_mode = self.edit_mode
        selection = self.selected_square
        self.reset_board(update=False, log=False)  # Don't clear redoing data, we're going to use it for, well, redoing.
        # Also, a restart message should have been logged prior to this function being called, so we do not log it here.
        if not self.future_move_history:
            self.select_piece(selection)
            self.edit_mode = edit_mode
            return True
        future_move_history = self.future_move_history
        self.future_move_history = []
        finished = False
        next_move = future_move_history.pop()
        while True:
            chained = False
            if next_move is None:
                log_pass = self.board_config['log_pass']
                if log_pass is None:
                    log_pass = set(self.moves[self.turn_side]) != {'pass'}
                turn_side = self.get_turn_side(+1)
                if log_pass:
                    self.log(f"Pass: {turn_side} to move")
                self.move_history.append(None)
                self.shift_ply(+1)
            elif next_move.is_edit:
                self.update_move(next_move)
                self.move(next_move)
                self.update_auto_capture_markers(next_move)
                self.move_history.append(deepcopy(next_move))
                self.apply_edit_promotion(next_move)
                if next_move.promotion is Unset:
                    finished = True
                    break
                else:
                    self.log(f"Edit: {self.move_history[-1]}")
            elif next_move.movement_type == DropMovement:
                pos = next_move.pos_to
                if not self.not_on_board(pos) and self.not_a_piece(pos):
                    if next_move.promotion is Unset:
                        self.try_drop(next_move)
                    if next_move.promotion is Unset:
                        self.move_history.append(next_move)
                        finished = True
                        break
                    continue
                else:
                    finished = False
                    break
            else:
                move = self.find_move(next_move.pos_from, next_move.pos_to)
                if move is None:
                    finished = False
                    break
                self.update_move(move)
                if next_move.promotion is not None:
                    move.promotion = next_move.promotion
                chained_move = self.chain_start
                poss = []
                while chained_move:
                    poss.extend((chained_move.pos_from, chained_move.pos_to))
                    chained_move = chained_move.chained_move
                chained_move = move
                while chained_move and chained_move.chained_move and (
                    issubclass(chained_move.movement_type, CastlingMovement) or
                    isinstance(chained_move.piece.movement, AutoCaptureMovement) or
                    issubclass(chained_move.chained_move.movement_type, CloneMovement)
                ):
                    poss.extend((chained_move.pos_from, chained_move.pos_to))
                    chained_move = chained_move.chained_move
                poss.extend((chained_move.pos_from, chained_move.pos_to))
                if chained_move.chained_move or self.chain_moves.get(self.turn_side, {}).get(tuple(poss)):
                    chained_move.chained_move = Unset  # do not chain moves because we're updating every move separately
                self.update_auto_capture_markers(move, True)
                self.update_auto_captures(move, self.turn_side.opponent())
                chained_move = move
                while chained_move:
                    self.move(chained_move)
                    self.update_auto_capture_markers(chained_move)
                    chained_move.set(piece=copy(chained_move.piece))
                    if self.promotion_piece is None:
                        self.log(f"Move: {chained_move}")
                    chained_move = chained_move.chained_move
                    if chained_move:
                        next_move = next_move.chained_move
                if self.chain_start is None:
                    self.chain_start = deepcopy(move)
                    self.move_history.append(self.chain_start)
                else:
                    last_move = self.chain_start
                    while last_move.chained_move:
                        last_move = last_move.chained_move
                    last_move.chained_move = deepcopy(move)
                if chained_move is Unset and not self.promotion_piece:
                    self.load_pieces()
                    self.load_moves()
                    chained = True
                else:
                    self.chain_start = None
                    if self.promotion_piece is None:
                        self.shift_ply(+1)
                    else:
                        finished = True
                        break
            if not chained:
                self.unload_end_data()
                self.load_pieces()
                self.load_check()
                self.update_end_data(self.move_history[-1])
                self.load_moves()
                self.reload_end_data()
                self.advance_turn()
            else:
                if next_move:
                    next_move = next_move.chained_move
                if next_move:
                    continue
                elif next_move is Unset:
                    finished = True
                    break
            if future_move_history:
                next_move = future_move_history.pop()
            else:
                finished = True
                break
        if finished:
            self.select_piece(selection)
            self.edit_mode = edit_mode
        return finished

    def move(self, move: Move) -> None:
        self.skip_caption_update = True
        self.deselect_piece()
        if move.piece is not None and move.pos_to is not None:
            # piece was moved to a different square, set its position to the new square
            self.set_position(move.piece, move.pos_to)
        if move.swapped_piece is not None:
            # piece was swapped with another piece, set the swapped piece's position to the square the move started from
            self.set_position(move.swapped_piece, move.pos_from)
        if move.piece is not None and move.pos_to is None:
            # piece was removed from the board, empty the square it was on
            self.piece_sprite_list.remove(move.piece)
        if move.pos_to is not None and move.pos_from != move.pos_to:
            # piece was moved to a different square, empty the square it was moved to and put the piece there
            self.piece_sprite_list.remove(self.pieces[move.pos_to[0]][move.pos_to[1]])
            self.pieces[move.pos_to[0]][move.pos_to[1]] = move.piece
        if move.captured_piece is not None and move.captured_piece.board_pos != move.pos_to:
            # piece was captured on a different square than the one the capturing piece moved to (e.g. en passant)
            # empty the square it was captured on (it was not emptied earlier because it was not the one moved to)
            self.piece_sprite_list.remove(move.captured_piece)
        if move.pos_from is not None and move.pos_from != move.pos_to:
            # existing piece was moved to a different square, create a blank piece on the square that was moved from
            self.pieces[move.pos_from[0]][move.pos_from[1]] = (
                NoPiece(self, pos=move.pos_from) if move.swapped_piece is None else move.swapped_piece
            )
            self.piece_sprite_list.append(self.pieces[move.pos_from[0]][move.pos_from[1]])
        if move.captured_piece is not None and (capture_pos := move.captured_piece.board_pos) != move.pos_to:
            # piece was captured on a different square than the one the capturing piece moved to (e.g. en passant)
            # create a blank piece on the square it was captured on
            self.pieces[capture_pos[0]][capture_pos[1]] = NoPiece(self, pos=capture_pos)
            self.piece_sprite_list.append(self.pieces[capture_pos[0]][capture_pos[1]])
        if move.piece is not None and move.pos_from is None:
            # piece was added to the board, update it and add it to the sprite list
            self.update_piece(move.piece)
            self.piece_sprite_list.append(move.piece)
        if move.piece is not None and move.piece.side in self.drops and not move.is_edit == 1:
            captured_piece = move.piece if move.pos_to is None else move.captured_piece
            if captured_piece is not None and move.piece.side in self.captured_pieces:
                capture_type = captured_piece.promoted_from or type(captured_piece)
                if capture_type in self.drops[move.piece.side]:
                    # droppable piece was captured, add it to the roster of captured pieces
                    self.captured_pieces[move.piece.side].append(capture_type)
        if (
            move.is_edit != 1 and move.movement_type and move.piece.movement
            and not issubclass(move.movement_type, (CloneMovement, DropMovement))
        ):
            # call movement.update() to update movement state after the move (e.g. pawn double move, castling rights)
            move.piece.movement.update(move, move.piece)
        if move.is_edit != 1:
            if not move.piece or isinstance(move.piece, NoPiece):
                # check if a piece can be dropped
                self.try_drop(move)
            else:
                # check if the piece needs to be promoted
                self.try_promotion(move)
        if not self.ply_simulation:
            # update markers for possible en passant captures
            self.update_en_passant_markers(move)
            # as well as for relay moves
            self.update_relay_markers(move)

    def auto(self, move: Move) -> None:
        self.update_auto_capture_markers(move, True)
        self.update_auto_captures(move, self.turn_side.opponent())
        chained_move = move
        while chained_move:
            self.move(chained_move)
            self.update_auto_capture_markers(chained_move)
            chained_move.set(piece=copy(chained_move.piece))
            if self.promotion_piece is None:
                self.log(f"Move: {chained_move}")
            chained_move = chained_move.chained_move
        if self.chain_start is None:
            self.chain_start = move
            self.move_history.append(deepcopy(self.chain_start))
        else:
            last_move = self.chain_start
            while last_move.chained_move:
                last_move = last_move.chained_move
            last_move.chained_move = move
        self.unload_end_data()
        self.load_pieces()
        if move.chained_move is Unset and not self.promotion_piece:
            self.load_moves()
            self.show_moves(False)
            self.draw(0)
            self.select_piece(move.pos_to)
            if self.auto_moves and self.board_config['fast_chain'] and not self.game_over:
                self.try_auto()
        else:
            self.chain_start = None
            if self.promotion_piece is None:
                self.shift_ply(+1)
                self.load_pieces()
                self.load_check()
                self.update_end_data(self.move_history[-1])
                self.load_moves()
                self.reload_end_data()
                self.compare_history()
            self.advance_turn()

    def try_auto(self) -> bool:
        moves = self.moves[self.turn_side]
        only_move = None
        for pos_from in moves:
            if isinstance(pos_from, str):
                if only_move is None:
                    only_move = pos_from
                    continue
                else:
                    only_move = False
                    break
            for pos_to in moves[pos_from]:
                for move in moves[pos_from][pos_to]:
                    if not move:
                        continue
                    if only_move is None:
                        only_move = move
                    elif isinstance(only_move, str):
                        only_move = False
                        break
                    elif not only_move.matches(move):
                        only_move = False
                        break
                if only_move is False:
                    break
            if only_move is False:
                break
        if isinstance(only_move, Move):
            self.auto(only_move)
            return True
        return False

    def undo(self, move: Move) -> None:
        if move.pos_from != move.pos_to or move.promotion is not None:
            # piece was added, moved, removed, or promoted
            if move.pos_from is not None:
                # existing piece was moved, empty the square it was moved from and restore its position
                self.set_position(move.piece, move.pos_from)
                self.piece_sprite_list.remove(self.pieces[move.pos_from[0]][move.pos_from[1]])
            if move.pos_to is not None and move.pos_from != move.pos_to:
                # piece was placed on a different square, empty that square
                self.piece_sprite_list.remove(self.pieces[move.pos_to[0]][move.pos_to[1]])
            if move.pos_to is None or move.promotion is not None:
                # existing piece was removed from the board (possibly promoted to a different piece type)
                if not self.is_trickster_mode():  # reset_trickster_mode() does not reset removed pieces
                    move.piece.angle = 0          # so instead we have to do it manually as a workaround
            if not isinstance(move.piece, NoPiece):
                # update the piece sprite to reflect current piece hiding mode
                self.update_piece(move.piece)
            if move.pos_from is not None:
                # existing piece was moved, restore it on the square it was moved from
                self.pieces[move.pos_from[0]][move.pos_from[1]] = move.piece
                self.piece_sprite_list.append(move.piece)
        if move.captured_piece is not None:
            # piece was captured, restore it on the square it was captured on
            capture_pos = move.captured_piece.board_pos
            if capture_pos != move.pos_to:
                # piece was captured on a different square than the one the capturing piece moved to (e.g. en passant)
                # empty the square it was captured on (it was not emptied earlier because it was not the one moved to)
                self.piece_sprite_list.remove(self.pieces[capture_pos[0]][capture_pos[1]])
            self.reset_position(move.captured_piece)
            if not self.is_trickster_mode():   # reset_trickster_mode() does not reset removed pieces
                move.captured_piece.angle = 0  # so instead we have to do it manually as a workaround
            self.update_piece(move.captured_piece)  # update the piece sprite to reflect current piece hiding mode
            self.pieces[capture_pos[0]][capture_pos[1]] = move.captured_piece
            self.piece_sprite_list.append(move.captured_piece)
        if move.piece is not None and move.piece.side in self.drops and move.is_edit != 1:
            captured_piece = move.piece if move.pos_to is None else move.captured_piece
            if captured_piece is not None and move.piece.side in self.captured_pieces:
                capture_type = captured_piece.promoted_from or type(captured_piece)
                if capture_type in self.drops[move.piece.side]:
                    # droppable piece was captured, remove it from the roster of captured pieces
                    for i, piece in enumerate(self.captured_pieces[move.piece.side][::-1]):
                        if piece == capture_type:
                            self.captured_pieces[move.piece.side].pop(-(i + 1))
                            break
        if move.pos_to is not None and move.pos_from != move.pos_to:
            # piece was added on or moved to a different square, restore the piece that was there before
            if move.captured_piece is None or move.captured_piece.board_pos != move.pos_to:
                # no piece was on the square that was moved to (e.g. non-capturing move, en passant)
                # create a blank piece on that square
                self.pieces[move.pos_to[0]][move.pos_to[1]] = NoPiece(self, pos=move.pos_to)
                self.piece_sprite_list.append(self.pieces[move.pos_to[0]][move.pos_to[1]])
            if move.swapped_piece is not None:
                # piece was swapped with another piece, move the swapped piece to the square that was moved to
                self.set_position(move.swapped_piece, move.pos_to)
                self.update_piece(move.swapped_piece)  # update the piece sprite to reflect current piece hiding mode
                self.pieces[move.pos_to[0]][move.pos_to[1]] = move.swapped_piece
                self.piece_sprite_list.append(move.swapped_piece)
        if (
            move.is_edit != 1 and move.movement_type and move.piece.movement
            and not issubclass(move.movement_type, (CloneMovement, DropMovement))
        ):
            # call movement.undo() to restore movement state before the move (e.g. pawn double move, castling rights)
            move.piece.movement.undo(move, move.piece)
        if not self.ply_simulation:
            # revert markers for relay moves
            self.revert_relay_markers(move)

    def undo_last_move(self) -> None:
        self.deselect_piece()
        if not self.move_history:
            return
        offset = False
        in_promotion = self.promotion_piece is not None
        if in_promotion:
            if self.move_history and self.future_move_history:
                past, future = self.move_history[-1], self.future_move_history[-1]
                while (
                    past and future and past.pos_from == future.pos_from and past.pos_to == future.pos_to
                    and not (past.captured_piece is not None and future.swapped_piece is not None)
                    and not (past.swapped_piece is not None and future.captured_piece is not None)
                ):
                    if future.promotion is not None:
                        past.promotion = future.promotion
                        if future.placed_piece is not None:
                            past.placed_piece = future.placed_piece
                    past, future = past.chained_move, future.chained_move
            self.end_promotion()
        else:
            last_move = self.move_history[-1]
            offset = last_move is None or (not last_move.is_edit and self.chain_start is None)
            if offset:
                self.revert_end_data(last_move)
                self.shift_ply(-1)
        last_move = self.move_history.pop()
        if last_move is not None:
            move_chain = [last_move]
            while move_chain[-1].chained_move:
                move_chain.append(move_chain[-1].chained_move)
            for chained_move in move_chain[::-1]:
                if (
                    chained_move.is_edit != 1
                    and chained_move.pos_from == chained_move.pos_to
                    and chained_move.promotion is None
                ):
                    chained_move.set(piece=self.get_piece(chained_move.pos_to))
                self.undo(chained_move)
                self.revert_auto_capture_markers(chained_move)
                if chained_move.promotion is not None:
                    if chained_move.placed_piece is not None:
                        turn_side = self.get_turn_side(+1)
                        if chained_move.placed_piece in self.drops[turn_side]:
                            self.captured_pieces[turn_side].append(chained_move.placed_piece)
                    if not isinstance(chained_move.piece, NoPiece):
                        self.update_piece(chained_move.piece)
                logged_move = copy(chained_move)
                if in_promotion:
                    logged_move.set(promotion=Unset)
                move_type = (
                    'Edit' if logged_move.is_edit
                    else 'Drop' if logged_move.movement_type == DropMovement
                    else 'Move'
                )
                self.log(f"Undo: {move_type}: {logged_move}")
                in_promotion = False
        else:
            log_pass = self.board_config['log_pass']
            if log_pass is None:
                log_pass = set(self.moves[self.turn_side]) != {'pass'}
            turn_side = self.get_turn_side(+1)
            if log_pass:
                self.log(f"Undo: Pass: {turn_side} to move")
        self.chain_start = None
        self.chain_moves = {side: {} for side in self.chain_moves}
        if self.move_history:
            move = self.move_history[-1]
            if move is not None and move.is_edit != 1 and move.movement_type != DropMovement:
                move.piece.movement.reload(move, move.piece)
        self.reload_en_passant_markers()
        future_move_history = self.future_move_history.copy()
        self.unload_end_data()
        self.load_pieces()
        self.load_check()
        self.load_moves()
        self.reload_end_data()
        self.advance_turn()
        self.future_move_history = future_move_history
        if self.future_move_history:
            copies = [
                copy(move).set(chained_move=Default) if move is not None else None
                for move in (self.future_move_history[-1], last_move)
            ]
            if (
                (copies[0] is None) or (copies[1] is None) or
                (copies[0] is not None and not copies[0].matches(copies[1]))
            ):
                if not offset:
                    self.clear_future_history(self.ply_count)
                self.future_move_history.append(last_move)
        else:
            self.future_move_history.append(last_move)

    def redo_last_move(self) -> None:
        self.deselect_piece()
        piece_was_moved = False
        if self.promotion_piece is not None:
            if self.move_history and self.future_move_history:
                past, future = self.move_history[-1], self.future_move_history[-1]
                while (
                    past and future and past.pos_from == future.pos_from and past.pos_to == future.pos_to
                    and not (past.captured_piece is not None and future.swapped_piece is not None)
                    and not (past.swapped_piece is not None and future.captured_piece is not None)
                ):
                    if future.promotion:
                        past.promotion = future.promotion
                        if future.placed_piece is not None:
                            past.placed_piece = future.placed_piece
                            for i, piece in enumerate(self.captured_pieces[self.turn_side][::-1]):
                                if piece == future.placed_piece:
                                    self.captured_pieces[self.turn_side].pop(-(i + 1))
                                    break
                        self.replace(self.promotion_piece, future.promotion)
                        self.update_promotion_auto_captures(self.move_history[-1])
                        self.end_promotion()
                        piece_was_moved = True
                        break
                    elif future.promotion is Unset:
                        return
                    past, future = past.chained_move, future.chained_move
            else:
                return
        if not self.future_move_history:
            return
        last_history_move = self.future_move_history[-1]
        last_move = last_history_move
        if self.chain_start:
            if not last_history_move:
                return
            last_chain_move = self.chain_start
            while last_chain_move:
                if last_history_move:
                    copies = [
                        copy(move).set(chained_move=Default) if move is not None else None
                        for move in (last_history_move, last_chain_move)
                    ]
                    if (
                        (copies[0] is None) != (copies[1] is None) or
                        (copies[0] is not None and not copies[0].matches(copies[1]))
                    ):
                        return
                    last_history_move = last_history_move.chained_move
                    last_chain_move = last_chain_move.chained_move
                else:
                    return
            if last_history_move:
                last_move = last_history_move
            else:
                return
        last_chain_move = last_move
        if self.future_move_history[-1] is None:
            log_pass = self.board_config['log_pass']
            if log_pass is None:
                log_pass = set(self.moves[self.turn_side]) != {'pass'}
            turn_side = self.get_turn_side(+1)
            if log_pass:
                self.log(f"Redo: Pass: {turn_side} to move")
            self.update_en_passant_markers()
            self.move_history.append(deepcopy(last_move))
        elif piece_was_moved:
            chained_move = last_move
            while chained_move:
                move_type = (
                    'Edit' if chained_move.is_edit
                    else 'Drop' if chained_move.movement_type == DropMovement
                    else 'Move'
                )
                self.log(f"Redo: {move_type}: {chained_move}")
                last_chain_move = chained_move
                chained_move = chained_move.chained_move
                if chained_move:
                    self.move(chained_move)
                    self.update_auto_capture_markers(chained_move)
                    chained_move.set(piece=copy(chained_move.piece))
        else:
            if last_move.pos_from is not None:
                self.update_move(last_move)
                self.update_auto_capture_markers(last_move, True)
                self.update_auto_captures(last_move, self.turn_side.opponent())
            chained_move = last_move
            while chained_move:
                self.move(chained_move)
                self.update_auto_capture_markers(chained_move)
                chained_move.set(piece=copy(chained_move.piece))
                move_type = (
                    'Edit' if chained_move.is_edit
                    else 'Drop' if chained_move.movement_type == DropMovement
                    else 'Move'
                )
                self.log(f"Redo: {move_type}: {chained_move}")
                self.apply_edit_promotion(chained_move)
                last_chain_move = chained_move
                chained_move = chained_move.chained_move
                if chained_move:
                    self.update_move(chained_move)
            if self.chain_start is None:
                self.chain_start = deepcopy(last_move)
                self.move_history.append(self.chain_start)
            else:
                last_history_move = self.chain_start
                while last_history_move.chained_move:
                    last_history_move = last_history_move.chained_move
                last_history_move.chained_move = deepcopy(last_move)
        # do not pop move from future history because compare_history() will do it for us
        chained_move = self.chain_start
        poss = []
        while chained_move:
            poss.extend((chained_move.pos_from, chained_move.pos_to))
            chained_move = chained_move.chained_move
        if (
            last_chain_move is None or last_chain_move.chained_move is None
            or not self.chain_moves.get(self.turn_side, {}).get(tuple(poss))
        ):
            self.chain_start = None
            self.unload_end_data()
            self.load_pieces()
            if self.promotion_piece is None:
                offset = last_move is None or not last_move.is_edit
                if offset:
                    self.shift_ply(+1)
                    self.load_check()
                    self.update_end_data(last_move)
                    self.load_moves()
                    self.reload_end_data()
                self.compare_history()
            self.advance_turn()
        elif last_chain_move.chained_move is Unset:
            last_history_move = self.chain_start
            current_pos = last_history_move.pos_to
            while last_history_move.chained_move:
                if last_history_move.pos_from == current_pos:
                    current_pos = last_history_move.pos_to
                last_history_move = last_history_move.chained_move
            if last_history_move.pos_from == current_pos:
                current_pos = last_history_move.pos_to
            self.load_pieces()
            self.load_moves()
            self.select_piece(current_pos)

    def undo_last_finished_move(self) -> None:
        self.auto_moves = False
        while self.move_history and self.move_history[-1] is None:
            self.undo_last_move()
        self.undo_last_move()
        self.auto_moves = True

    def redo_last_finished_move(self) -> None:
        self.auto_moves = False
        self.redo_last_move()
        while self.future_move_history and self.future_move_history[-1] is None:
            self.redo_last_move()
        self.auto_moves = True

    def pass_turn(self, side: Side | None = None) -> None:
        index = self.ply_count
        count = self.get_turn()
        start_count = count
        while self.turn_order[count][0] != side:
            index += 1
            if side is None:
                break
            count = self.get_turn(index)
            if count == start_count:
                return
        for _ in range(index - self.ply_count):
            log_pass = self.board_config['log_pass']
            if log_pass is None:
                log_pass = set(self.moves[self.turn_side]) != {'pass'}
            turn_side = self.get_turn_side(+1)
            if log_pass:
                self.log(f"Pass: {turn_side} to move")
            self.update_en_passant_markers()
            self.move_history.append(None)
            self.shift_ply(+1)
            self.unload_end_data()
            self.load_pieces()
            self.load_check()
            self.update_end_data()
            self.load_moves()
            self.reload_end_data()
            self.compare_history()
            self.advance_turn()

    def advance_turn(self) -> None:
        self.deselect_piece()
        # if we're promoting, we can't advance the turn yet
        if self.promotion_piece:
            self.update_caption()
            return
        self.skip_caption_update = False
        self.action_count += 1
        if self.board_config['autosave_act'] and self.action_count >= self.board_config['autosave_act']:
            self.action_count %= self.board_config['autosave_act']
            self.auto_save()
        elif (
            self.board_config['autosave_ply'] and self.ply_count and
            self.ply_count % self.board_config['autosave_ply'] == 0
        ):
            self.auto_save()
        if self.edit_mode:
            self.load_end_conditions()
            self.color_pieces()  # reverting the piece colors to normal in case they were changed
            self.update_caption()  # updating the caption to reflect the edit that was just made
            return  # let's not advance the turn while editing the board to hopefully make things easier for everyone
        self.update_status()
        self.draw(0)
        if self.auto_moves and self.board_config['fast_moves'] and not self.game_over:
            if self.try_auto():
                return
        if self.auto_moves and self.board_config['fast_turn_pass'] and not self.game_over:
            if 'pass' in self.moves[self.turn_side] and len(self.moves[self.turn_side]) == 1:
                self.pass_turn()
                return

    def get_status_string(self) -> str | None:
        if self.game_over:
            error = False
            string = ''
            if self.end_condition == 'checkmate':
                string += "Checkmate!"
            elif self.end_condition == 'stalemate':
                string += "Stalemate!"
            elif self.end_condition == 'check':
                if self.end_value == 1:
                    string += "Check!"
                else:
                    string += f"{spell(self.end_value, 10).capitalize()}-check!"
            elif self.end_condition == 'capture':
                if end_group := self.end_group.strip('*'):
                    string += f"{end_group} captured!"
                else:
                    string += "Piece captured!"
            elif self.end_condition in {k for d in self.area_groups.values() for k in d}:
                string += "Goal reached!"
            else:
                string += "Game over..?"  # this should never happen
                error = True
            if self.win_side:
                string += f" {self.win_side} wins."
            else:
                string += " It's a draw."
            if error:
                string += f' I think. (Unknown end condition: "{self.end_condition}")'
            return string
        elif self.check_side:
            return f"{self.check_side} is in check!"
        else:
            return

    def update_status(self) -> None:
        self.load_end_conditions()
        if self.game_over and self.win_side is not Side.NONE:
            losing_side = self.win_side.opponent()
            self.moves[losing_side] = {}
            self.moves_queried[losing_side] = True
        self.skip_caption_update = False
        self.show_moves()
        status_string = self.get_status_string()
        if status_string:
            self.log(f"Info: {status_string}")
        self.color_all_pieces()

    def update_caption(self) -> None:
        if self.skip_caption_update:
            return
        if self.board_config['status_string'] is None:
            return
        prefix = ''
        if self.board_config['status_prefix'] == 0:
            prefix = f"Ply {self.ply_count}"
        if self.board_config['status_prefix'] > 0:
            if self.turn_data[0] == 0:
                prefix = "Start"
            if self.turn_data[0] > 0:
                prefix = f"Turn {self.turn_data[0]}: {self.turn_data[1]}"
                if self.board_config['status_prefix'] > 1:
                    prefix += f", Move {self.turn_data[2]}"
                if self.board_config['status_prefix'] > 2:
                    prefix = f"(Ply {self.ply_count}) {prefix}"
        if not self.board_config['status_string']:
            if prefix:
                if self.board_config['status_prefix'] == 1 and self.turn_data[0] > 0:
                    self.set_caption(f"{prefix} to move")
                else:
                    self.set_caption(prefix)
            else:
                self.set_caption('Chess')
            return
        if prefix:
            prefix = f"[{prefix}]"
        selected_square = self.selected_square
        hovered_square = None
        if self.is_active:
            hovered_square = self.hovered_square or self.highlight_square
        if self.promotion_piece:
            piece = self.promotion_piece
            if isinstance(piece, NoPiece):
                if hovered_square in self.promotion_area:
                    promotion = self.promotion_area[hovered_square]
                    message = f"{promotion}"
                else:
                    message = f""
                    if self.edit_mode and self.edit_piece_set_id is not None:
                        if is_prefix_of('custom', self.edit_piece_set_id):
                            message += "Custom piece"
                        elif is_prefix_of('wall', self.edit_piece_set_id):
                            message += "Obstacle"
                        else:
                            message += f"Piece from {piece_groups[self.edit_piece_set_id]['name']}"
                    else:
                        message += "New piece"
                if not self.edit_mode or (self.move_history and ((m := self.move_history[-1]) and m.is_edit != 1)):
                    message += f" is placed on {toa(piece.board_pos)}"
                else:
                    message += f" appears on {toa(piece.board_pos)}"
                self.set_caption(f"{prefix} {message}")
                return
            message = f"{piece} on {toa(piece.board_pos)}"
            if not self.edit_mode or (self.move_history and ((m := self.move_history[-1]) and m.is_edit != 1)):
                message += " promotes"
            else:
                message += " is promoted"
            if hovered_square in self.promotion_area:
                promotion = self.promotion_area[hovered_square]
                if promotion.is_hidden:
                    message += " to ???"
                elif isinstance(promotion, Piece) and promotion.side not in {piece.side, Side.NONE}:
                    message += f" to {promotion}"
                else:
                    message += f" to {promotion.name}"
            elif self.edit_mode and self.edit_piece_set_id is not None:
                if is_prefix_of('custom', self.edit_piece_set_id):
                    message += " to a custom piece"
                elif is_prefix_of('wall', self.edit_piece_set_id):
                    message += " to an obstacle"
                else:
                    message += f" to {piece_groups[self.edit_piece_set_id]['name']}"
            self.set_caption(f"{prefix} {message}")
            return
        piece = self.get_piece(selected_square)
        if isinstance(piece, NoPiece):
            piece = None
        hide_piece = piece.is_hidden if piece else self.hide_pieces
        hide_move_markers = (
            self.edit_mode or self.hide_move_markers or
            (hide_piece and self.hide_move_markers is not False)
        )
        if selected_square:
            if hide_move_markers and hovered_square:
                move = Move(
                    pos_from=selected_square,
                    pos_to=hovered_square,
                    piece=piece,
                    is_edit=int(self.edit_mode),
                )
                self.set_caption(f"{prefix} {move}")
                return
            move = None
            if not hide_move_markers and hovered_square:
                move = self.find_move(selected_square, hovered_square)
            if move:
                move = deepcopy(move)
                if move.promotion is not None and type(move.piece) != type(move.promotion):
                    move.promotion = Unset
                chained_move = self.chain_start
                poss = []
                while chained_move:
                    poss.extend((chained_move.pos_from, chained_move.pos_to))
                    chained_move = chained_move.chained_move
                chained_move = move
                while chained_move and chained_move.chained_move and (
                    issubclass(chained_move.movement_type, CastlingMovement) or
                    isinstance(chained_move.piece.movement, AutoCaptureMovement) or
                    issubclass(chained_move.chained_move.movement_type, CloneMovement)
                ):
                    # let's also not show all auto-captures because space in the caption is VERY limited
                    if isinstance(chained_move.piece.movement, AutoCaptureMovement):
                        chained_move.chained_move = Unset
                        break
                    poss.extend((chained_move.pos_from, chained_move.pos_to))
                    chained_move = chained_move.chained_move
                if chained_move.chained_move is not Unset:
                    poss.extend((chained_move.pos_from, chained_move.pos_to))
                    if chained_move.chained_move or self.chain_moves.get(self.turn_side, {}).get(tuple(poss)):
                        chained_move.chained_move = Unset  # don't chain moves since we're only showing selectable moves
                moves = []
                while move:
                    moves.append(move)
                    move = move.chained_move
                self.set_caption(f"{prefix} {'; '.join(str(move) for move in moves)}")
                return
        if piece or hovered_square:
            if not piece:
                piece = self.get_piece(hovered_square)
            if not isinstance(piece, NoPiece) and (self.edit_mode or not isinstance(piece, Border)):
                self.set_caption(f"{prefix} {piece} on {toa(piece.board_pos)}")
                return
        if self.edit_mode:
            self.set_caption(f"{prefix} Editing board")
            return
        message = self.get_status_string()
        if message:
            self.set_caption(f"{prefix} {message}")
        elif self.board_config['status_prefix'] == 0 or self.turn_data[0] == 0:
            self.set_caption(f"{prefix} {self.turn_data[1]} to move")
        elif self.board_config['status_prefix'] == 1:
            self.set_caption(f"[{prefix[1:-1] or '???'} to move]")
        else:
            self.set_caption(prefix)

    def try_drop(self, move: Move) -> None:
        if move.promotion:
            if move.placed_piece is not None:
                for i, piece in enumerate(self.captured_pieces[self.turn_side][::-1]):
                    if piece == move.placed_piece:
                        self.captured_pieces[self.turn_side].pop(-(i + 1))
                        break
            promotion_piece = self.promotion_piece
            self.promotion_piece = True
            self.replace(move.piece, move.promotion)
            self.update_promotion_auto_captures(move)
            self.promotion_piece = promotion_piece
        else:
            if self.turn_side not in self.drops:
                return
            if not self.captured_pieces[self.turn_side]:
                return
            if not self.use_drops and not self.edit_mode:
                return
            valid_drops = self.moves[self.turn_side].get('drop', {}).get(move.piece.board_pos, set())
            if not valid_drops:
                return
            side_drops = self.drops[self.turn_side]
            drop_list = []
            drop_type_list = []
            drop_indexes = {k: i for i, k in enumerate(side_drops)}
            limits = self.piece_limits.get(self.turn_side, self.piece_limits)
            limit_groups = {}
            limit_hits = {}
            for piece_type in sorted(self.captured_pieces[self.turn_side], key=lambda x: drop_indexes.get(x, 0)):
                if piece_type not in side_drops:
                    continue
                if piece_type not in valid_drops:
                    continue
                drop_squares = side_drops[piece_type]
                if move.piece.board_pos not in drop_squares:
                    continue
                drops = []
                for drop in drop_squares[move.piece.board_pos]:
                    drop_type = type(drop) if isinstance(drop, Piece) else drop
                    if drop_type not in limit_hits:
                        if drop_type not in limit_groups:
                            limit_groups[drop_type] = {g for g in limits if self.fits(g, drop_type)}
                        limit_hits[drop_type] = False
                        for g in limit_groups[drop_type]:
                            if self.piece_counts[self.turn_side].get(g, 0) >= limits[g]:
                                limit_hits[drop_type] = True
                                break
                    if not limit_hits[drop_type]:
                        drops.append(drop)
                drop_list.extend(drops)
                drop_type_list.extend(piece_type for _ in drops)
            if not drop_list:
                return
            if self.auto_moves and self.board_config['fast_drop'] and len(drop_list) == 1:
                promotion_piece = self.promotion_piece
                self.promotion_piece = True
                drop = drop_list[0]
                if isinstance(drop, Piece):
                    drop = drop.of(drop.side or self.turn_side).on(move.pos_to)
                else:
                    drop = drop(board=self, pos=move.piece.board_pos, side=self.turn_side)
                move.set(promotion=drop, placed_piece=drop_type_list[0])
                for i, piece in enumerate(self.captured_pieces[self.turn_side][::-1]):
                    if piece == type(drop):
                        self.captured_pieces[self.turn_side].pop(-(i + 1))
                        break
                self.replace(move.piece, move.promotion)
                self.update_promotion_auto_captures(move)
                self.promotion_piece = promotion_piece
            else:
                self.start_promotion(self.get_piece(move.piece.board_pos), drop_list, drop_type_list)
                return
        if move.promotion:
            chained_move = move
            while chained_move:
                move_type = (
                    'Edit' if chained_move.is_edit
                    else 'Drop' if chained_move.movement_type == DropMovement
                    else 'Move'
                )
                self.log(f"{move_type}: {chained_move}")
                chained_move = chained_move.chained_move
                if chained_move:
                    self.move(chained_move)
                    self.update_auto_capture_markers(chained_move)
                    chained_move.set(piece=copy(chained_move.piece))
            self.update_en_passant_markers(move)
            self.move_history.append(deepcopy(move))
            self.unload_end_data()
            self.load_pieces()
            self.load_check()
            if not move.is_edit:
                self.shift_ply(+1)
                self.update_end_data(self.move_history[-1])
                self.load_moves()
                self.reload_end_data()
            self.compare_history()
            self.advance_turn()

    def try_promotion(self, move: Move) -> None:
        promotion_piece = self.promotion_piece
        if move.promotion:
            self.promotion_piece = True
            promoted_from = move.promotion.promoted_from or move.piece.promoted_from
            if not isinstance(move.piece, NoPiece):
                promoted_from = promoted_from or type(move.piece)
            if type(move.promotion) != promoted_from:
                move.promotion.promoted_from = promoted_from
            self.replace(move.piece, move.promotion)
            self.update_promotion_auto_captures(move)
            self.promotion_piece = promotion_piece
            return
        if is_active(move.chained_move):
            return
        if move.piece.side not in self.promotions:
            return
        side_promotions = self.promotions[move.piece.side]
        if type(move.piece) not in side_promotions:
            return
        limits = self.piece_limits.get(move.piece.side, self.piece_limits)
        limit_groups = {}
        limit_hits = {}
        promotion_squares = side_promotions[type(move.piece)]
        for square in (move.pos_to, move.pos_from):
            if square not in promotion_squares:
                continue
            promotions = []
            for promotion in promotion_squares[square]:
                promotion_type = type(promotion) if isinstance(promotion, Piece) else promotion
                if promotion_type not in limit_hits:
                    if promotion_type not in limit_groups:
                        limit_groups[promotion_type] = {g for g in limits if self.fits(g, promotion_type)}
                    limit_hits[promotion_type] = False
                    for g in limit_groups[promotion_type]:
                        if self.piece_counts[move.piece.side].get(g, 0) >= limits[g]:
                            limit_hits[promotion_type] = True
                            break
                if not limit_hits[promotion_type]:
                    promotions.append(promotion)
            if not promotions:
                return
            if self.auto_moves and self.board_config['fast_promotion'] and len(promotions) == 1:
                self.promotion_piece = True
                promotion = promotions[0]
                if isinstance(promotion, Piece):
                    promotion = promotion.of(promotion.side or move.piece.side).on(square)
                else:
                    promotion = promotion(board=self, pos=square, side=move.piece.side)
                promoted_from = promotion.promoted_from or move.piece.promoted_from
                if not isinstance(move.piece, NoPiece):
                    promoted_from = promoted_from or type(move.piece)
                if type(promotion) != promoted_from:
                    promotion.promoted_from = promoted_from
                move.set(promotion=promotion)
                self.replace(move.piece, move.promotion)
                self.update_promotion_auto_captures(move)
                self.promotion_piece = promotion_piece
                return
            self.start_promotion(move.piece, promotions)
            return

    def start_promotion(
        self, piece: Piece, promotions: list[Piece | type[Piece]], drops: list[type[Piece]] | None = None
    ) -> None:
        if drops is None:
            drops = {}
        self.hide_moves()
        self.promotion_piece = piece
        piece_pos = piece.board_pos
        direction = (Side.WHITE if piece_pos[0] < self.board_height / 2 else Side.BLACK).direction
        area = len(promotions)
        area_height = min(len(promotions), max(self.board_height // 2, 1 + isqrt(area - 1)))
        area_width = ceil(area / area_height)
        area_origin = piece_pos
        while self.not_on_board((area_origin[0] + direction(area_height - 1), area_origin[1])):
            area_origin = add(area_origin, direction((-1, 0)))
        area_origin = add(area_origin, direction((area_height - 1, 0)))
        area_squares = []
        col_increment = 0
        aim_left = area_origin[1] >= self.board_width / 2
        for col, row in product(range(area_width), range(area_height)):
            current_row = area_origin[0] + direction(-row)
            new_col = col + col_increment
            current_col = area_origin[1] + ((new_col + 1) // 2 * ((aim_left + new_col) % 2 * 2 - 1))
            while self.not_on_board((current_row, current_col)):
                col_increment += 1
                new_col = col + col_increment
                current_col = area_origin[1] + ((new_col + 1) // 2 * ((aim_left + new_col) % 2 * 2 - 1))
            area_squares.append((current_row, current_col))
        side = self.get_promotion_side(piece) if self.edit_mode and not drops else (piece.side or self.turn_side)
        for promotion, drop, pos in zip_longest(promotions, drops, area_squares):
            background_sprite = Sprite("assets/util/square.png")
            background_sprite.color = self.color_scheme['promotion_area_color']
            background_sprite.position = self.get_screen_position(pos)
            background_sprite.scale = self.square_size / background_sprite.texture.width
            self.promotion_area_sprite_list.append(background_sprite)
            if promotion is None:
                continue
            if isinstance(promotion, Piece):
                promotion_piece = promotion.of(promotion.side or side).on(pos)
                promotion = type(promotion)
            else:
                promotion_piece = promotion(board=self, pos=pos, side=side)
            if not self.edit_mode or (self.move_history and ((m := self.move_history[-1]) and m.is_edit != 1)):
                promoted_from = promotion_piece.promoted_from or piece.promoted_from
                if not isinstance(piece, NoPiece):
                    promoted_from = promoted_from or type(piece)
                if type(promotion_piece) != promoted_from:
                    promotion_piece.promoted_from = promoted_from
            if issubclass(promotion, Piece) and not issubclass(promotion, NoPiece):
                if issubclass(promotion, (King, CBKing)) and promotion not in self.piece_sets[side]:
                    self.update_piece(promotion_piece, asset_folder='other')
                elif self.edit_mode and self.edit_piece_set_id is not None and not isinstance(piece, Obstacle):
                    promotion_piece.should_hide = self.hide_edit_pieces
                    self.update_piece(promotion_piece, penultima_hide=False)
                else:
                    self.update_piece(promotion_piece, penultima_flip=True)
            promotion_piece.scale = self.square_size / promotion_piece.texture.width
            if isinstance(promotion_piece, (Border, Wall)):
                promotion_piece.scale *= 0.8
            if isinstance(promotion_piece, (Shield, Void)):
                promotion_piece.scale *= 0.8
            if isinstance(promotion_piece, (NoPiece, Obstacle)):
                promotion_piece.set_color(
                    self.color_scheme.get(
                        f"{promotion_piece.side.key()}piece_color",
                        self.color_scheme['piece_color']
                    ),
                    self.color_scheme['colored_pieces']
                )
            self.promotion_piece_sprite_list.append(promotion_piece)
            self.promotion_area[pos] = promotion_piece
            self.promotion_area_drops[pos] = drop
        self.skip_caption_update = False
        self.update_caption()

    def apply_edit_promotion(self, move: Move) -> None:
        if move.is_edit and move.movement_type != DropMovement and move.promotion is not None:
            if move.promotion is Unset:
                promotion_side = self.get_promotion_side(move.piece)
                if len(self.edit_promotions[promotion_side]):
                    self.start_promotion(move.piece, self.edit_promotions[promotion_side])
                    self.update_caption()
            else:
                self.promotion_piece = True
                self.replace(move.piece, move.promotion)
                self.update_promotion_auto_captures(move)
                self.promotion_piece = None

    def end_promotion(self) -> None:
        self.promotion_piece = None
        self.promotion_area = {}
        self.promotion_area_drops = {}
        self.promotion_area_sprite_list.clear()
        self.promotion_piece_sprite_list.clear()

    def replace(self, piece: Piece, new_piece: Piece) -> None:
        new_piece.board_pos = None
        new_piece = copy(new_piece)
        pos = piece.board_pos
        self.piece_sprite_list.remove(self.pieces[pos[0]][pos[1]])
        self.pieces[pos[0]][pos[1]] = new_piece
        self.set_position(new_piece, pos)
        self.update_piece(new_piece)
        if not isinstance(piece, (NoPiece, Obstacle)):
            new_piece.set_color(
                self.color_scheme.get(
                    f"{new_piece.side.key()}piece_color",
                    self.color_scheme['piece_color']
                ),
                self.color_scheme['colored_pieces']
            )
        new_piece.scale = self.square_size / new_piece.texture.width
        self.piece_sprite_list.append(new_piece)
        if type(new_piece) == self.past_custom_pieces.get(new_type := save_piece_type(type(new_piece))):
            self.custom_pieces[new_type] = self.past_custom_pieces[new_type]
            del self.past_custom_pieces[new_type]

    def color_pieces(self, side: Side = Side.ANY, color: tuple[int, int, int] | None = None) -> None:
        for piece in self.movable_pieces.get(side, sum(self.movable_pieces.values(), [])):
            piece.set_color(
                color if color is not None else
                self.color_scheme.get(
                    f"{piece.side.key()}piece_color",
                    self.color_scheme['piece_color']
                ),
                self.color_scheme['colored_pieces']
            )

    def color_all_pieces(self) -> None:
        if self.game_over:
            if self.win_side:
                self.color_pieces(
                    self.win_side,
                    self.color_scheme.get(
                        f"{self.win_side.key()}win_color",
                        self.color_scheme['win_color']
                    ),
                )
                self.color_pieces(
                    self.win_side.opponent(),
                    self.color_scheme.get(
                        f"{self.win_side.opponent().key()}loss_color",
                        self.color_scheme['loss_color']
                    ),
                )
            else:
                self.color_pieces(
                    Side.WHITE,
                    self.color_scheme.get(
                        f"{Side.WHITE.key()}draw_color",
                        self.color_scheme['draw_color']
                    ),
                )
                self.color_pieces(
                    Side.BLACK,
                    self.color_scheme.get(
                        f"{Side.BLACK.key()}draw_color",
                        self.color_scheme['draw_color']
                    ),
                )
        else:
            if self.check_side:
                self.color_pieces(
                    self.check_side,
                    self.color_scheme.get(
                        f"{self.check_side.key()}check_color",
                        self.color_scheme['check_color']
                    ),
                )
                self.color_pieces(self.check_side.opponent())
            else:
                self.color_pieces()

    def update_colors(self) -> None:
        if self.is_trickster_mode():
            self.color_scheme = copy(self.color_scheme)
            new_colors = (
                trickster_colors[self.trickster_color_index - 1],
                trickster_colors[self.trickster_color_index % len(trickster_colors)]
            )
            self.color_scheme['light_square_color'] = lighten(desaturate(new_colors[0], 0.11), 0.011)
            self.color_scheme['dark_square_color'] = lighten(desaturate(new_colors[1], 0.11), 0.011)
            self.color_scheme['background_color'] = darken(average(
                self.color_scheme['light_square_color'],
                self.color_scheme['dark_square_color']
            ), 0.11 / 2)
            self.color_scheme['promotion_area_color'] = darken(self.color_scheme['background_color'], 0.11)
            self.color_scheme['highlight_color'] = saturate(self.color_scheme['promotion_area_color'], 0.11 * 2) + (80,)
            self.color_scheme['selection_color'] = self.color_scheme['highlight_color'][:3] + (120,)
            self.color_scheme['text_color'] = darken(self.color_scheme['background_color'], 0.11 * 3)
            self.color_scheme['white_piece_color'] = saturate(darken(new_colors[0], 0.11), 0.11)
            self.color_scheme['black_piece_color'] = desaturate(darken(new_colors[1], 0.11), 0.11)
            self.color_scheme['white_check_color'] = desaturate(self.color_scheme['white_piece_color'], 0.11)
            self.color_scheme['black_check_color'] = desaturate(self.color_scheme['black_piece_color'], 0.11)
            self.color_scheme['white_win_color'] = darken(self.color_scheme['white_piece_color'], 0.11)
            self.color_scheme['black_win_color'] = darken(self.color_scheme['black_piece_color'], 0.11)
            self.color_scheme['white_draw_color'] = desaturate(self.color_scheme['white_piece_color'], 0.11 * 5)
            self.color_scheme['black_draw_color'] = desaturate(self.color_scheme['black_piece_color'], 0.11 * 5)
            self.color_scheme['loss_color'] = getrgb('#bbbbbb')
        self.background_color = self.color_scheme['background_color']
        for sprite in self.obstacles:
            sprite.color = self.color_scheme.get('wall_color', self.color_scheme['background_color'])
        for sprite in self.label_list:
            sprite.color = self.color_scheme['text_color']
        for sprite in self.board_sprite_list:
            position = self.get_board_position(sprite.position)
            sprite.color = self.color_scheme[f"{'light' if self.is_light_square(position) else 'dark'}_square_color"]
        for sprite in self.promotion_area_sprite_list:
            sprite.color = self.color_scheme['promotion_area_color']
        for sprite in self.promotion_piece_sprite_list:
            if isinstance(sprite, Piece):
                if isinstance(sprite, Obstacle):
                    sprite.color = self.color_scheme.get('wall_color', self.color_scheme['background_color'])
                elif not isinstance(sprite, NoPiece):
                    sprite.set_color(
                        self.color_scheme.get(
                            f"{sprite.side.key()}piece_color",
                            self.color_scheme['piece_color']
                        ),
                        self.color_scheme['colored_pieces']
                    )
        self.color_all_pieces()
        self.selection.color = self.color_scheme['selection_color'] if self.selection.alpha else (0, 0, 0, 0)
        self.highlight.color = self.color_scheme['highlight_color'] if self.highlight.alpha else (0, 0, 0, 0)
        self.show_moves()

    def update_piece(
        self,
        piece: Piece,
        asset_folder: str | None = None,
        file_name: str | None = None,
        penultima_flip: bool = None,
        penultima_hide: bool = None,
    ) -> None:
        if piece.side not in self.piece_set_ids:
            return
        if penultima_flip is None:
            set_id = self.piece_set_ids[piece.side]
            penultima_flip = (self.chaos_mode in {2, 4}) and (set_id is None or set_id < 0)
        penultima_pieces = self.penultima_pieces.get(piece.side, {})
        if asset_folder is None:
            if piece.should_hide is False:
                asset_folder = piece.asset_folder
            elif self.hide_pieces == 1:
                asset_folder = 'other'
            elif self.hide_pieces == 2 and type(piece) in penultima_pieces and penultima_hide is not False:
                asset_folder = 'other'
            else:
                asset_folder = piece.asset_folder
        if file_name is None:
            if piece.should_hide is False:
                file_name = piece.file_name
            elif self.hide_pieces == 1:
                file_name = 'ghost'
            elif self.hide_pieces == 2 and type(piece) in penultima_pieces and penultima_hide is not False:
                file_name = penultima_pieces[type(piece)]
            else:
                file_name = piece.file_name
        if penultima_hide is not None:
            is_hidden = penultima_hide
        else:
            is_hidden = bool(self.hide_pieces) or Default
        file_name, flip = (file_name[:-1], penultima_flip) if file_name[-1] == '|' else (file_name, False)
        piece.reload(is_hidden=is_hidden, asset_folder=asset_folder, file_name=file_name, flipped_horizontally=flip)
        piece.scale = self.square_size / piece.texture.width

    def update_pieces(self) -> None:
        for piece in sum(self.movable_pieces.values(), []):
            self.update_piece(piece)
        for piece in self.promotion_piece_sprite_list:
            if isinstance(piece, Piece) and not isinstance(piece, NoPiece):
                if isinstance(piece, (King, CBKing)) and type(piece) not in self.piece_sets[piece.side]:
                    self.update_piece(piece, asset_folder='other')
                elif self.edit_mode and self.edit_piece_set_id is not None and not isinstance(piece, Obstacle):
                    piece.should_hide = self.hide_edit_pieces
                    self.update_piece(piece, penultima_hide=False)
                else:
                    self.update_piece(piece, penultima_flip=True)

    def update_sprite(
        self,
        sprite: Sprite,
        from_size: float,
        from_origin: tuple[float, float],
        from_width: int,
        from_height: int,
        from_cols: list[int],
        from_rows: list[int],
        from_flip_mode: bool
    ) -> None:
        old_position = sprite.position
        sprite.scale = self.square_size / sprite.texture.width
        sprite.position = self.get_screen_position(self.get_board_position(
            old_position, from_size, from_origin, from_width, from_height, from_cols, from_rows, from_flip_mode
        ))

    def update_sprites(
        self,
        size: float,
        origin: tuple[float, float],
        width: int,
        height: int,
        border_cols: list[int],
        border_rows: list[int],
        flip_mode: bool
    ) -> None:
        args = size, origin, width, height, border_cols, border_rows, flip_mode
        selected_square = self.selected_square
        self.update_sprite(self.highlight, *args)
        self.update_sprite(self.selection, *args)
        if self.active_piece is not None:
            self.update_sprite(self.active_piece, *args)
        for sprite_list in (
            self.board_sprite_list,
            self.move_sprite_list,
            self.piece_sprite_list,
            self.promotion_area_sprite_list,
            self.promotion_piece_sprite_list,
        ):
            for sprite in sprite_list:
                self.update_sprite(sprite, *args)
        for label in self.label_list:
            position = label.position
            label.font_size = self.square_size / 2
            label.x, label.y = self.get_screen_position(self.get_board_position(position, *args))
        self.deselect_piece()
        self.select_piece(selected_square)
        if self.highlight_square:
            self.update_highlight(self.highlight_square)
            self.hovered_square = None
        else:
            self.update_highlight(self.get_board_position(self.highlight.position, *args))
        if self.skip_mouse_move == 2:
            self.skip_mouse_move = 1

    def flip_board(self) -> None:
        self.flip_mode = not self.flip_mode
        self.update_sprites(
            self.square_size, self.origin,
            self.visual_board_width, self.visual_board_height,
            self.border_cols, self.border_rows, not self.flip_mode
        )

    def is_trickster_mode(self) -> bool:
        return self.trickster_color_index != 0

    def update_trickster_mode(self) -> None:
        if not self.is_trickster_mode():
            self.trickster_color_delta = 0
            return  # trickster mode is disabled
        if self.trickster_color_delta > 1 / 11:
            self.trickster_color_delta %= 1 / 11  # ah yes, modulo assignment. derpy stepbrother of the walrus operator
            self.trickster_color_index = self.trickster_color_index % len(trickster_colors) + 1
            self.update_colors()
        for sprite_list in (self.piece_sprite_list, self.promotion_piece_sprite_list, [self.active_piece]):
            for sprite in sprite_list:
                if (
                    isinstance(sprite, Piece) and not isinstance(sprite, NoPiece)
                    and not (self.game_over and not self.edit_mode and sprite.side == self.check_side)
                ):
                    direction = 1 if self.is_light_square(sprite.board_pos) else -1
                    sprite.angle += self.trickster_angle_delta / 11 * 360 * direction
        self.trickster_angle_delta = 0

    def reset_trickster_mode(self) -> None:
        if self.is_trickster_mode():
            return  # trickster mode is enabled
        if self.color_index is None:
            self.color_index = 0
            while colors[self.color_index]['scheme_type'] != 'cherub':
                self.color_index += 1
                if self.color_index >= len(colors):
                    self.color_index = 0
                    break
        self.color_scheme = colors[self.color_index]
        self.update_colors()
        for sprite_list in (self.piece_sprite_list, self.promotion_piece_sprite_list, [self.active_piece]):
            for sprite in sprite_list:
                if isinstance(sprite, Piece) and not isinstance(sprite, Obstacle):
                    sprite.angle = 0

    def resize_board(
        self,
        width: int = 0,
        height: int = 0,
        border_cols: list[int] | None = None,
        border_rows: list[int] | None = None,
        update: bool = True,
    ) -> None:
        width, height = width or self.board_width, height or self.board_height
        border_cols = self.border_cols if border_cols is None else border_cols
        border_rows = self.border_rows if border_rows is None else border_rows
        visual_width, visual_height = width + len(border_cols), height + len(border_rows)
        if (
            self.game_loaded and self.board_width == width and self.board_height == height
            and self.border_cols == border_cols and self.border_rows == border_rows
        ):
            return

        old_highlight = self.get_board_position(self.highlight.position) if self.highlight_square else None
        self.board_width, self.board_height = width, height
        old_cols, old_rows = self.border_cols, self.border_rows
        self.border_cols, self.border_rows = sorted(border_cols), sorted(border_rows)
        while self.border_cols and self.border_cols[-1] >= self.board_width:
            self.border_cols.pop()
        while self.border_rows and self.border_rows[-1] >= self.board_height:
            self.border_rows.pop()
        old_width, old_height = self.visual_board_width, self.visual_board_height
        self.visual_board_width, self.visual_board_height = visual_width, visual_height
        old_board_size = old_width, old_height

        self.board_sprite_list.clear()
        self.label_list.clear()

        position_kwargs = {
            'width': old_width,
            'height': old_height,
            'border_cols': old_cols,
            'border_rows': old_rows,
        }

        label_kwargs = {
            'anchor_x': 'center',
            'anchor_y': 'center',
            'font_name': 'Courier New',
            'font_size': self.square_size / 2,
            'bold': True,
            'align': 'center',
            'color': self.color_scheme['text_color'],
        }

        for row in range(self.board_height):
            text = str(row + 1)
            width = round(self.square_size / 2 * len(text))
            poss = [
                self.get_screen_position((row, -1), **position_kwargs),
                self.get_screen_position((row, self.board_width), **position_kwargs),
            ]
            self.label_list.extend(Text(text, *pos, width=width, **label_kwargs) for pos in poss)

        for col in range(self.board_width):
            text = b26(col + 1)
            width = round(self.square_size / 2 * len(text))
            poss = [
                self.get_screen_position((-1, col), **position_kwargs),
                self.get_screen_position((self.board_height, col), **position_kwargs),
            ]
            self.label_list.extend(Text(text, *pos, width=width, **label_kwargs) for pos in poss)

        for row, col in product(range(self.board_height), range(self.board_width)):
            sprite = Sprite("assets/util/square.png")
            sprite.color = self.color_scheme[f"{'light' if self.is_light_square((row, col)) else 'dark'}_square_color"]
            sprite.position = self.get_screen_position((row, col), **position_kwargs)
            sprite.scale = self.square_size / sprite.texture.width
            self.board_sprite_list.append(sprite)

        self.reset_drops()
        self.reset_promotions()

        for row in range(len(self.pieces), self.board_height):
            self.pieces += [[]]
        for row in range(self.board_height, len(self.pieces)):
            for col in range(len(self.pieces[row])):
                self.piece_sprite_list.remove(self.pieces[row][col])
        self.pieces = self.pieces[:self.board_height]
        for row in range(self.board_height):
            for col in range(len(self.pieces[row]), self.board_width):
                self.pieces[row].append(NoPiece(self, pos=(row, col)))
                self.piece_sprite_list.append(self.pieces[row][col])
            for col in range(self.board_width, len(self.pieces[row])):
                self.piece_sprite_list.remove(self.pieces[row][col])
            self.pieces[row] = self.pieces[row][:self.board_width]

        if (
            self.game_loaded or self.board_width != default_board_width or self.board_height != default_board_height
            or self.visual_board_width != default_board_width or self.visual_board_height != default_board_height
        ):
            self.log(f"Info: Changed board size to {self.board_width}x{self.board_height}")
            self.update_sprites(
                self.square_size, self.origin,
                old_width, old_height,
                old_cols, old_rows,
                self.flip_mode
            )
            new_width, new_height = (
                self.width + self.square_size * (self.visual_board_width - old_width),
                self.height + self.square_size * (self.visual_board_height - old_height)
            )
            if self.fullscreen:
                visual_board_size = (self.visual_board_width, self.visual_board_height)
                square_size, origin = self.square_size, self.origin
                self.windowed_size = tuple(
                    self.windowed_size[i] + self.windowed_square_size * (visual_board_size[i] - old_board_size[i])
                    for i in range(2)
                )
                self.windowed_square_size = min(self.windowed_size[i] / (visual_board_size[i] + 2) for i in range(2))
                self.square_size = min(self.size[i] / (visual_board_size[i] + 2) for i in range(2))
                self.origin = self.width / 2, self.height / 2
                self.update_sprites(
                    square_size, origin,
                    self.visual_board_width,
                    self.visual_board_height,
                    self.border_cols,
                    self.border_rows,
                    self.flip_mode
                )
            else:
                self.resize(new_width, new_height)
            self.update_highlight(old_highlight)

        if update and self.game_loaded:
            self.unload_end_data()
            self.load_pieces()
            self.load_check()
            self.load_moves()
            self.reload_end_data()
            self.advance_turn()

    def resize(self, width: float, height: float) -> None:
        if self.fullscreen:
            return
        if width == self.width and height == self.height:
            return
        self.skip_mouse_move = 2
        old_width, old_height = self.width, self.height
        x, y = self.get_location()
        self.set_visible(False)
        self.set_size(round(max(width, min_width)), round(max(height, min_height)))
        square_size = min(self.width / (self.visual_board_width + 2), self.height / (self.visual_board_height + 2))
        self.log(f"Info: Resized to {self.width}x{self.height} (Size: {round(square_size, 5)}px)")
        self.set_location(x - (self.width - old_width) // 2, y - (self.height - old_height) // 2)
        if not self.fullscreen:
            self.windowed_size = self.width, self.height
            self.windowed_square_size = min(
                self.width / (self.visual_board_width + 2),
                self.height / (self.visual_board_height + 2)
            )
        self.set_visible(True)

    def toggle_fullscreen(self) -> None:
        if self.fullscreen:
            self.log("Info: Fullscreen disabled", False)
            self.set_fullscreen(False)
            if self.size != self.windowed_size:
                self.resize(*self.windowed_size)
            else:
                self.log(f"Info: Resized to {self.width}x{self.height}", False)
            return
        screens = get_screens()
        if len(screens) == 1:
            self.log("Info: Fullscreen enabled", False)
            self.set_fullscreen()
            self.log(f"Info: Resized to {self.width}x{self.height}", False)
            return
        pos, size = self.get_location(), self.get_size()
        pos_min, pos_max = pos, add(pos, size)  # a bit of an unconventional usage of add() here but sure i guess
        portions = []
        for screen in screens:
            screen_min, screen_max = (screen.x, screen.y), add((screen.x, screen.y), (screen.width, screen.height))
            portion = (
                max(0, min(screen_max[0], pos_max[0]) - max(screen_min[0], pos_min[0])) *
                max(0, min(screen_max[1], pos_max[1]) - max(screen_min[1], pos_min[1]))
            )
            portions.append(portion)
        screen = portions.index(max(portions))
        self.log(f"Info: Fullscreen enabled on screen {screen + 1}", False)
        self.set_fullscreen(screen=screens[screen])
        self.log(f"Info: Resized to {self.width}x{self.height}", False)

    def set_visible(self, visible: bool = True) -> None:
        if self.board_config['save_update_mode'] < 0 and self.load_data is None:
            visible = False
        super().set_visible(visible)

    def activate(self):
        self.is_active = True
        self.on_activate()

    def deactivate(self):
        self.is_active = False
        self.on_deactivate()

    def on_draw(self) -> None:
        self.update_trickster_mode()
        start_render()
        for label in self.label_list:
            label.draw()
        self.board_sprite_list.draw()
        if not self.promotion_area:
            self.highlight.draw()
            self.selection.draw()
        self.move_sprite_list.draw()
        self.piece_sprite_list.draw()
        self.type_sprite_list.draw()
        if self.active_piece:
            self.active_piece.draw()
        self.promotion_area_sprite_list.draw()
        if self.promotion_area:
            self.highlight.draw()
        self.promotion_piece_sprite_list.draw()

    def on_update(self, delta_time: float) -> None:
        if self.is_trickster_mode():
            self.trickster_color_delta += delta_time
            self.trickster_angle_delta += delta_time
        self.save_interval += delta_time
        if self.board_config['autosave_time'] and self.save_interval >= self.board_config['autosave_time']:
            self.save_interval %= self.board_config['autosave_time']
            self.auto_save()

    def on_resize(self, width: float, height: float) -> None:
        self.skip_mouse_move = 2
        super().on_resize(width, height)
        square_size, origin = self.square_size, self.origin
        self.square_size = min(
            self.width / (self.visual_board_width + 2),
            self.height / (self.visual_board_height + 2),
        )
        self.origin = self.width / 2, self.height / 2
        self.update_sprites(
            square_size, origin,
            self.visual_board_width,
            self.visual_board_height,
            self.border_cols,
            self.border_rows,
            self.flip_mode
        )

    def on_activate(self) -> None:
        if not self.is_active:
            return
        if self.highlight_square:
            self.update_highlight(self.highlight_square)
            self.hovered_square = None
        hovered_square = self.get_board_position(self.highlight.position) if self.is_focused else None
        if self.on_board(hovered_square):
            self.highlight.color = self.color_scheme['highlight_color']
            if not self.highlight_square:
                self.hovered_square = hovered_square
        self.show_moves()

    def on_deactivate(self) -> None:
        self.hovered_square = None
        self.clicked_square = None
        self.held_buttons = 0
        self.highlight.color = (0, 0, 0, 0)
        self.show_moves()

    def on_mouse_enter(self, x: int, y: int):
        self.is_focused = True
        highlight_square = self.highlight_square
        self.update_highlight(self.highlight_square or self.get_board_position((x, y)))
        if highlight_square:
            self.hovered_square = None
        self.show_moves()

    def on_mouse_leave(self, x: int, y: int):
        self.is_focused = False
        highlight_square = self.highlight_square
        self.update_highlight(self.highlight_square)
        if highlight_square:
            self.hovered_square = None
        self.show_moves()

    def on_mouse_press(self, x: int, y: int, buttons: int, modifiers: int) -> None:
        if not self.is_active:
            return
        self.piece_was_selected = False
        if buttons & MOUSE_BUTTON_LEFT:
            self.held_buttons = MOUSE_BUTTON_LEFT
            if self.game_over and not self.edit_mode:
                return
            pos = self.get_board_position((x, y))
            if self.promotion_piece:
                if pos in self.promotion_area:
                    chained_move = self.move_history[-1]
                    while chained_move.chained_move:
                        chained_move = chained_move.chained_move
                    if pos in self.promotion_area_drops and (drop := self.promotion_area_drops[pos]) is not None:
                        chained_move.set(placed_piece=drop)
                        for i, piece in enumerate(self.captured_pieces[self.turn_side][::-1]):
                            if piece == drop:
                                self.captured_pieces[self.turn_side].pop(-(i + 1))
                                break
                        self.update_en_passant_markers(chained_move)
                    chained_move.set(promotion=self.promotion_area[pos])
                    self.replace(self.promotion_piece, self.promotion_area[pos])
                    self.update_promotion_auto_captures(chained_move)
                    self.end_promotion()
                    current_move = chained_move
                    while chained_move:
                        move_type = (
                            'Edit' if chained_move.is_edit
                            else 'Drop' if chained_move.movement_type == DropMovement
                            else 'Move'
                        )
                        self.log(f"{move_type}: {chained_move}")
                        chained_move = chained_move.chained_move
                        if chained_move:
                            self.move(chained_move)
                            self.update_auto_capture_markers(chained_move)
                            chained_move.set(piece=copy(chained_move.piece))
                    self.load_pieces()
                    if not current_move.is_edit:
                        self.shift_ply(+1)
                        self.unload_end_data()
                        self.load_pieces()
                        self.load_check()
                        self.update_end_data(self.move_history[-1])
                        self.load_moves()
                        self.reload_end_data()
                    self.compare_history()
                    self.advance_turn()
                return
            if pos == self.selected_square:
                if self.find_move(pos, pos) is None and not self.can_pass():
                    self.deselect_piece()
                    return
            if self.selected_square is not None:
                if self.edit_mode:
                    self.square_was_clicked = True
                    self.clicked_square = pos
                    return
                if pos not in self.moves.get(self.turn_side, {}).get(self.selected_square, {}) and not self.can_pass():
                    self.deselect_piece()
            if (
                pos != self.selected_square
                and not self.not_a_piece(pos)
                and (self.turn_side == self.get_side(pos) or self.edit_mode)
            ):
                self.deselect_piece()  # just in case we had something previously selected
                self.select_piece(pos)
                self.piece_was_selected = True
            self.square_was_clicked = True
            self.clicked_square = pos
        if buttons & MOUSE_BUTTON_RIGHT:
            self.held_buttons = MOUSE_BUTTON_RIGHT
            pos = self.get_board_position((x, y))
            if self.not_on_board(pos):
                self.deselect_piece()
                if self.promotion_piece:
                    self.undo_last_finished_move()
                    self.update_caption()
                return
            self.square_was_clicked = True
            self.clicked_square = pos

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        if not self.held_buttons:
            if not self.skip_mouse_move:
                pos = self.get_board_position((x, y))
                self.update_highlight(pos)
                self.highlight_square = None
            elif self.skip_mouse_move == 1:
                self.skip_mouse_move = 0

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int) -> None:
        if not self.skip_mouse_move:
            pos = self.get_board_position((x, y))
            self.update_highlight(pos)
            self.highlight_square = None
            if self.is_active and buttons & self.held_buttons & MOUSE_BUTTON_LEFT and self.selected_square is not None:
                if self.edit_mode and modifiers & key.MOD_ACCEL:
                    self.reset_position(self.get_piece(self.selected_square))
                else:
                    sprite = self.get_piece(self.selected_square)
                    sprite.position = x, y
        elif self.skip_mouse_move == 1:
            self.skip_mouse_move = 0

    def on_mouse_release(self, x: int, y: int, buttons: int, modifiers: int) -> None:
        if not self.is_active:
            return
        held_buttons = buttons & self.held_buttons
        self.held_buttons = 0
        if self.edit_mode:
            pos = self.get_board_position((x, y))
            if self.not_on_board(pos):
                return
            next_selected_square = None
            move = Move(is_edit=1)
            if held_buttons & MOUSE_BUTTON_LEFT:
                if self.promotion_piece:
                    return
                if not self.selected_square:
                    return
                if pos == self.selected_square and not modifiers & key.MOD_ALT:
                    if not self.square_was_clicked:
                        self.deselect_piece()
                    self.reset_position(self.get_piece(pos))
                    return
                if modifiers & key.MOD_ALT:
                    if self.not_a_piece(pos):
                        self.deselect_piece()
                        return
                    move.set(pos_from=pos, pos_to=None, piece=self.get_piece(pos), is_edit=2)
                elif modifiers & key.MOD_ACCEL:
                    self.reset_position(self.get_piece(self.selected_square))
                    piece = copy(self.get_piece(self.selected_square))
                    piece.board_pos = None
                    move.set(pos_from=None, pos_to=pos, piece=piece)
                    if not self.not_a_piece(pos):
                        move.set(captured_piece=self.get_piece(pos))
                    if self.square_was_clicked:
                        next_selected_square = pos
                elif modifiers & key.MOD_SHIFT:
                    move.set(
                        pos_from=self.selected_square, pos_to=pos,
                        piece=self.get_piece(self.selected_square)
                    )
                    if not self.not_a_piece(pos):
                        move.set(swapped_piece=self.get_piece(pos))
                else:
                    move.set(
                        pos_from=self.selected_square, pos_to=pos,
                        piece=self.get_piece(self.selected_square)
                    )
                    if not self.not_a_piece(pos):
                        move.set(captured_piece=self.get_piece(pos))
            elif held_buttons & MOUSE_BUTTON_RIGHT:
                self.deselect_piece()
                if self.promotion_piece:
                    self.undo_last_finished_move()
                    self.update_caption()
                if modifiers & key.MOD_ALT:
                    move.set(pos_from=pos, pos_to=pos, piece=self.get_piece(pos), is_edit=2)
                    if isinstance(move.piece, NoPiece):
                        move.set(pos_from=None, movement_type=DropMovement, promotion=Unset)
                    else:
                        side = self.get_promotion_side(move.piece)
                        if (
                            self.auto_moves and self.board_config['fast_promotion']
                            and len(self.edit_promotions[side]) == 1
                        ):
                            piece = self.edit_promotions[side][0]
                            if isinstance(piece, Piece):
                                piece = piece.of(piece.side or side).on(pos)
                            else:
                                piece = piece(board=self, pos=move.pos_to, side=side)
                            promoted_from = piece.promoted_from or move.piece.promoted_from
                            if not isinstance(move.piece, NoPiece):
                                promoted_from = promoted_from or type(move.piece)
                            if type(piece) != promoted_from:
                                piece.promoted_from = promoted_from
                            move.set(promotion=piece)
                        elif len(self.edit_promotions[side]) > 1:
                            move.set(promotion=Unset)
                elif modifiers & key.MOD_ACCEL:
                    if self.not_a_piece(pos):
                        self.deselect_piece()
                        return
                    move.set(pos_from=pos, pos_to=pos, piece=self.get_piece(pos), is_edit=2)
                elif modifiers & key.MOD_SHIFT:
                    move.set(pos_from=pos, pos_to=pos, piece=self.get_piece(pos))
                    if isinstance(move.piece, NoPiece):
                        move.set(pos_from=None)
                    side = self.get_promotion_side(move.piece)
                    if self.auto_moves and self.board_config['fast_promotion'] and len(self.edit_promotions[side]) == 1:
                        piece = self.edit_promotions[side][0]
                        if isinstance(piece, Piece):
                            piece = piece.of(piece.side or side).on(pos)
                        else:
                            piece = piece(board=self, pos=move.pos_to, side=side)
                        move.set(promotion=piece)
                    elif len(self.edit_promotions[side]) > 1:
                        move.set(promotion=Unset)
                else:
                    if self.not_a_piece(pos):
                        self.deselect_piece()
                        return
                    move.set(pos_from=pos, pos_to=None, piece=self.get_piece(pos))
            else:
                return
            self.move(move)
            if move.promotion is Unset and move.movement_type == DropMovement and not self.promotion_piece:
                return
            self.update_auto_capture_markers(move)
            self.move_history.append(deepcopy(move))
            self.apply_edit_promotion(move)
            if not self.promotion_piece:
                self.log(f"Edit: {self.move_history[-1]}")
                self.compare_history()
            self.unload_end_data()
            self.load_pieces()
            self.load_check()
            self.load_moves()
            self.reload_end_data()
            self.advance_turn()
            if next_selected_square:
                self.select_piece(next_selected_square)
            return
        if held_buttons & MOUSE_BUTTON_RIGHT:
            self.deselect_piece()
            if self.promotion_piece:
                self.undo_last_finished_move()
                self.update_caption()
                if not modifiers & key.MOD_SHIFT:
                    return
            if not self.drops:
                return
            if self.game_over:
                return
            pos = self.get_board_position((x, y))
            if not self.not_on_board(pos) and isinstance((piece := self.get_piece(pos)), NoPiece):
                move = Move(pos_from=pos, pos_to=pos, movement_type=DropMovement, piece=piece, promotion=Unset)
                self.try_drop(move)
                if self.promotion_piece:
                    self.move_history.append(move)
                    self.update_caption()
        if held_buttons & MOUSE_BUTTON_LEFT:
            if self.game_over:
                self.deselect_piece()
                return
            if self.promotion_piece:
                return
            if self.nothing_selected():
                return
            pos = self.get_board_position((x, y))
            if self.selected_square is not None and (pos != self.selected_square or not self.piece_was_selected):
                move = self.find_move(self.selected_square, pos)
                if move is None:
                    if pos == self.selected_square and self.can_pass():
                        self.pass_turn()
                        return
                    else:
                        self.deselect_piece()
                        return
                self.update_move(move)
                if move.promotion is not None:
                    move.promotion = Unset  # do not auto-promote because we are selecting promotion type manually
                chained_move = self.chain_start
                poss = []
                while chained_move:
                    poss.extend((chained_move.pos_from, chained_move.pos_to))
                    chained_move = chained_move.chained_move
                chained_move = move
                while chained_move and chained_move.chained_move and (
                    issubclass(chained_move.movement_type, CastlingMovement) or
                    isinstance(chained_move.piece.movement, AutoCaptureMovement) or
                    issubclass(chained_move.chained_move.movement_type, CloneMovement)
                ):
                    poss.extend((chained_move.pos_from, chained_move.pos_to))
                    chained_move = chained_move.chained_move
                poss.extend((chained_move.pos_from, chained_move.pos_to))
                if chained_move.chained_move or self.chain_moves.get(self.turn_side, {}).get(tuple(poss)):
                    chained_move.chained_move = Unset  # do not chain moves since we are selecting chained move manually
                    is_final = False
                else:
                    is_final = True
                self.update_auto_capture_markers(move, True)
                self.update_auto_captures(move, self.turn_side.opponent())
                chained_move = move
                while chained_move:
                    self.move(chained_move)
                    chained_move.set(piece=copy(chained_move.piece))
                    if self.promotion_piece is None:
                        self.log(f"Move: {chained_move}")
                    chained_move = chained_move.chained_move
                    if chained_move:
                        self.update_auto_capture_markers(chained_move)
                if self.chain_start is None:
                    self.chain_start = deepcopy(move)
                    self.move_history.append(self.chain_start)
                else:
                    last_move = self.chain_start
                    while last_move.chained_move:
                        last_move = last_move.chained_move
                    last_move.chained_move = deepcopy(move)
                self.unload_end_data()
                self.load_pieces()
                if not is_final and not self.promotion_piece:
                    self.load_moves()
                    self.show_moves(False)
                    self.draw(0)
                    self.select_piece(move.pos_to)
                    if self.auto_moves and self.board_config['fast_chain'] and not self.game_over:
                        self.try_auto()
                else:
                    self.chain_start = None
                    if self.promotion_piece is None:
                        self.shift_ply(+1)
                        self.load_check()
                        self.update_end_data(self.move_history[-1])
                        self.load_moves()
                        self.reload_end_data()
                        self.compare_history()
                    self.advance_turn()
            else:
                self.reset_position(self.get_piece(self.selected_square))
                if not self.square_was_clicked:
                    self.deselect_piece()

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if not self.is_active:
            return
        partial_move = self.chain_start or self.promotion_piece
        if self.edit_mode and modifiers & key.MOD_ACCEL:
            if self.held_buttons & MOUSE_BUTTON_LEFT and self.selected_square is not None:
                self.reset_position(self.get_piece(self.selected_square))
        if symbol == key.ESCAPE:  # Quit
            self.close()
        if symbol == key.ENTER:  # Simulate LMB
            self.on_mouse_press(
                round(self.highlight.center_x), round(self.highlight.center_y), MOUSE_BUTTON_LEFT, modifiers
            )
            self.hovered_square = None
        if symbol == key.BACKSPACE:  # Simulate RMB
            self.on_mouse_press(
                round(self.highlight.center_x), round(self.highlight.center_y), MOUSE_BUTTON_RIGHT, modifiers
            )
            self.hovered_square = None
        if symbol in (key.UP, key.DOWN, key.LEFT, key.RIGHT):  # Move highlight
            start_row, start_col = self.get_board_position(self.highlight.position)
            row, col = start_row, start_col
            start_row = max(0, min(self.board_height - 1, start_row))
            start_col = max(0, min(self.board_width - 1, start_col))
            use_shift = (row == start_row) and (col == start_col)
            row_shift = {key.DOWN: -1, key.UP: 1}.get(symbol, 0) * (-1 if self.flip_mode else 1)
            col_shift = {key.LEFT: -1, key.RIGHT: 1}.get(symbol, 0) * (-1 if self.flip_mode else 1)
            row = {(0, -1): self.board_height - 1, (self.board_height - 1, 1): 0}.get((row, row_shift), row + row_shift)
            col = {(0, -1): self.board_width - 1, (self.board_width - 1, 1): 0}.get((col, col_shift), col + col_shift)
            row = max(0, min(self.board_height - 1, row if use_shift else start_row))
            col = max(0, min(self.board_width - 1, col if use_shift else start_col))
            self.update_highlight((row, col))
            self.highlight_square = (row, col)
            self.hovered_square = None
        if symbol == key.TAB:  # Next piece
            start_row, start_col = self.get_board_position(self.highlight.position)
            side = self.turn_side.opponent() if modifiers & key.MOD_ACCEL else self.turn_side
            direction = -1 if (modifiers & key.MOD_SHIFT) == (side == Side.WHITE) else 1
            if not self.selected_square:
                positions = {piece.board_pos for piece in self.movable_pieces[side]}
            elif not self.edit_mode:
                positions = self.moves.get(self.turn_side, {}).get(self.selected_square, {})
            else:
                positions = set(product(range(self.board_height), range(self.board_width)))
            if not positions:
                return
            if self.not_on_board((start_row, start_col)):
                start_row, start_col = (0, 0) if direction == 1 else (self.board_height - 1, self.board_width - 1)
            for row, col in product(range(self.board_height), range(self.board_width)):
                if not self.highlight.alpha or row or col:
                    current_col = (start_col + col * direction) % self.board_width
                    row_shift = int(current_col < start_col) if direction == 1 else -int(current_col > start_col)
                    current_row = (start_row + row * direction + row_shift) % self.board_height
                    if (current_row, current_col) in positions:
                        self.update_highlight((current_row, current_col))
                        self.highlight_square = (row, col)
                        self.hovered_square = None
                        return
        if self.held_buttons:
            return
        if symbol == key.S:  # Save data
            if modifiers & key.MOD_ALT:  # Save custom layout
                self.custom_layout = {}
                for pieces in [*self.movable_pieces.values(), self.obstacles]:
                    for piece in pieces:
                        self.custom_layout[piece.board_pos] = copy(piece)
                self.log("Info: Custom layout saved")
            elif modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:  # Save
                save_path = get_filename('save', 'json')
                self.save(save_path)
            elif modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Save as
                self.deactivate()
                self.draw(0)
                self.log("Info: Selecting a file to save to", False)
                save_path = select_save_name()
                if save_path:
                    self.save(save_path)
                else:
                    self.log("Info: Save cancelled", False)
                self.activate()
        if symbol == key.R:  # Restart
            if modifiers & key.MOD_ALT and modifiers & key.MOD_ACCEL:  # Reset custom data
                self.log("Info: Clearing custom data")
                self.reset_custom_data()
                self.log("Info: Starting new game", bool(self.hide_pieces))
                self.reset_board()
            elif modifiers & key.MOD_ALT:  # Reload save data
                data = self.save_data if modifiers & key.MOD_SHIFT else self.load_data
                if data is not None:
                    whence = 'saved to' if modifiers & key.MOD_SHIFT else 'loaded from'
                    path = self.save_path if modifiers & key.MOD_SHIFT else self.load_path
                    state = '' if isfile(path) else '(deleted) '
                    self.log(f"Info: Reloading data {whence} {state}{path}")
                    self.load_board(data)
            elif modifiers & key.MOD_SHIFT:  # Randomize piece sets
                blocked_ids = set(self.board_config['block_ids'])
                set_id_list = list(i for i in range(len(piece_groups)) if i not in blocked_ids)
                if modifiers & key.MOD_ACCEL:  # Randomize piece sets (same for both sides)
                    self.log(
                        "Info: Starting new game (with a random piece set)",
                        bool(self.hide_pieces)
                    )
                    chosen_id = self.set_rng.sample(set_id_list, k=1)[0]
                    self.piece_set_ids = {side: chosen_id for side in self.piece_set_ids}
                else:  # Randomize piece sets (different for each side)
                    self.log(
                        "Info: Starting new game (with random piece sets)",
                        bool(self.hide_pieces)
                    )
                    chosen_ids = self.set_rng.sample(set_id_list, k=len(self.piece_set_ids))
                    self.piece_set_ids = {side: set_id for side, set_id in zip(self.piece_set_ids, chosen_ids)}
                self.chaos_mode = 0
                self.reset_custom_data()
                self.reset_board()
            elif modifiers & key.MOD_ACCEL:  # Restart with the same piece sets
                self.log("Info: Starting new game", bool(self.hide_pieces))
                self.reset_board(update=None)  # Clear redoing if and only if no moves were made yet, i.e. double Ctrl+R
        if symbol == key.C:
            if modifiers & (key.MOD_SHIFT | key.MOD_ALT):  # Chaos mode
                self.load_chaos_sets(1 + bool(modifiers & key.MOD_ALT), modifiers & key.MOD_ACCEL)
            elif modifiers & key.MOD_ACCEL:  # Config
                self.save_config()
                self.log("Info: Configuration saved", False)
        if symbol == key.X:
            if modifiers & (key.MOD_SHIFT | key.MOD_ALT):  # Extreme chaos mode
                self.load_chaos_sets(3 + bool(modifiers & key.MOD_ALT), modifiers & key.MOD_ACCEL)
            elif modifiers & key.MOD_ACCEL and not partial_move:  # Extra roll (update probabilistic pieces)
                if self.selected_square:  # Only update selected piece (if it is probabilistic)
                    piece = self.get_piece(self.selected_square)
                    if isinstance(piece.movement, ProbabilisticMovement):
                        del self.roll_history[self.ply_count - 1][piece.board_pos]
                        self.probabilistic_piece_history[self.ply_count - 1].discard((piece.board_pos, type(piece)))
                        self.log(f"Info: Probabilistic piece on {toa(piece.board_pos)} updated")
                        self.reload_end_data()
                        self.advance_turn()
                else:  # Update all probabilistic pieces
                    self.clear_future_history(self.ply_count - 1)
                    self.log("Info: Probabilistic pieces updated")
                    self.reload_end_data()
                    self.advance_turn()
        if symbol == key.BRACKETLEFT and modifiers & key.MOD_ACCEL and not partial_move:  # Decrease board size
            width = self.board_width - (0 if modifiers & key.MOD_ALT else 1)
            height = self.board_height - (1 if modifiers & key.MOD_ALT else 0)
            self.resize_board(width, height)
        if symbol == key.BRACKETRIGHT and modifiers & key.MOD_ACCEL and not partial_move:  # Increase board size
            width = self.board_width + (0 if modifiers & key.MOD_ALT else 1)
            height = self.board_height + (1 if modifiers & key.MOD_ALT else 0)
            self.resize_board(width, height)
        if symbol == key.APOSTROPHE and modifiers & key.MOD_ACCEL and not partial_move:  # Add border row/column
            border_cols = self.border_cols + ([] if modifiers & key.MOD_ALT else [self.board_width])
            border_rows = self.border_rows + ([self.board_height] if modifiers & key.MOD_ALT else [])
            width = self.board_width + (0 if modifiers & key.MOD_ALT else 1)
            height = self.board_height + (1 if modifiers & key.MOD_ALT else 0)
            self.resize_board(width, height, border_cols, border_rows)
        if symbol == key.BACKSLASH and modifiers & key.MOD_ACCEL and not partial_move:
            if modifiers & key.MOD_ALT:  # Invert board size
                self.resize_board(self.board_height, self.board_width, self.border_rows, self.border_cols)
            else:  # Reset board size
                self.resize_board(default_board_width, default_board_height, [], [])
        if symbol == key.F11:  # Full screen (toggle)
            self.toggle_fullscreen()
        if symbol == key.MINUS and not self.fullscreen:  # (-) Decrease window size
            if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:
                self.resize(
                    (self.visual_board_width + 2) * min_size,
                    (self.visual_board_height + 2) * min_size
                )
            elif modifiers & key.MOD_ACCEL:
                width, height = self.get_size()
                self.resize(
                    width - (self.visual_board_width + 2) * size_step,
                    height - (self.visual_board_height + 2) * size_step
                )
            elif modifiers & key.MOD_SHIFT:
                width, height = self.get_size()
                size = min(
                    round(width / (self.visual_board_width + 2)),
                    round(height / (self.visual_board_height + 2))
                )
                self.resize(
                    (self.visual_board_width + 2) * size,
                    (self.visual_board_height + 2) * size
                )
        if symbol == key.EQUAL and not self.fullscreen:  # (+) Increase window size
            if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:
                self.resize(
                    (self.visual_board_width + 2) * max_size,
                    (self.visual_board_height + 2) * max_size
                )
            elif modifiers & key.MOD_ACCEL:
                width, height = self.get_size()
                self.resize(
                    width + (self.visual_board_width + 2) * size_step,
                    height + (self.visual_board_height + 2) * size_step
                )
            elif modifiers & key.MOD_SHIFT:
                width, height = self.get_size()
                size = max(
                    round(width / (self.visual_board_width + 2)),
                    round(height / (self.visual_board_height + 2))
                )
                self.resize(
                    (self.visual_board_width + 2) * size,
                    (self.visual_board_height + 2) * size
                )
        if symbol == key.KEY_0 and modifiers & key.MOD_ACCEL:  # Reset window size
            self.set_fullscreen(False)
            self.resize(
                (self.visual_board_width + 2) * default_size,
                (self.visual_board_height + 2) * default_size
            )
        if symbol == key.E:
            if modifiers & key.MOD_ALT:  # Everything
                self.save_config()
                self.log("Info: Configuration saved", False)
                self.save_log()
                self.log("Info: Log file saved", False)
                self.log("Info: Saving debug information", False)
                debug_log_data = debug_info(self)
                self.save_log(debug_log_data, 'debug')
                self.log("Info: Debug information saved", False)
                save_path = get_filename('save', 'json')
                self.save(save_path)
                if modifiers & key.MOD_ACCEL:
                    self.save_log(self.verbose_data, 'verbose')
                    self.log("Info: Verbose log file saved", False)
                if modifiers & key.MOD_SHIFT:
                    self.log("Info: Saving debug listings", False)
                    save_piece_data(self)
                    save_piece_sets()
                    save_piece_types()
                    self.log("Info: Debug listings saved", False)
            else:
                if modifiers & key.MOD_SHIFT:  # Empty board
                    self.empty_board()
                if modifiers & key.MOD_ACCEL and not partial_move:  # Edit mode (toggle)
                    self.edit_mode = not self.edit_mode
                    self.log(f"Mode: {'EDIT' if self.edit_mode else 'PLAY'}", False)
                    self.deselect_piece()
                    self.unload_end_data()
                    self.load_pieces()
                    self.load_check()
                    self.load_moves()
                    self.hide_moves()
                    self.reload_end_data()
                    self.advance_turn()
        if symbol == key.W:  # White
            if modifiers & key.MOD_ALT:  # Reset white set to default
                self.piece_set_ids[Side.WHITE] = 0
                set_name_suffix = ''
                if not self.hide_pieces:
                    set_name = piece_groups[self.piece_set_ids[Side.WHITE]].get('name')
                    set_name_suffix = f" ({set_name})"
                self.log(
                    f"Info: Using default piece set for White{set_name_suffix}",
                    bool(self.hide_pieces)
                )
                self.reset_custom_data()
                self.reset_board()
            elif modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT and not partial_move:  # White moves
                self.pass_turn(Side.WHITE)
            elif modifiers & key.MOD_SHIFT:  # Shift white piece set
                d = -1 if modifiers & key.MOD_ACCEL else 1
                self.piece_set_ids[Side.WHITE] = (
                    (self.piece_set_ids[Side.WHITE] + len(self.chaos_sets) + d)
                    % (len(piece_groups) + len(self.chaos_sets))
                    - len(self.chaos_sets)
                ) if self.piece_set_ids[Side.WHITE] is not None else 0
                which = {-1: 'previous', 1: 'next'}[d]
                set_name_suffix = ''
                if not self.hide_pieces:
                    if self.piece_set_ids[Side.WHITE] < 0:
                        set_name = get_set_name(self.chaos_sets[-self.piece_set_ids[Side.WHITE]])
                    else:
                        set_name = piece_groups[self.piece_set_ids[Side.WHITE]].get('name')
                    set_name_suffix = f" ({set_name})"
                self.log(
                    f"Info: Using {which} piece set for White{set_name_suffix}",
                    bool(self.hide_pieces)
                )
                self.reset_custom_data()
                self.reset_board()
        if symbol == key.B:  # Black
            if modifiers & key.MOD_ALT:  # Reset black set to default
                self.piece_set_ids[Side.BLACK] = 0
                set_name_suffix = ''
                if not self.hide_pieces:
                    set_name = piece_groups[self.piece_set_ids[Side.BLACK]].get('name')
                    set_name_suffix = f" ({set_name})"
                self.log(
                    f"Info: Using default piece set for Black{set_name_suffix}",
                    bool(self.hide_pieces)
                )
                self.reset_custom_data()
                self.reset_board()
            elif modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT and not partial_move:  # Black moves
                self.pass_turn(Side.BLACK)
            elif modifiers & key.MOD_SHIFT:  # Shift black piece set
                d = -1 if modifiers & key.MOD_ACCEL else 1
                self.piece_set_ids[Side.BLACK] = (
                    (self.piece_set_ids[Side.BLACK] + len(self.chaos_sets) + d)
                    % (len(piece_groups) + len(self.chaos_sets))
                    - len(self.chaos_sets)
                ) if self.piece_set_ids[Side.BLACK] is not None else 0
                which = {-1: 'previous', 1: 'next'}[d]
                set_name_suffix = ''
                if not self.hide_pieces:
                    if self.piece_set_ids[Side.BLACK] < 0:
                        set_name = get_set_name(self.chaos_sets[-self.piece_set_ids[Side.BLACK]])
                    else:
                        set_name = piece_groups[self.piece_set_ids[Side.BLACK]].get('name')
                    set_name_suffix = f" ({set_name})"
                self.log(
                    f"Info: Using {which} piece set for Black{set_name_suffix}",
                    bool(self.hide_pieces)
                )
                self.reset_custom_data()
                self.reset_board()
        if symbol == key.N:  # Next
            if modifiers & key.MOD_ALT:  # Reset white and black sets to default
                self.chaos_mode = 0
                self.piece_set_ids = {side: 0 for side in self.piece_set_ids}
                set_name_suffix = ''
                if not self.hide_pieces:
                    set_name = piece_groups[self.piece_set_ids[Side.WHITE]].get('name')
                    set_name_suffix = f" ({set_name})"
                self.log(
                    f"Info: Using default piece set{set_name_suffix}",
                    bool(self.hide_pieces)
                )
                self.reset_custom_data()
                self.reset_board()
            elif modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT and not partial_move:  # Next player
                self.pass_turn()
            elif modifiers & key.MOD_SHIFT:
                if (
                    self.piece_set_ids[Side.WHITE] == self.piece_set_ids[Side.BLACK]
                    and None not in self.piece_set_ids.values()
                ):  # Next piece set
                    d = -1 if modifiers & key.MOD_ACCEL else 1
                    self.piece_set_ids[Side.WHITE] = (
                        (self.piece_set_ids[Side.WHITE] + len(self.chaos_sets) + d)
                        % (len(piece_groups) + len(self.chaos_sets))
                        - len(self.chaos_sets)
                    ) if self.piece_set_ids[Side.WHITE] is not None else 0
                    self.piece_set_ids[Side.BLACK] = (
                        (self.piece_set_ids[Side.BLACK] + len(self.chaos_sets) + d)
                        % (len(piece_groups) + len(self.chaos_sets))
                        - len(self.chaos_sets)
                    ) if self.piece_set_ids[Side.BLACK] is not None else 0
                    which = {-1: 'previous', 1: 'next'}[d]
                    set_name_suffix = ''
                    if not self.hide_pieces:
                        if self.piece_set_ids[Side.WHITE] < 0:
                            set_name = get_set_name(self.chaos_sets[-self.piece_set_ids[Side.WHITE]])
                        else:
                            set_name = piece_groups[self.piece_set_ids[Side.WHITE]].get('name')
                        set_name_suffix = f" ({set_name})"
                    self.log(
                        f"Info: Using {which} piece set{set_name_suffix}",
                        bool(self.hide_pieces)
                    )
                else:  # Next player goes first
                    for data in (self.piece_sets, self.piece_set_ids, self.piece_set_names):
                        data[Side.WHITE], data[Side.BLACK] = data[Side.BLACK], data[Side.WHITE]
                    set_name_suffix = ''
                    if not self.hide_pieces:
                        set_names = [self.piece_set_names[side] for side in (Side.WHITE, Side.BLACK)]
                        set_name_suffix = f" ({' vs. '.join(set_names)})"
                    self.log(
                        f"Info: Swapping piece sets{set_name_suffix}",
                        bool(self.hide_pieces)
                    )
                self.reset_custom_data()
                self.reset_board()
        if symbol == key.O and modifiers & key.MOD_ACCEL and not partial_move:  # Toggle drops (Crazyhouse mode)
            self.use_drops = not self.use_drops
            if self.use_drops:
                self.log("Info: Drops enabled")
            else:
                self.log("Info: Drops disabled")
            self.future_move_history = []  # we don't know if we can redo all the future moves anymore, so we clear them
            self.unload_end_data()
            self.load_pieces()
            self.load_check()
            self.load_moves()
            self.reload_end_data()
            self.advance_turn()
        if symbol == key.P:  # Promotion
            if self.edit_mode:
                old_id = self.edit_piece_set_id
                if modifiers & key.MOD_ALT:  # Promote to custom pieces
                    self.edit_piece_set_id = 'wall' if modifiers & key.MOD_SHIFT else 'custom'
                    which = {'custom': 'custom', 'wall': 'obstacle'}[self.edit_piece_set_id]
                    self.log(f"Info: Placing {which} pieces", False)
                elif modifiers & key.MOD_SHIFT:  # Shift promotion piece set
                    if isinstance(self.edit_piece_set_id, int):
                        d = -1 if modifiers & key.MOD_ACCEL else 1
                        self.edit_piece_set_id = (self.edit_piece_set_id + d) % len(piece_groups)
                        which = {-1: 'previous', 1: 'next'}[d]
                    else:
                        self.edit_piece_set_id = 0
                        which = 'default'
                    set_name = piece_groups[self.edit_piece_set_id].get('name')
                    set_name_suffix = f" ({set_name})"
                    self.log(f"Info: Placing from {which} piece set{set_name_suffix}", False)
                elif modifiers & key.MOD_ACCEL:  # Reset promotion piece set
                    self.edit_piece_set_id = None
                    set_names = [self.piece_set_names[side] for side in (Side.WHITE, Side.BLACK)]
                    set_names = list(dict.fromkeys(set_names))
                    set_name_suffix = f"{'s' * (len(set_names) > 1)}"
                    if not self.hide_pieces:
                        set_name_suffix += f" ({' vs. '.join(set_names)})"
                    self.log(f"Info: Placing from current piece set{set_name_suffix}", False)
                if old_id != self.edit_piece_set_id:
                    self.reset_edit_promotions()
                    if self.promotion_piece:
                        promotion_piece = self.promotion_piece
                        promotion_side = self.get_promotion_side(promotion_piece)
                        self.end_promotion()
                        if len(self.edit_promotions[promotion_side]):
                            self.start_promotion(promotion_piece, self.edit_promotions[promotion_side])
                            self.update_caption()
        if symbol == key.F:
            if modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:  # Flip board
                self.flip_board()
                self.log("Info: Board flipped", False)
            if not modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Fast-forward
                self.auto_moves = False
                if self.future_move_history:
                    self.log("Info: Fast-forwarding", False)
                while self.future_move_history:
                    self.redo_last_move()
                self.auto_moves = True
            if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Fast-forward, but slowly. (Reload history)
                self.log("Info: Reloading history", False)
                self.log("Info: Starting new game", bool(self.hide_pieces))
                if not self.reload_history():
                    self.log("Error: Failed to reload history!")
                if self.edit_mode:
                    self.moves = {side: {} for side in self.moves}
                    self.chain_moves = {side: {} for side in self.chain_moves}
                    self.theoretical_moves = {side: {} for side in self.theoretical_moves}
                    self.show_moves()
        if symbol == key.G and not self.is_trickster_mode():  # Graphics
            old_color_index = self.color_index
            which = 'current'
            if modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:  # Graphics reset
                self.color_index = 0
                which = 'default'
            elif modifiers & key.MOD_SHIFT:  # Graphics shift
                if self.color_index is None:
                    self.color_index = 0
                    which = 'default'
                else:
                    d = -1 if modifiers & key.MOD_ACCEL else 1
                    self.color_index = (self.color_index + d) % len(colors)
                    which = {-1: 'previous', 1: 'next'}[d]
            if old_color_index != self.color_index:
                self.log(f"Info: Using {which} color scheme (ID {self.color_index})", False)
                self.color_scheme = colors[self.color_index]
                self.update_colors()
        if symbol == key.H:  # Hide pieces
            old_hide_pieces = self.hide_pieces
            old_hide_edit_pieces = self.hide_edit_pieces
            if modifiers & key.MOD_ALT and modifiers & key.MOD_SHIFT:  # Mark as hidden
                self.hide_edit_pieces = None if self.hide_edit_pieces is True else True
            elif modifiers & key.MOD_ALT:  # Mark as shown
                self.hide_edit_pieces = None if self.hide_edit_pieces is False else False
            elif modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Show
                self.hide_pieces = 0
            elif modifiers & key.MOD_SHIFT:  # Hide
                self.hide_pieces = 1
            elif modifiers & key.MOD_ACCEL:  # Penultima mode
                self.hide_pieces = 2
            if old_hide_edit_pieces != self.hide_edit_pieces:
                if self.hide_edit_pieces:
                    self.log("Info: Newly placed pieces are now marked as hidden", False)
                elif self.hide_edit_pieces is not None:
                    self.log("Info: Newly placed pieces are now marked as shown", False)
                else:
                    self.log("Info: Newly placed pieces are no longer marked", False)
            if old_hide_pieces != self.hide_pieces:
                if self.hide_pieces == 0:
                    self.log(
                        f"Info: Pieces revealed: "
                        f"{self.piece_set_names[Side.WHITE]} vs. "
                        f"{self.piece_set_names[Side.BLACK]}"
                    )
                elif self.hide_pieces == 1:
                    self.log("Info: Pieces hidden")
                elif self.hide_pieces == 2:
                    self.log("Info: Penultima mode active")
                else:
                    self.hide_pieces = old_hide_pieces
                self.update_pieces()
                self.show_moves()
        if symbol == key.M:  # Moves
            if modifiers & key.MOD_ALT and not partial_move:  # Clear future move history
                self.log("Info: Future move history cleared", False)
                if self.future_move_history:
                    self.future_move_history = []
                else:
                    self.clear_future_history(self.ply_count - 1)
                    self.log("Info: Probabilistic pieces updated")
                    self.unload_end_data()
                    self.load_pieces()
                    self.load_check()
                    self.load_moves()
                    self.reload_end_data()
                    self.advance_turn()
            else:  # Move visibility
                old_hide_move_markers = self.hide_move_markers
                if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Default
                    self.hide_move_markers = None
                elif modifiers & key.MOD_SHIFT:  # Hide
                    self.hide_move_markers = True
                elif modifiers & key.MOD_ACCEL:  # Show
                    self.hide_move_markers = False
                if old_hide_move_markers != self.hide_move_markers:
                    if self.hide_move_markers is None:
                        self.log("Info: Move markers default to piece visibility", False)
                    elif self.hide_move_markers is False:
                        self.log("Info: Move markers default to shown", False)
                    elif self.hide_move_markers is True:
                        self.log("Info: Move markers default to hidden", False)
                    else:
                        self.hide_move_markers = old_hide_move_markers
                    self.update_pieces()
                    self.show_moves()
        if symbol == key.K and not self.hide_move_markers:  # Move marker mode
            selected_square = self.selected_square
            if modifiers & key.MOD_ALT:  # Move type markers
                self.move_type_markers = not self.move_type_markers
                self.log(f"Info: Using {'typed' if self.move_type_markers else 'regular'} move markers", False)
            elif modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Default
                self.log("Info: Showing legal moves for moving player", False)
                self.load_moves(False)
            elif modifiers & key.MOD_ACCEL:  # Valid moves
                self.log("Info: Showing legal moves for both players", False)
                self.load_moves(False, Side.ANY, Side.NONE)
            elif modifiers & key.MOD_SHIFT:  # Theoretical moves
                self.log("Info: Showing all possible moves for both players", False)
                self.load_moves(False, Side.NONE, Side.ANY)
            if selected_square:
                self.select_piece(selected_square)
            self.show_moves()
        if symbol == key.T and modifiers & key.MOD_ACCEL:  # Trickster mode
            if self.color_scheme['scheme_type'] == 'cherub':
                self.trickster_color_index = (
                    0 if self.is_trickster_mode() else base_rng.randrange(len(trickster_colors)) + 1
                )
                self.reset_trickster_mode()
        if symbol == key.Z and modifiers & key.MOD_ACCEL:  # Undo
            if modifiers & key.MOD_SHIFT:  # Unless Ctrl+Shift+Z, then redo
                self.redo_last_finished_move()
            else:
                self.undo_last_finished_move()
            self.update_caption()
        if symbol == key.Y and modifiers & key.MOD_ACCEL:  # Redo
            self.redo_last_finished_move()
            self.update_caption()
        if symbol == key.L:
            if modifiers & key.MOD_ALT:  # Load save data
                self.deactivate()
                self.draw(0)
                self.log("Info: Selecting a file to load from", False)
                load_path = select_save_data()
                if load_path:
                    self.load(load_path, with_history=modifiers & key.MOD_SHIFT)
                    if not self.save_loaded:
                        self.reset_custom_data(True)
                        self.reset_board()
                        self.log_special_modes()
                else:
                    self.log("Info: Load cancelled", False)
                self.activate()
            else:  # Log
                if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Toggle verbose
                    if self.verbose is None:
                        # The granular log and status settings should really be changeable with hotkeys. Will add later.
                        pass
                    else:
                        self.verbose = not self.verbose
                        self.log(f"Info: Verbose output: {'ON' if self.verbose else 'OFF'}", False)
                elif modifiers & key.MOD_ACCEL:  # Save log
                    self.save_log()
                    self.log("Info: Log file saved", False)
                elif modifiers & key.MOD_SHIFT:  # Save verbose log
                    self.save_log(self.verbose_data, 'verbose')
                    self.log("Info: Verbose log file saved", False)
        if symbol == key.D:  # Debug
            if modifiers & key.MOD_ACCEL:  # Save debug log
                self.log("Info: Saving debug information", False)
                debug_log_data = debug_info(self)
                self.save_log(debug_log_data, 'debug')
                self.log("Info: Debug information saved", False)
            if modifiers & key.MOD_SHIFT:  # Print debug log
                self.log("Info: Printing debug information", False)
                debug_log_data = debug_info(self)
                for string in debug_log_data:
                    print(f"[Debug] {string}")
                self.log("Info: Debug information printed", False)
            if modifiers & key.MOD_ALT:  # Save debug listings
                self.log("Info: Saving debug listings", False)
                save_piece_data(self)
                save_piece_sets()
                save_piece_types()
                self.log("Info: Debug listings saved", False)
        if symbol == key.SLASH:  # (?) Random
            if self.edit_mode:
                return
            moves = self.unique_moves()[self.turn_side]
            if modifiers & key.MOD_SHIFT:  # Random piece
                self.deselect_piece()
                if moves:
                    self.log("Info: Selecting a random piece", False)
                    self.select_piece(base_rng.choice(list(moves.keys())))
            if modifiers & key.MOD_ACCEL:  # Random move
                if self.game_over:
                    return
                choices = (
                    moves.get(self.selected_square, [])
                    if self.selected_square       # Pick from moves of selected piece
                    else sum(moves.values(), [])  # Pick from all possible moves
                )
                if choices:
                    suffix = ' with selected piece' if self.selected_square else ''
                    self.log(f"Info: Making a random move{suffix}", False)
                    self.auto(base_rng.choice(choices))

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        if not self.is_active:
            return
        if symbol == key.ENTER:  # Simulate LMB
            self.on_mouse_release(
                round(self.highlight.center_x), round(self.highlight.center_y),  MOUSE_BUTTON_LEFT, modifiers
            )
        if symbol == key.BACKSPACE:  # Simulate RMB
            self.on_mouse_release(
                round(self.highlight.center_x), round(self.highlight.center_y),  MOUSE_BUTTON_RIGHT, modifiers
            )

    def load(self, path: str | None, with_history: bool = False) -> None:
        if not path:
            return
        update_mode = abs(self.board_config['save_update_mode'])
        should_update = bool(update_mode)
        if should_update:
            update_mode -= 1
        # noinspection PyBroadException
        try:
            save_path = join(base_dir, path)
            if not isfile(save_path):
                return
            self.log(f"Info: Loading from {path}")
            self.save_info = []
            save_data = ''
            save_data_start, save_data_end = False, False
            with open(save_path, mode='r', encoding='utf-8') as file:
                for line in file.read().splitlines():
                    stripped_line = line.strip()
                    if not stripped_line:
                        continue
                    if stripped_line[0] == '#':
                        if save_data_start:
                            save_data_end = True
                        self.save_info.append(stripped_line[1:].strip())
                    elif not save_data_start:
                        save_data_start = True
                        self.save_info.append(None)
                        save_data = line
                    elif save_data_end:
                        self.log("Error: Comments within save data are not supported")
                        save_data = ''
                    else:
                        save_data = f"{save_data}\n{line}"
                if not save_data:
                    self.log_info()
                    self.save_info.append(None)
                    return
            if self.load_board(save_data, with_history=update_mode & 1 if should_update else with_history):
                if should_update:
                    self.save(save_path)
        except Exception:
            self.log(f"Error: Failed to load from {path}")
            print_exc()

    def save(self, path: str | None, auto: bool = False) -> None:
        if not path:
            return
        data = self.dump_board(self.board_config[f"partial_{'auto' * auto}save"])  # completely unnecessary but whatever
        if auto and data == self.save_data:
            return
        makedirs(dirname(path), exist_ok=True)
        with open(path, mode='w', encoding='utf-8') as file:
            first_line = True
            for string in self.save_info:
                if first_line:
                    first_line = False
                else:
                    file.write('\n')
                if isinstance(string, str):
                    file.write(f"# {string}")
                elif string is None:
                    file.write(f"{data}")
        self.save_data = data
        self.save_path = path
        saved = 'Auto-saved' if auto else 'Saved'
        self.log(f"Info: {saved} to {path}", False)

    def auto_save(self) -> None:
        self.save(get_filename('autosave', 'json', in_dir=join(base_dir, 'auto')), auto=True)

    def log(self, string: str, important: bool = True, *, prefix: str | None = None) -> None:
        if prefix is None:
            if self.board_config['log_prefix'] == 0:
                prefix = f"Ply {self.ply_count}"
            if self.board_config['log_prefix'] > 0:
                if self.turn_data[0] == 0:
                    prefix = "Start"
                if self.turn_data[0] > 0:
                    prefix = f"Turn {self.turn_data[0]}: {self.turn_data[1]}"
                    if self.board_config['log_prefix'] > 1:
                        prefix += f", Move {self.turn_data[2]}"
                    if self.board_config['log_prefix'] > 2:
                        prefix = f"(Ply {self.ply_count}) {prefix}"
        if prefix:
            string = f"[{prefix}] {string}"
        self.verbose_data.append(string)
        if important:
            self.log_data.append(string)
        if self.verbose is None:
            return
        if important or self.verbose:
            print(string)

    def log_info(self, info: list[str | None] | None = None):
        if not self.board_config['log_info']:
            return
        if info is None:
            info = self.save_info
        for line in info:
            if isinstance(line, str):
                self.log(f"Note: {line}", False)

    def log_armies(self):
        if self.variant or self.custom_layout:
            self.log(f"Game: {self.variant or 'Custom'}")
            return
        if self.piece_set_ids[Side.WHITE] == self.piece_set_ids[Side.BLACK] == 0 and not self.hide_pieces:
            self.log("Game: Chess")
            return
        self.log(
            "Game: "
            f"{self.piece_set_names[Side.WHITE] if not self.hide_pieces else '???'} vs. "
            f"{self.piece_set_names[Side.BLACK] if not self.hide_pieces else '???'}"
        )

    def log_special_modes(self):
        if self.hide_pieces == 1:
            self.log("Info: Pieces hidden")
        if self.hide_pieces == 2:
            self.log("Info: Penultima mode active")
        if self.use_drops:
            self.log("Info: Drops enabled")

    def save_log(self, log_data: list[str] | None = None, log_name: str = 'log') -> None:
        if not log_data:
            log_data = self.log_data
        if log_data:
            with open(get_filename(log_name, 'txt'), mode='w', encoding='utf-8') as log_file:
                log_file.write('\n'.join(log_data))

    def clear_log(self, console: bool = True, log: bool = True, verbose: bool = True) -> None:
        self.log("Info: Log cleared", False)
        if console:
            system('cls' if os_name == 'nt' else 'clear')
        if log:
            self.log_data.clear()
        if verbose:
            self.verbose_data.clear()

    def save_config(self) -> None:
        config = copy(self.board_config)
        config['color_id'] = self.color_index
        config['white_id'] = self.piece_set_ids[Side.WHITE]
        config['black_id'] = self.piece_set_ids[Side.BLACK]
        config['edit_id'] = self.edit_piece_set_id
        config['hide_pieces'] = self.hide_pieces
        config['hide_moves'] = self.hide_move_markers
        config['use_drops'] = self.use_drops
        config['chaos_mode'] = self.chaos_mode
        config['chaos_seed'] = self.chaos_seed
        config['set_seed'] = self.set_seed
        config['roll_seed'] = self.roll_seed
        config['verbose'] = self.verbose
        config.save(get_filename('config', 'ini'))

    def run(self):
        if self.board_config['save_update_mode'] < 0 and self.load_data is not None:
            self.close()
        else:
            self.set_visible()
            super().run()
