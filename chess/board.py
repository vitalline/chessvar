from __future__ import annotations

from collections import defaultdict
from collections.abc import Collection, Sequence
from copy import copy, deepcopy
from datetime import datetime, UTC
from itertools import chain, product, zip_longest
from json import loads, JSONDecodeError
from math import ceil, floor, isqrt
from os import makedirs, name as os_name, system
from os.path import dirname, getsize, isfile, join, relpath, split
from random import Random
from sys import argv
from traceback import print_exc
from typing import Any, Callable, TypeVar

from PIL.ImageColor import getrgb
from arcade import key, MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT, Text
from arcade import Sprite, SpriteList, View, Window
from arcade import draw_sprite, get_screens
from requests import request
from requests.exceptions import RequestException

from chess.color import colors, default_colors, trickster_colors
from chess.color import average, darken, desaturate, lighten, saturate
from chess.config import Config
from chess.data import base_rng, get_set_data, get_set_name, piece_groups
from chess.data import default_board_width, default_board_height, default_size
from chess.data import min_width, min_height, min_size, max_size, size_step
from chess.data import action_types, end_types, expand_types as ext
from chess.data import prefix_chars as pch, prefix_types, type_prefixes
from chess.data import default_rules, default_sub_rules, default_end_rules
from chess.data import penultima_textures, sync_trim_fields
from chess.debug import debug_info, save_piece_data, save_piece_sets, save_piece_types
from chess.movement.base import BaseMovement
from chess.movement.move import Move
from chess.movement.types import AutoActMovement, AutoCaptureMovement, AutoMarkMovement, BaseMultiMovement
from chess.movement.types import CastlingMovement, CastlingPartnerMovement, ChangingLegalMovement, ChangingMovement
from chess.movement.types import CloneMovement, ConvertMovement, DropMovement, ProbabilisticMovement
from chess.movement.types import is_active
from chess.movement.util import Position, GenericPosition, ANY, LAST, NONE
from chess.movement.util import add, to_alpha as b26, resolve as res
from chess.movement.util import to_algebraic as toa, from_algebraic as fra, is_algebraic as isa
from chess.movement.util import to_algebraic_map as tom, from_algebraic_map as frm
from chess.pieces.groups.classic import Pawn, King
from chess.pieces.groups.colorbound import King as CBKing
from chess.pieces.piece import AbstractPiece, Piece
from chess.pieces.side import Side
from chess.pieces.types import Covered, Delayed, Delayed1, Shared, Slow
from chess.pieces.util import NoPiece, Obstacle, Block, Border, Shield, Void, Wall
from chess.save import condense, expand, condense_algebraic as cnd_alg, expand_algebraic as exp_alg, substitute
from chess.save import load_rng, load_move, load_piece, load_piece_type, load_custom_type, load_movement_type
from chess.save import save_rng, save_move, save_piece, save_piece_type, save_custom_type
from chess.util import base_dir, config_path, get_file_name, get_file_path
from chess.util import prompt_string, prompt_integer, load_menu, save_menu
from chess.util import Default, Unset, Key, Index, TypeOr, Unpacked, unpack, repack, sign, spell
from chess.util import deduplicate, dumps, find, find_string, fits, normalize, pluralize


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
        self.notation_offset = (0, 0)
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

        # piece base classes. when you need to check if something is a piece but you don't know what a piece is just yet
        self.piece_abc = AbstractPiece  # piece abstract base class
        self.piece_cbc = Piece          # piece concrete base class (now with sprites!)

        # basic window parameters used for resizing
        self.origin = self.width / 2, self.height / 2
        self.set_minimum_size(round(min_width), round(min_height))

        # window parameters when reverting to windowed mode
        # these are written to save data in fullscreen mode
        self.windowed_size = self.width, self.height
        self.windowed_square_size = self.square_size

        # truncate color scheme id to the total number of color schemes
        if self.board_config['color_id'] < 0 or self.board_config['color_id'] >= len(colors):
            self.board_config['color_id'] %= len(colors)

        self.color_index = self.board_config['color_id'] or 0  # index of the current color scheme
        self.color_scheme = colors[self.color_index]  # current color scheme
        self.background_color = self.color_scheme['background_color']  # background color
        self.log_data = []  # list of important logged strings
        self.verbose_data = []  # list of all logged strings
        self.verbose = self.board_config['verbose']  # whether to use verbose data for console output
        self.variant = ''  # name of the variant being played
        self.load_data = None  # last loaded data
        self.load_dict = None  # last loaded data, parsed from JSON
        self.load_name = ''  # name of the last loaded data file
        self.load_path = str(join(base_dir, self.board_config['load_path']))  # directory of the last loaded file
        self.auto_data = None  # last auto-saved data
        self.auto_name = ''  # name of the last auto-saved data file
        self.auto_path = str(join(base_dir, self.board_config['autosave_path']))  # directory for auto-saved files
        self.save_data = None  # last saved data
        self.save_name = ''  # name of the last saved data file
        self.save_path = str(join(base_dir, self.board_config['save_path']))  # directory of the last saved file
        self.save_info = []  # list of comment strings in save data
        self.save_imported = False  # whether a save was successfully imported
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
        self.drop_area = {}  # squares to draw captured pieces on in the drop UI
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
        self.turn_order = [(Side.WHITE, [{}]), (Side.BLACK, [{}])]  # order of turns
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
        self.alternate_pieces = self.board_config['alter_pieces']  # 0: promote, 1/2: white/black, -1/-2: show/hide
        self.alternate_swap = self.board_config['alter_swap']  # whether to swap the side showing alternate pieces
        self.hide_edit_pieces = False  # whether to mark pieces placed in edit mode as hidden
        self.auto_moves = True  # whether to skip move animations if allowed
        self.flip_mode = self.board_config['flip_board']  # whether the board is flipped
        self.edit_mode = self.board_config['edit_mode']  # allows to edit the board position if set to True
        self.game_over = False  # act 6 act 6 intermission 3 (game over)
        self.trickster_color_index = 0  # hey wouldn't it be funny if there was an easter egg here
        self.trickster_color_delta = 0  # but it's not like that's ever going to happen right
        self.trickster_angle_delta = 0  # this is just a normal chess game after all
        self.no_piece = NoPiece(self)  # piece that represents an off-board square
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
        self.royal_types = {Side.WHITE: {}, Side.BLACK: {}}  # types of pieces that are known to be considered royal
        self.royal_pieces = {Side.WHITE: [], Side.BLACK: []}  # these have to stay on the board and should be protected
        self.royal_markers = {Side.WHITE: set(), Side.BLACK: set()}  # squares where the side's royal pieces are
        self.anti_royal_pieces = {Side.WHITE: [], Side.BLACK: []}  # these need to remain attacked at all times
        self.anti_royal_markers = {Side.WHITE: set(), Side.BLACK: set()}  # squares where the side's anti-royals are
        self.en_passant_targets = {Side.WHITE: {}, Side.BLACK: {}}  # pieces that can be captured en passant
        self.en_passant_markers = {Side.WHITE: {}, Side.BLACK: {}}  # where the side's pieces can be captured e.p.
        self.royal_ep_targets = {Side.WHITE: {}, Side.BLACK: {}}  # royal pieces that can be captured en passant
        self.royal_ep_markers = {Side.WHITE: {}, Side.BLACK: {}}  # where the side's royals can be captured e.p.
        self.relay_targets = {Side.WHITE: {}, Side.BLACK: {}}  # pieces that can get powers relayed from friendly pieces
        self.relay_sources = {Side.WHITE: {}, Side.BLACK: {}}  # pieces that relay powers to the side's pieces
        self.coordinate_targets = {Side.WHITE: {}, Side.BLACK: {}}  # squares that are targeted by coordination partners
        self.coordinate_sources = {Side.WHITE: {}, Side.BLACK: {}}  # pieces that can act as coordination partners
        self.auto_pieces = {Side.WHITE: [], Side.BLACK: []}  # pieces that automatically act anywhere they can move to
        self.auto_markers = {Side.WHITE: {}, Side.BLACK: {}}  # squares where the side's pieces can automatically act
        self.auto_markers_theoretical = {Side.WHITE: {}, Side.BLACK: {}}  # same as above, but for theoretical moves
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
        self.custom_variant = ''  # custom variant name
        self.captured_pieces = {Side.WHITE: [], Side.BLACK: []}  # pieces captured by each side
        self.alias_dict = {}  # dictionary of aliases for save data
        self.moves = {Side.WHITE: {}, Side.BLACK: {}}  # dictionary of valid moves from any square
        self.chain_moves = {Side.WHITE: {}, Side.BLACK: {}}  # dictionary of moves chained from a certain move (from/to)
        self.chain_start = None  # move that started the current chain (if any)
        self.theoretical_moves = {Side.WHITE: {}, Side.BLACK: {}}  # dictionary of theoretical moves from any square
        self.threats = {}  # inverted version of the above dictionary that only stores positions
        self.move_tags = set()  # set of currently legal move tags (NB: only used during TagMovement move generation)
        self.moves_queried = {Side.WHITE: False, Side.BLACK: False}  # whether moves have been queried for each side
        self.display_moves = {Side.WHITE: False, Side.BLACK: False}  # whether to display moves for each side
        self.display_theoretical_moves = {Side.WHITE: False, Side.BLACK: False}  # same for theoretical moves
        self.theoretical_move_markers = True  # whether to display theoretical moves (overrides above)
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
        self.is_started = False  # whether a game has been initialized and started
        self.extra_labels = False  # whether to show additional labels on border rows/columns
        self.show_history = False  # whether to show all moves made during the opponent's turn
        self.show_drops = False  # whether to show a list of all droppable pieces (the drop UI)
        self.row_label_list = []  # labels for the rows
        self.col_label_list = []  # labels for the columns
        self.board_sprite_list = SpriteList()  # sprites for the board squares
        self.move_sprite_list = SpriteList()  # sprites for the move markers
        self.type_sprite_list = SpriteList()  # sprites for the type-based move markers
        self.piece_sprite_list = SpriteList()  # sprites for the pieces
        self.promotion_area_sprite_list = SpriteList()  # sprites for the promotion area background tiles
        self.promotion_piece_sprite_list = SpriteList()  # sprites for the possible promotion pieces
        self.drop_area_sprite_list = SpriteList()  # sprites for the drop UI background tiles
        self.drop_piece_sprite_list = SpriteList()  # sprites for the drop UI captured pieces
        self.drop_piece_label_list = []  # labels for the drop UI captured piece counts
        self.sync_timestamp = None  # timestamp of the last server sync
        self.sync_interval = 0.0  # time since the last server sync
        self.save_interval = 0.0  # time since the last autosave

        # normalize file paths
        paths = self.auto_path, self.load_path, self.save_path
        self.auto_path, self.load_path, self.save_path = map(normalize, paths)

        # load piece set ids from the config
        for side in self.piece_set_ids:
            self.piece_set_ids[side] = self.board_config[f'{side.key()}id'] or self.piece_set_ids[side]
        self.edit_piece_set_id = self.board_config['edit_id']

        # initialize random number seeds and generators
        self.roll_seed = (
            self.board_config['roll_seed']
            if self.board_config['roll_seed'] is not None
            else base_rng.randint(0, self.board_config['max_seed'])
        )
        self.roll_rng = None  # will be initialized later
        self.set_seed = (
            self.board_config['set_seed']
            if self.board_config['set_seed'] is not None
            else base_rng.randint(0, self.board_config['max_seed'])
        )
        self.set_rng = Random(self.set_seed)
        self.chaos_seed = (
            self.board_config['chaos_seed']
            if self.board_config['chaos_seed'] is not None
            else base_rng.randint(0, self.board_config['max_seed'])
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
        save_path = None
        if len(argv) > 1:
            save_path = argv[1]
        elif save_name := self.board_config['load_save'].strip():
            save_path = join(self.load_path, save_name + ('.json' if '.' not in save_name else ''))
        load_attempted = self.load(save_path)
        if not load_attempted or not self.save_imported:
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
        offset: tuple[int, int] | None = None,
        flip: bool | None = None,
        between_cols: bool = False,
        between_rows: bool = False,
    ) -> Position | None:
        x, y = pos
        size = self.square_size if size is None else size
        origin = self.origin if origin is None else origin
        width = self.visual_board_width if width is None else width
        height = self.visual_board_height if height is None else height
        border_cols = self.border_cols if border_cols is None else border_cols
        border_rows = self.border_rows if border_rows is None else border_rows
        offset = self.notation_offset if offset is None else offset
        flip = self.flip_mode if flip is None else flip
        board_size = width, height
        col = round((x - origin[0]) / size + (board_size[0] - 1) / 2)
        row = round((y - origin[1]) / size + (board_size[1] - 1) / 2)
        col, row = (board_size[0] - 1 - col, board_size[1] - 1 - row) if flip else (col, row)
        col, row = (col + offset[0], row + offset[1])
        for border_col in border_cols:
            if col > border_col:
                col -= 1
            elif col == border_col and not between_cols:
                return None
        for border_row in border_rows:
            if row > border_row:
                row -= 1
            elif row == border_row and not between_rows:
                return None
        return row, col

    def get_screen_position(
        self,
        pos: Position | None,
        size: float | None = None,
        origin: tuple[float, float] | None = None,
        width: int | None = None,
        height: int | None = None,
        border_cols: list[int] | None = None,
        border_rows: list[int] | None = None,
        offset: tuple[int, int] | None = None,
        flip: bool | None = None,
        between_cols: bool = False,
        between_rows: bool = False,
    ) -> tuple[float, float]:
        if pos is None:
            return -1, -1
        row, col = pos
        size = self.square_size if size is None else size
        origin = self.origin if origin is None else origin
        width = self.visual_board_width if width is None else width
        height = self.visual_board_height if height is None else height
        border_cols = self.border_cols if border_cols is None else border_cols
        border_rows = self.border_rows if border_rows is None else border_rows
        offset = self.notation_offset if offset is None else offset
        flip = self.flip_mode if flip is None else flip
        board_size = width, height
        col += sum(1 for border_col in border_cols if (col > border_col or not between_cols and col == border_col))
        row += sum(1 for border_row in border_rows if (row > border_row or not between_rows and row == border_row))
        col, row = (col - offset[0], row - offset[1])
        col, row = (board_size[0] - 1 - col, board_size[1] - 1 - row) if flip else (col, row)
        x = (col - (board_size[0] - 1) / 2) * size + origin[0]
        y = (row - (board_size[1] - 1) / 2) * size + origin[1]
        return x, y

    def get_absolute(self, pos: Position | None) -> Position:
        return None if pos is None else (pos[0] - self.notation_offset[1], pos[1] - self.notation_offset[0])

    def get_relative(self, pos: Position | None) -> Position:
        return None if pos is None else (pos[0] + self.notation_offset[1], pos[1] + self.notation_offset[0])

    # From now on we shall unanimously assume that the first coordinate corresponds to row number (AKA vertical axis).

    @staticmethod
    def get_square_color(pos: Position) -> int:
        return (pos[0] + pos[1]) % 2

    def is_dark_square(self, pos: Position) -> bool:
        return self.get_square_color(pos) == 0

    def is_light_square(self, pos: Position) -> bool:
        return self.get_square_color(pos) == 1

    def get_piece(self, pos: Position | None) -> AbstractPiece:
        if self.not_on_board(pos):
            return self.no_piece
        pos = self.get_absolute(pos)
        return self.pieces[pos[0]][pos[1]]

    def get_side(self, pos: Position | None) -> Side:
        return self.get_piece(pos).side

    def get_turn_index(self, offset: int = 0, origin: int | None = None) -> int:
        if origin is None:
            origin = self.ply_count
        ply_count = origin + offset
        return (
            (ply_count - 1 - self.initial_turns) % (len(self.turn_order) - self.initial_turns) + self.initial_turns
            if ply_count > self.initial_turns else ply_count - 1
        )

    def get_turn_entry(self, offset: int = 0, origin: int | None = None) -> tuple[Side, list[dict]]:
        index = self.get_turn_index(offset, origin)
        if index < 0:
            return Side.NONE, []
        return self.turn_order[index]

    def get_turn_side(self, offset: int = 0, origin: int | None = None) -> Side:
        return self.get_turn_entry(offset, origin)[0]

    def get_turn_rules(self, offset: int = 0, origin: int | None = None) -> list[dict]:
        return self.get_turn_entry(offset, origin)[1]

    def get_promotion_side(self, piece: AbstractPiece):
        return (
            piece.side if piece.side in {Side.WHITE, Side.BLACK} else
            (Side.WHITE if piece.board_pos[0] < (self.board_height / 2 + self.notation_offset[1]) else Side.BLACK)
        )

    def shift_ply(self, offset: int) -> None:
        if self.ply_count <= 0:
            self.ply_count = 1
            self.turn_side, self.turn_rules = self.get_turn_entry()
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
        self.turn_side, self.turn_rules = self.get_turn_entry()

    def keys(self, data):
        if isinstance(data, Move):
            if data.tag:
                yield pch['tag'] + data.tag
            if data.type_str():
                yield pch['type'] + data.type_str()
        elif isinstance(data, AbstractPiece):
            if data.side:
                yield from self.keys(data.side)
            yield from self.keys(type(data))
        elif isinstance(data, Side):
            yield from (pch['side'] + data.name.lower(), pch['side'] + str(data.value))
        elif isinstance(data, type):
            if issubclass(data, AbstractPiece):
                for group in data.groups():
                    yield pch['group'] + group
                if data.name:
                    yield pch['name'] + data.name
                if data.type_str():
                    yield pch['type'] + data.type_str()
            if issubclass(data, BaseMovement):
                yield pch['type'] + data.type_str()
        elif isinstance(data, list):
            yield from (k for x in data if x for k in self.keys(x) if k)
        elif data:
            if isinstance(data, tuple):
                if isinstance(data[0], Side):
                    yield from (x for x in data[1:] if x)
                else:
                    yield data
            else:
                yield data

    def fits(self, template: str, data: Any, last: Any = ()) -> bool:
        if template == ANY:
            return True
        def double(x):
            if isinstance(x, str) and ((y := x.lstrip(''.join(prefix_types))) and y != x):
                return x, y
            return x,
        if template in {NONE, LAST, *type_prefixes} and last:
            data_set = set(
                x for k in self.keys(data)
                if template in {NONE, LAST}
                or isinstance(k, str)
                and k.startswith(template)
                for x in double(k)
            )
            return any(data_set.intersection(double(k)) for k in self.keys(last))
        if isinstance(data, list):
            return any(self.fits(template, item, last) for item in data)
        if isinstance(data, tuple):
            if not data:
                return False
            if isinstance(data[0], int):
                return self.in_area(template, data, last=last)  # type: ignore
            return self.in_area(template, data[1], data[0], last=last)  # type: ignore
        data_set = set(x for k in self.keys(data) for x in double(k))
        return fits(template, data_set)

    def fits_one(self, t: Index, p: Unpacked[Key], d: Any = (), l: Any = (), fit: bool = True):
        p, l = (repack(x) for x in (p, l))
        lf = lambda ts, *fs: list(find(ts, *fs))
        def split_templates(templates: Index, fields: Sequence[Key]) -> dict[bool, Collection]:
            results = {False: set(), True: set()}
            for s in lf(templates, *fields):
                (results[False].add(s[1:]) if isinstance(s, str) and s[0:1] == pch['not'] else results[True].add(s))
            return results
        def match_templates(s: Collection):
            return any(self.fits(x, d, lf(t, *l)) for x in s) if fit else ('*' in s or any(e in s for e in d))
        for k, part in split_templates(t, p).items():
            if part and k != match_templates(part):
                return False
        return True

    def fits_any(
        self, templates: Collection[Index], path: Unpacked[Key], data: Any = (), last: Any = (), fit: bool = True
    ) -> bool:
        return any(self.fits_one(template, path, data, last, fit) for template in templates)

    def filter(
        self, templates: Collection[Index], path: Unpacked[Key], data: Any = (), last: Any = (), fit: bool = True
    ) -> list:
        return [template for template in templates if self.fits_one(template, path, data, last, fit)]

    def split(
        self, templates: Collection[Index], path: Unpacked[Key], data: Any = (), last: Any = (), fit: bool = True
    ) -> tuple[list, list]:
        results = {False: [], True: []}
        _ = [results[self.fits_one(template, path, data, last, fit)].append(template) for template in templates]
        return results[True], results[False]

    def set_position(self, piece: AbstractPiece, pos: Position, update: bool = True) -> None:
        piece.board_pos = pos
        if update and isinstance(piece, Piece):
            piece.sprite.position = self.get_screen_position(pos)

    def reset_position(self, piece: AbstractPiece, update: bool = True) -> None:
        self.set_position(piece, piece.board_pos, update)

    def on_board(self, pos: Position | None) -> bool:
        return not self.not_on_board(pos)

    def not_on_board(self, pos: Position | None) -> bool:
        pos = self.get_absolute(pos)
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
        if isinstance(piece, Piece):
            self.piece_sprite_list.remove(piece.sprite)
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
        if isinstance(piece, Piece):
            self.reset_position(piece)
            self.piece_sprite_list.append(piece.sprite)

        self.selected_square = None
        self.show_moves()

    def reset_pieces(self, pieces: dict | None = None) -> None:
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
            pos = self.get_relative((row, col))
            if pieces is not None:
                piece_data = pieces.get(pos)
                self.pieces[row].append(
                    NoPiece(self, board_pos=pos) if piece_data is None
                    else load_piece(self, piece_data, self.custom_pieces).on(pos)
                )
            elif self.custom_layout:
                self.pieces[row].append(
                    copy(self.custom_layout[pos])
                    if pos in self.custom_layout
                    else NoPiece(self, board_pos=pos)
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
                    piece_type(board=self, board_pos=pos, side=piece_side)
                )
            if isinstance(self.pieces[row][col], Piece):
                if not isinstance(self.pieces[row][col], (NoPiece, Obstacle)):
                    self.update_piece(self.pieces[row][col])
                    self.pieces[row][col].set_color(
                        self.color_scheme.get(
                            f"{self.pieces[row][col].side.key()}piece_color",
                            self.color_scheme['piece_color']
                        ),
                        self.color_scheme['colored_pieces']
                    )
                self.pieces[row][col].set_size(self.square_size)
                self.piece_sprite_list.append(self.pieces[row][col].sprite)

    def reset_board(self, update: bool | None = True, log: bool = True) -> None:
        self.save_interval = 0.0
        self.sync_interval = 0.0
        self.is_started = False

        self.hovered_square = None
        self.deselect_piece()
        self.clear_relay_markers()
        self.clear_en_passant_markers()
        self.clear_auto_markers()
        self.reset_captures()
        self.update_drops(False)

        old_turn_side = self.turn_side

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

        if self.edit_mode != self.board_config['edit_mode']:
            self.edit_mode = self.board_config['edit_mode']
            self.log(f"Mode: {'EDIT' if self.edit_mode else 'PLAY'}", False)

        if update is None:
            update = not self.move_history

        if update:
            self.edit_piece_set_id = self.board_config['edit_id']
            self.roll_history = []
            self.future_move_history = []
            self.probabilistic_piece_history = []
            self.reset_end_rules()
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
                self.roll_seed = self.roll_rng.randint(0, self.board_config['max_seed'])
            self.roll_rng = Random(self.roll_seed)

        self.move_history = []

        self.reset_pieces()

        self.draw(0)

        self.clear_theoretical_moves()
        self.unload_end_data()
        self.load_pieces()
        self.load_check()
        self.update_end_data()
        self.load_moves()
        self.reload_end_data()
        if old_turn_side != self.turn_side:
            self.update_alternate_sprites(old_turn_side)
        self.update_status()

        self.is_started = True
        self.sync(get=not self.game_loaded, post=True)

    def dump_board(
        self,
        data: dict | None = None,
        trim: bool | Collection[str] = False,
        alias: bool | dict[str, Any] = True,
        string: bool = True,
        unicode: bool = True,
        compress: int | None = None,
        recursive: bool | None = None,
        indent: type(Default) | int | None = Default,
    ) -> str | dict:
        no_data = data is None
        wh = self.board_width, self.board_height, *self.notation_offset
        whn = *wh, {}
        whc = *wh, {}
        wha = defaultdict(lambda: whn)
        if no_data:
            whc = *wh, {k: v for k, v in self.custom_areas.items() if isinstance(v, set)}
            wha = defaultdict(lambda: whn, {s: (*wh, self.areas.get(s) or {}) for s in (Side.WHITE, Side.BLACK)})
        data = {
            'variant': self.custom_variant,
            'info': '\n'.join(self.save_info),
            'board_size': [self.board_width, self.board_height],
            'offset': list(self.notation_offset),
            'borders': [toa((ANY, col)) for col in self.border_cols] + [toa((row, ANY)) for row in self.border_rows],
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
            } if isinstance(self.custom_pawns, dict)
            else unpack([save_piece_type(t) for t in self.custom_pawns])
            if self.custom_pawns is not None else None,
            'pieces': cnd_alg({
                p.board_pos: save_piece(p.on(None))
                for pieces in [*self.movable_pieces.values(), self.obstacles] for p in pieces
            }, *whc),
            'custom': {
                k: save_custom_type(v(self))  # instantiating a custom piece type loads the type's default movement data
                for k, v in self.custom_pieces.items()  # so the movement will actually get compressed when exporting it
            },
            'layout': cnd_alg({pos: save_piece(p.on(None)) for pos, p in self.custom_layout.items()}, *whc),
            'promotions': {
                side.value: {
                    save_piece_type(f): cnd_alg({
                        p: unpack([
                            save_piece(t, f, True) if isinstance(t, AbstractPiece) else save_piece_type(t, f) for t in l
                        ]) for p, l in s.items()
                    }, *wha[side]) for f, s in d.items()
                } for side, d in self.custom_promotions.items()
            },
            'drops': {
                side.value: {
                    save_piece_type(f): cnd_alg({
                        p: unpack([
                            save_piece(t, f, True) if isinstance(t, AbstractPiece) else save_piece_type(t, f) for t in l
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
                side[0].value if side[1] is None else [
                    side[0].value, unpack([{mk: unpack([
                        {lk: unpack(lv) for lk in sorted(default_sub_rules.get(mk, {})) if (lv := ld.get(lk))}
                        if isinstance(ld, dict) else ld for ld in mv
                    ]) for mk in sorted(default_rules) if (mv := md.get(mk)) is not None} for md in side[1]])
                ] for side in self.custom_turn_order
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
                            (condition := end_types.get(word)) in ext(('check', 'capture'))
                            or condition in ext(('checkmate',))
                            and ((need := self.end_rules.get(side, {}).get(condition, {}).get(group, 0))
                            and isinstance(need, int) and abs(need) > 1)
                        )
                    })
                })
            },
            'edit': self.edit_mode,
            'edit_promotion': self.edit_piece_set_id,
            'alter_pieces': self.alternate_pieces,
            'alter_swap': self.alternate_swap,
            'hide_pieces': self.hide_pieces,
            'hide_moves': self.hide_move_markers,
            'use_drops': self.use_drops,
            'chaos_mode': self.chaos_mode,
            'chaos_seed': self.chaos_seed,
            'set_seed': self.set_seed,
            'roll_seed': self.roll_seed,
            'roll_update': self.board_config['update_roll_seed'],
        } if no_data else data
        if no_data:
            for k, v in {
                'chaos': (self.chaos_seed, self.chaos_rng),
                'set': (self.set_seed, self.set_rng),
                'roll':  (self.roll_seed, self.roll_rng),
            }.items():
                seed, rng = v
                new_rng = Random(seed)
                if rng.getstate() != new_rng.getstate():
                    data[f"{k}_state"] = save_rng(rng)
        if not isinstance(trim, bool):
            data = {k: v for k, v in data.items() if k not in trim}
        elif trim and self.load_dict is not None:
            data = {k: v for k, v in data.items() if k in self.load_dict}
        alias_dict = alias if isinstance(alias, dict) else self.alias_dict
        if recursive is None:
            recursive = self.board_config['recursive_aliases']
        if alias and alias_dict and recursive is not None:
            data = {'alias': alias_dict, **condense(data, alias_dict, recursive)}
        if not string:
            return data
        indent = self.board_config['indent'] if indent is Default else indent
        compress = self.board_config['compression'] if compress is None else compress
        if indent is None:
            return dumps(data, separators=(',', ':'), indent=indent, ensure_ascii=not unicode)
        else:
            return dumps(data, compression=compress, indent=indent, ensure_ascii=not unicode)

    def load_board(self, dump: str, with_history: bool = False) -> bool:
        self.save_imported = False
        self.save_loaded = False

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

        self.save_interval = 0.0
        self.sync_interval = 0.0
        self.is_started = False
        success = True

        self.hovered_square = None
        self.deselect_piece()
        self.clear_relay_markers()
        self.clear_en_passant_markers()
        self.clear_auto_markers()
        self.update_drops(False)
        self.end_value = 0
        self.end_group = None
        self.end_condition = None
        self.win_side = Side.NONE
        self.game_over = False
        self.action_count = 0

        self.alias_dict = data.get('alias', {})
        if 'alias' in data:
            del data['alias']
        if self.alias_dict and self.board_config['recursive_aliases'] is not None:
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

        self.custom_variant = data.get('variant', '')
        self.save_info = list(chain.from_iterable(str(x).split('\n') for x in repack(data.get('info') or ())))

        # might have to add more error checking to saving/loading, even if at the cost of slight redundancy.
        # who knows when someone decides to introduce a breaking change and absolutely destroy all the saves
        board_size = tuple(data.get('board_size', (self.board_width, self.board_height)))
        offset = tuple(data.get('offset', (0, 0)))
        borders = [fra(t) for t in data.get('borders', [])]
        borders = [t[1] for t in borders if t[0] == ANY], [t[0] for t in borders if t[1] == ANY]
        self.resize_board(*board_size, *borders, *offset, update=False)

        wh = self.board_width, self.board_height, *self.notation_offset
        whn = *wh, {}
        self.custom_areas = {
            name: {
                Side(int(side)): set(frm(repack(area), *whn)) for side, area in data.items()
            } if isinstance(data, dict) else set(frm(repack(data), *whn))
            for name, data in data.get('areas', {}).items()
        }
        self.reset_areas()
        whc = *wh, {k: v for k, v in self.custom_areas.items() if isinstance(v, set)}
        wha = defaultdict(lambda: whn, {side: (*wh, self.areas.get(side) or {}) for side in [Side.WHITE, Side.BLACK]})

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
            self.log(
                f"Error: Square size does not match (was {round(square_size, 5)}, but is {round(new_square_size, 5)})"
            )

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

        self.alternate_pieces = data.get('alter_pieces', self.alternate_pieces)
        self.alternate_swap = data.get('alter_swap', self.alternate_swap)
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
                piece_type.add_group(group)
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
                        (load_piece_type(t, c, f) if isinstance(t, str) else load_piece(self, t, c, f, True))
                        for t in repack(l)
                    ] for p, l in exp_alg(s, *wha[Side(int(v))]).items()
                } for f, s in d.items()
            } for v, d in data.get('promotions', {}).items()
        }
        self.custom_drops = {
            Side(int(v)): {
                load_piece_type(f, c): {
                    p: [
                        (load_piece_type(t, c, f) if isinstance(t, str) else load_piece(self, t, c, f, True))
                        for t in repack(l)
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

        self.custom_layout = {p: load_piece(self, v, c).on(p) for p, v in exp_alg(data.get('layout', {}), *whc).items()}

        if 'ply' in data:
            ply_count = data['ply']
            if ply_count <= 0:
                self.log(f"Error: Invalid ply count ({ply_count})")
                ply_count = 1
        else:
            ply_count = self.ply_count
        self.custom_turn_order = [
            (Side(int(side[0])), [{mk: [
                {lk: repack(lv) for lk in default_sub_rules.get(mk, {}) if (lv := ld.get(lk))}
                if isinstance(ld, dict) else ld for ld in repack(mv)
            ] for mk in default_rules if (mv := md.get(mk)) is not None} for md in repack(side[1])])
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
            for k in end_data[s]:
                keyword = end_types.get(k, k)
                if keyword not in self.end_data[side]:
                    continue
                for g in end_data[s][k]:
                    group = g
                    if group not in self.end_data[side][keyword]:
                        continue
                    self.end_data[side][keyword][group] = end_data[s][k][g]

        self.reset_drops()
        self.reset_promotions()
        self.reset_edit_promotions()
        self.reset_penultima_pieces()

        self.move_history = [load_move(self, d, c) for d in data.get('moves', [])]
        self.future_move_history = [load_move(self, d, c) for d in data.get('future', [])[::-1]]

        rolls = data.get('rolls', {})
        self.roll_history = [
            ({fra(s): v for s, v in rolls[str(n)].items()} if str(n) in rolls else {})
            for n in range(ply_count)
        ]
        rph = data.get('roll_piece_history', {})
        self.probabilistic_piece_history = [
            ({(fra(k), load_piece_type(v, c)) for k, v in rph[str(n)].items()} if str(n) in rph else set())
            for n in range(ply_count)
        ]

        self.chain_start = load_move(self, data.get('chain_start'), c)
        if self.move_history and self.move_history[-1] and self.move_history[-1].matches(self.chain_start):
            self.chain_start = self.move_history[-1]
        chained_move = self.chain_start
        poss = []
        while chained_move:
            poss.extend((chained_move.pos_from, chained_move.pos_to))
            chained_move = chained_move.chained_move
        self.chain_moves = {
            self.chain_start.piece.side: {
                (tuple(poss)): [load_move(self, m, c) for m in data.get('chain_moves', [])]
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

        if 'pieces' in data:
            pieces = exp_alg(data['pieces'], *whc)
        elif old_pieces:
            pieces = old_pieces
        else:
            pieces = None

        for sprite_list in (
            self.piece_sprite_list,
            self.promotion_piece_sprite_list,
            self.promotion_area_sprite_list
        ):
            sprite_list.clear()

        self.reset_pieces(pieces)

        self.draw(0)

        self.promotion_piece = load_piece(self, data.get('promotion'), c)

        self.load_pieces()
        self.update_pieces()
        self.update_colors()
        for side in self.auto_pieces:
            if self.auto_pieces[side]:
                self.load_auto_markers(side)

        starting = 'Starting new' if with_history else 'Resuming saved'
        if self.custom_variant:
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
            self.turn_side, self.turn_rules = self.get_turn_entry()
            if self.turn_side != turn_data[1]:
                self.log(f"Error: Turn side does not match ({self.turn_side} was {turn_data[1]})")
                self.turn_side = turn_data[1]
        self.log_armies()
        self.log_info()
        if with_history or self.ply_count == 0:
            self.shift_ply(+1)
        self.log_special_modes()
        if with_history:
            success = self.reload_history()
            if not success:
                self.log("Error: Failed to reload history")
        else:
            if self.move_history:
                last_move = self.move_history[-1]
                if last_move and last_move.is_edit != 1 and last_move.movement_type != DropMovement:
                    if last_move.piece and last_move.piece.movement:
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
            self.update_alternate_sprites()
            if self.move_history and self.move_history[-1]:
                if self.move_history[-1].is_edit == 1:
                    self.start_promotion(piece, self.edit_promotions[self.get_promotion_side(piece)])
                elif self.move_history[-1].piece.board_pos == piece.board_pos:
                    if isinstance(piece, NoPiece):
                        self.move_history[-1] = self.try_drop(self.move_history[-1])
                    else:
                        self.move_history[-1] = self.try_promotion(self.move_history[-1])
        else:
            if not with_history and not self.edit_mode:
                self.clear_theoretical_moves()
                self.unload_end_data()
                self.load_pieces()
                self.load_check()
                self.load_moves()
                self.reload_end_data()
                self.update_alternate_sprites()
                self.update_status()
            selection = data.get('selection')
            if selection:
                self.select_piece(fra(selection))

        self.load_data = dump
        self.load_dict = data
        self.is_started = True
        self.save_imported = True
        self.save_loaded = success

        return success

    def empty_board(self) -> None:
        self.save_interval = 0.0
        self.sync_interval = 0.0
        self.is_started = False

        self.hovered_square = None
        self.deselect_piece()
        self.clear_relay_markers()
        self.clear_en_passant_markers()
        self.clear_auto_markers()
        self.reset_captures()
        self.update_drops(False)

        old_turn_side = self.turn_side

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

        self.log("Info: Board cleared")
        self.shift_ply(+1)
        if not self.edit_mode:
            self.log("Mode: EDIT", False)
        self.edit_mode = True

        self.edit_piece_set_id = self.board_config['edit_id']
        self.roll_history = []
        self.future_move_history = []
        self.probabilistic_piece_history = []
        self.reset_end_rules()
        self.reset_drops()
        self.reset_promotions()
        self.reset_edit_promotions()
        self.reset_penultima_pieces()

        if self.board_config['update_roll_seed']:
            self.roll_seed = self.roll_rng.randint(0, self.board_config['max_seed'])
        self.roll_rng = Random(self.roll_seed)

        self.move_history = []

        self.reset_pieces({})

        self.draw(0)

        self.clear_theoretical_moves()
        self.unload_end_data()
        self.load_pieces()
        self.load_check()
        self.update_end_data()
        self.load_moves()
        self.reload_end_data()
        if old_turn_side != self.turn_side:
            self.update_alternate_sprites(old_turn_side)
        self.update_status()

        self.is_started = True
        self.sync(post=True)

    def reset_custom_data(self, rollback: bool = False) -> None:
        if rollback:
            self.custom_pieces = self.past_custom_pieces
        else:
            self.past_custom_pieces = {**self.past_custom_pieces, **self.custom_pieces}
        self.save_info = []
        self.custom_variant = ''
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
                piece_type.clear_groups()
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

    def reset_drops(self, piece_sets: dict[Side, list[type[AbstractPiece]]] | None = None) -> None:
        if self.custom_drops:
            self.drops = deepcopy(self.custom_drops)
            return
        if piece_sets is None:
            piece_sets = self.piece_sets
        self.drops = {}
        drop_squares = [
            self.get_relative((i, j)) for i in range(self.board_height) for j in range(self.board_width)
        ]
        pawn_drop_squares = [
            self.get_relative((i, j)) for i in range(1, self.board_height - 1) for j in range(self.board_width)
        ]
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
                        royal_value = self.get_royal_value(piece_type, drop_side)
                        if royal_value and royal_value not in {'+', '-'}:
                            continue
                        drops[piece_type] = {pos: [piece_type] for pos in drop_squares}
            self.drops[drop_side] = drops

    def reset_promotions(self, piece_sets: dict[Side, list[type[AbstractPiece]]] | None = None) -> None:
        if self.custom_promotions:
            self.promotions = deepcopy(self.custom_promotions)
            return
        if piece_sets is None:
            piece_sets = self.piece_sets
        self.promotions = {}
        promotion_squares = {
            Side.WHITE: [self.get_relative((self.board_height - 1, i)) for i in range(self.board_width)],
            Side.BLACK: [self.get_relative((0, i)) for i in range(self.board_width)],
        }
        middle = {side: len(piece_sets[side]) // 2 for side in self.piece_sets}
        custom_pawns = {
            side: self.custom_pawns.get(side)
            if isinstance(self.custom_pawns, dict)
            else self.custom_pawns for side in piece_sets
        }
        for side in promotion_squares:
            promotions = []
            used_piece_set = set()
            for pieces in (
                piece_sets[side][middle[side] - 1::-1], piece_sets[side.opponent()][middle[side.opponent()] - 1::-1],
                piece_sets[side][middle[side] + 1:], piece_sets[side.opponent()][middle[side.opponent()] + 1:],
                [
                    *piece_sets[side.opponent()][middle[side.opponent()]:middle[side.opponent()] + 1],
                    *piece_sets[side][middle[side]:middle[side] + 1],
                ],
            ):
                promotion_types = []
                for piece_type in pieces:
                    if piece_type not in used_piece_set and not issubclass(piece_type, NoPiece):
                        royal_value = self.get_royal_value(piece_type, side)
                        if royal_value and royal_value not in {'+', '-'}:
                            continue
                        used_piece_set.add(piece_type)
                        promotion_types.append(piece_type)
                promotions.extend(promotion_types[::-1])
            self.promotions[side] = {}
            pawns = custom_pawns[side]
            for pawn in (pawns if pawns is not None else [Pawn]):
                self.promotions[side][pawn] = {pos: promotions.copy() for pos in promotion_squares[side]}

    def reset_edit_promotions(self, piece_sets: dict[Side, list[type[AbstractPiece]]] | None = None) -> None:
        if find_string('custom', self.edit_piece_set_id, -1):
            self.edit_promotions = {
                side: [piece_type for _, piece_type in self.custom_pieces.items()]
                + [piece_type for k, piece_type in self.past_custom_pieces.items() if k not in self.custom_pieces]
                for side in self.edit_promotions
            }
            return
        if find_string('wall', self.edit_piece_set_id, -1):
            blanks = [''] * (
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
        middle = {side: len(piece_sets[side]) // 2 for side in self.piece_sets}
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
                piece_sets[side][middle[side] - 1::-1], piece_sets[side.opponent()][middle[side.opponent()] - 1::-1],
                piece_sets[side][middle[side] + 1:], piece_sets[side.opponent()][middle[side.opponent()] + 1:],
                [
                    *piece_sets[side.opponent()][middle[side.opponent()]:middle[side.opponent()] + 1],
                    *(opponent_pawns if opponent_pawns is not None else [Pawn]),
                    *(side_pawns if side_pawns is not None else [Pawn]),
                    *piece_sets[side][middle[side]:middle[side] + 1],
                ],
            ):
                promotion_types = []
                for piece in pieces:
                    if piece not in used_piece_set and not issubclass(piece, NoPiece):
                        used_piece_set.add(piece)
                        promotion_types.append(piece)
                self.edit_promotions[side].extend(promotion_types[::-1])

    def reset_penultima_pieces(self, piece_sets: dict[Side, list[type[AbstractPiece]]] | None = None) -> None:
        if piece_sets is None:
            piece_sets = {
                side: self.piece_sets[side]
                for side in self.piece_sets
                if self.piece_set_ids[side] is not None
            }
        self.penultima_pieces = {side: {} for side in self.penultima_pieces}
        for player_side in self.penultima_pieces:
            if not piece_sets.get(player_side):
                continue
            for piece_side in (player_side, player_side.opponent()):
                if not piece_sets.get(piece_side):
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
                self.areas[side][name] = area or []
            if Pawn.name not in self.areas[side]:
                rows = range(2) if side == Side.WHITE else range(self.board_height - 2, self.board_height)
                self.areas[side][Pawn.name] = {
                    self.get_relative((row, col)) for row in rows for col in range(self.board_width)
                }

    def reset_turn_order(self) -> None:
        start_turns, loop_turns = [], []
        start_ended = False
        def to_move(s: str) -> type[BaseMovement] | str:
            t = load_movement_type(s) or s
            return t.type_str() if isinstance(t, type) else t
        def to_type(s: str) -> type[AbstractPiece] | str:
            return action_types.get(s, s)
        t1 = TypeVar('t1')
        def notify(f: Callable[[str], type[t1] | str], s: str) -> type[t1] | str:
            return pch['not'] + f(s[1:]) if s[0:1] == pch['not'] else f(s)
        for i, turn in enumerate(self.custom_turn_order or [(Side.WHITE, [{}]), (Side.BLACK, [{}])]):
            side, rules = turn
            if side == Side.NONE:
                start_ended = True
                continue
            rules = [{}] if rules is None else [copy(rule) for rule in rules]
            for rule in rules:
                for field in default_rules:
                    if field not in rule:
                        rule[field] = default_rules[field]
                    elif not isinstance(default_rules[field], list):
                        rule[field] = unpack(rule[field])
                rule['move'] = [notify(to_move, s) for s in rule['move']]
                rule['type'] = [notify(to_type, s) for s in rule['type']]
                for field in default_sub_rules:
                    rule[field] = [copy(sub_rule) for sub_rule in rule[field]]
                    for sub_rule in rule[field]:
                        sub_rules = default_sub_rules[field]
                        for sub_field in sub_rules:
                            if sub_field not in sub_rule:
                                sub_rule[sub_field] = sub_rules[sub_field]
                            elif not isinstance(sub_rules[sub_field], list):
                                sub_rule[sub_field] = unpack(sub_rule[sub_field])
                        if field in ('last', 'next'):
                            sub_rule['move'] = [notify(to_move, s) for s in sub_rule['move']]
                            sub_rule['type'] = [notify(to_type, s) for s in sub_rule['type']]
            (loop_turns if start_ended else start_turns).append((side, rules))
        if start_turns and not loop_turns and not start_ended:
            start_turns, loop_turns = loop_turns, start_turns
        self.initial_turns = len(start_turns)
        self.turn_order = start_turns + loop_turns

    def reset_end_rules(self) -> None:
        self.royal_types = {}
        self.end_rules = {}
        self.end_data = {}
        for side in [Side.WHITE, Side.BLACK] + ([Side.NONE] if Side.NONE in self.custom_end_rules else []):
            self.end_rules[side] = {}
            if side != side.NONE:
                self.end_data[side] = {}
                self.royal_types[side] = {}
                side_rules = [self.custom_end_rules.get(side, {}), self.custom_end_rules]
            else:
                side_rules = [self.custom_end_rules.get(side, {})]
            for rule_set in side_rules:
                for condition, rules in rule_set.items():
                    if isinstance(condition, Side):
                        continue
                    invert, keyword = (True, condition[1:]) if condition[0:1] == pch['not'] else (False, condition)
                    is_area = True
                    if keyword in end_types:
                        keyword = end_types[keyword]
                        is_area = False
                    elif keyword not in self.areas.get(side, {}) and not isa(keyword):
                        continue
                    condition = pch['not'] + keyword if invert else keyword
                    if isinstance(rules, dict):
                        if keyword == 'checkmate':
                            self.end_rules[side].setdefault(condition, {}).setdefault('', 1)
                            if side != side.NONE:
                                self.end_data[side].setdefault(condition, {}).setdefault('', 0)
                        for group, value in rules.items():
                            self.end_rules[side].setdefault(condition, {}).setdefault(group, value)
                            if side != side.NONE and not is_area:
                                self.end_data[side].setdefault(condition, {}).setdefault(group, 0)
                    elif is_area:
                        self.end_rules.setdefault(side, {}).setdefault(condition, {}).setdefault('', rules)
                    else:
                        self.end_rules.setdefault(side, {}).setdefault(condition, {}).setdefault('', rules)
                        if side != side.NONE:
                            self.end_data.setdefault(side, {}).setdefault(condition, {}).setdefault('', 0)
            if side is Side.NONE:
                continue
            for condition, condition_data in default_end_rules.items():
                if condition not in self.end_rules[side]:
                    if condition == 'checkmate':
                        if 'capture' in self.end_rules[side]:
                            continue
                    self.end_rules[side][condition] = {}
                    self.end_data[side][condition] = {}
                    for group, group_data in condition_data.items():
                        group_exists = group == '' or group in (
                            *self.piece_groups, *(piece.name for piece in self.piece_sets[side])
                        )
                        if group_exists:
                            self.end_rules[side][condition][group] = group_data
                            self.end_data[side][condition][group] = 0

    def get_piece_sets(
        self,
        piece_set_ids: dict[Side, int] | int | None = None
    ) -> tuple[dict[Side, list[type[AbstractPiece]]], dict[Side, str]]:
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

    def get_random_set(self, side: Side, asymmetrical: bool = False) -> tuple[list[type[AbstractPiece]], str]:
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
        piece_set: list[type[AbstractPiece]] = [NoPiece] * default_board_width
        for i, group in enumerate(random_set_poss):
            random_set_ids = self.chaos_rng.sample(piece_set_ids, k=len(group))
            for j, poss in enumerate(group):
                for pos in poss:
                    piece_set[pos] = get_set_data(side, random_set_ids[j])[pos]
        return piece_set, get_set_name(piece_set)

    def get_extremely_random_set(self, side: Side, asymmetrical: bool = False) -> tuple[list[type[AbstractPiece]], str]:
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
        piece_set: list[type[AbstractPiece]] = [NoPiece] * default_board_width
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

    def get_chaos_set(self, side: Side) -> tuple[list[type[AbstractPiece]], str]:
        asymmetrical = self.chaos_mode in {2, 4}
        if self.chaos_mode in {1, 2}:
            return self.get_random_set(side, asymmetrical)
        if self.chaos_mode in {3, 4}:
            return self.get_extremely_random_set(side, asymmetrical)
        return [NoPiece] * default_board_width, '-'  # ideally should never happen

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
        self.chaos_seed = self.chaos_rng.randint(0, self.board_config['max_seed'])
        self.chaos_rng = Random(self.chaos_seed)
        self.piece_set_ids = {Side.WHITE: -1, Side.BLACK: -1 if same else -2}
        self.reset_custom_data()
        self.reset_board()

    def get_royal_group(self, piece: TypeOr[AbstractPiece], side: Side, conditions: set | None = None) -> str:
        return self.get_royal_state(piece, side, conditions)[0]

    def get_royal_type(self, piece: TypeOr[AbstractPiece], side: Side, conditions: set | None = None) -> int:
        return self.get_royal_state(piece, side, conditions)[1]

    def get_royal_value(self, piece: TypeOr[AbstractPiece], side: Side, conditions: set | None = None) -> int | str:
        return self.get_royal_state(piece, side, conditions)[2]

    def get_royal_state(
        self,
        piece: TypeOr[AbstractPiece],
        side: Side,
        conditions: set | None = None
    ) -> tuple[str, int, int | str]:
        if conditions is None:
            conditions = {'check', 'checkmate', 'capture'}
        conditions = {'check', 'checkmate', 'capture'}.intersection(conditions)
        if not conditions:
            return '', 0, 0
        piece_type = piece if isinstance(piece, type) else type(piece)
        royal_types = self.royal_types.setdefault(side, {}).setdefault(piece_type, {})
        opponent = side.opponent()
        end_rules = self.end_rules[opponent]
        if not end_rules:
            return '', 0, 0
        for condition in end_rules:
            invert, keyword = (True, condition[1:]) if condition[0:1] == pch['not'] else (False, condition)
            if keyword in conditions:
                if keyword in royal_types:
                    return royal_types[keyword]
                for group, value in end_rules.get(condition, {}).items():
                    if self.fits(group, piece):
                        return royal_types.setdefault(keyword, (group, (-1 if invert else 1), value))
        return '', 0, 0

    def in_area(self, area: str, pos: GenericPosition, of: Side = Side.NONE, last: list[GenericPosition] = ()) -> bool:
        if area == ANY:  # all squares on the board, guaranteed to be True
            return True
        if of in self.areas:  # try side-specific areas first
            if area == '':  # any side-specific area on the board
                return any(pos in a for _, a in self.areas[of].items())
            if area in self.areas[of]:  # a side-specific area on the board
                return pos in self.areas[of][area]
        # try side-neutral areas next
        if area == '':  # any side-neutral area on the board
            return any(pos in a for _, a in self.custom_areas.items() if isinstance(a, set))
        if area in self.custom_areas and isinstance(self.custom_areas[area], set):  # a side-neutral area on the board
            return pos in self.custom_areas[area]
        try:  # treating as notation (possibly generic)
            return any(all(i in {ANY, j} for i, j in zip(res(fra(area), last_pos), pos)) for last_pos in (None, *last))
        except ValueError:  # if all else fails...
            return False

    def get_area_rules(self, offset: int = 0, origin: int | None = None):
        turn_rules = self.get_turn_rules(offset, origin)
        full_rules = {}
        defaults = default_sub_rules.get('at')
        for rule_data in turn_rules:
            if 'at' not in rule_data:
                continue
            for condition in rule_data['at']:
                get_default = lambda x: condition.get(x, defaults.get(x))
                value = get_default('count')
                templates, sides = get_default('side'), set()
                all_sides = {Side.WHITE, Side.BLACK, Side.NEUTRAL}
                for template in templates:
                    if template == pch['any']:
                        sides.update(all_sides)
                        break
                    for side in all_sides:
                        if side not in sides and self.fits(template, side):
                            sides.add(side)
                for side in sides:
                    side_rules = full_rules.setdefault(side, {})
                    areas = get_default('at')
                    for area in areas:
                        area_rules = side_rules.setdefault(area, {})
                        pieces = get_default('piece')
                        for piece in pieces:
                            area_rules.setdefault(piece, value)
        return full_rules

    def get_area_groups(
        self, piece: AbstractPiece, side: Side, extra_rules: dict | None = None
    ) -> list[tuple[str, str]]:
        end_rules = self.end_rules[side]
        extra_rules = (extra_rules or {}).get(side, {})
        groups = []
        for rule_dict in (end_rules, extra_rules):
            for condition in rule_dict:
                invert, keyword = (True, condition[1:]) if condition[0:1] == pch['not'] else (False, condition)
                if rule_dict is end_rules and keyword in {'check', 'checkmate', 'capture', 'stalemate'}:
                    continue
                if self.in_area(keyword, piece.board_pos, side) == invert:
                    continue
                for group, value in rule_dict.get(condition, {}).items():
                    if group == '' or self.fits(group, piece):
                        groups.append((condition, group))
        return groups

    def get_new_area_count(self, area: str, group: str, side: Side, max_count: int = 0) -> int:
        if not self.move_history:
            return 0
        invert, area = (True, area[1:]) if area[0:1] == pch['not'] else (False, area)
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
            if self.in_area(area, move.pos_to, side) != invert:
                if group == '' or self.fits(group, piece):
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
        self.auto_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.obstacles = []
        royal_types = {Side.WHITE: {}, Side.BLACK: {}}
        royal_values = {Side.WHITE: {}, Side.BLACK: {}}
        turn_area_rules = self.get_area_rules()
        for row, col in product(range(self.board_height), range(self.board_width)):
            piece = self.get_piece(self.get_relative((row, col)))
            if isinstance(piece, Shared):
                sides = (Side.WHITE, Side.BLACK)
            elif not isinstance(piece, NoPiece):
                sides = piece.side,
            else:
                sides = ()
            for side in sides:
                if side in self.movable_pieces:
                    self.movable_pieces[side].append(piece)
                    for group in self.piece_limits.get(side, self.piece_limits):
                        if self.fits(group, piece):
                            self.piece_counts[side][group] = self.piece_counts[side].get(group, 0) + 1
                    for area, group in self.get_area_groups(piece, side, turn_area_rules):
                        self.area_groups[side].setdefault(area, {}).setdefault(group, []).append(piece)
                    royal_group, royal_type, royal_value = self.get_royal_state(piece, side)
                    if royal_type:
                        self.royal_groups[side].setdefault(royal_group, []).append(piece)
                        royal_types[side][royal_group] = royal_type
                        royal_values[side][royal_group] = royal_value
                    if isinstance(piece.movement, ProbabilisticMovement):
                        self.probabilistic_pieces[side].append(piece)
                    if isinstance(piece.movement, AutoMarkMovement):
                        self.auto_pieces[side].append(piece)
                elif isinstance(piece, Obstacle):
                    self.obstacles.append(piece)
        for side, data in self.royal_groups.items():
            for group, pieces in data.items():
                royal_type, royal_value = royal_types[side][group], royal_values[side][group]
                if isinstance(royal_value, int) or (len(pieces) == 1 and royal_value in {'+', '-'}):
                    if royal_type > 0:
                        self.royal_pieces[side].extend(pieces)
                    elif royal_type < 0:
                        self.anti_royal_pieces[side].extend(pieces)
        for side in (Side.WHITE, Side.BLACK):
            self.royal_markers[side] = {piece.board_pos for piece in self.royal_pieces[side]}
            self.anti_royal_markers[side] = {piece.board_pos for piece in self.anti_royal_pieces[side]}
        if self.ply_count == 1:
            for side in self.auto_pieces:
                if self.auto_pieces[side] and not self.auto_markers[side]:
                    self.load_auto_markers(side)

    def get_royal_loss(self, side: Side, move: Move, conditions: set) -> set:
        if not move or move.is_edit or not conditions:
            return set()
        piece_loss = set()
        piece_gain = set()
        royal_groups = self.royal_groups.get(side, {})
        is_royal_loss = lambda g, t, v: g and t and (isinstance(v, int) or not royal_groups.get(g))
        while move:
            for capture in move.captured:
                if capture.side == side:
                    royal_group, royal_type, royal_value = self.get_royal_state(capture, side, conditions)
                    if is_royal_loss(royal_group, royal_type, royal_value):
                        (piece_loss if royal_type > 0 else piece_gain).add(royal_group)
            if move.promotion or move.pos_to is None:
                if move.piece and move.piece.side == side:
                    royal_group, royal_type, royal_value = self.get_royal_state(move.piece, side, conditions)
                    if is_royal_loss(royal_group, royal_type, royal_value):
                        (piece_loss if royal_type > 0 else piece_gain).add(royal_group)
            if move.promotion and move.promotion.side == side:
                royal_group, royal_type, royal_value = self.get_royal_state(move.promotion, side, conditions)
                if is_royal_loss(royal_group, royal_type, royal_value):
                    (piece_loss if royal_type < 0 else piece_gain).add(royal_group)  # NB: sign matters!
                if move.placed_piece:
                    royal_group, royal_type, royal_value = self.get_royal_state(move.placed_piece, side, conditions)
                    if is_royal_loss(royal_group, royal_type, royal_value):
                        (piece_loss if royal_type > 0 else piece_gain).add(royal_group)
            move = move.chained_move
        if move is Unset:
            return set()  # the chain has not finished yet. who knows, maybe we will gain a new royal piece later on
        piece_loss.difference_update(piece_gain)
        return piece_loss

    def load_check(self, for_side: Side | None = None):
        # Can any of the side's royal pieces be captured by the opponent,
        # and are any of the side's anti-royal pieces safe from captures?
        # When side is not specified, checks for the side that moves now.
        side = for_side if isinstance(for_side, Side) else self.turn_side
        self.check_side = Side.NONE
        self.check_groups = set()
        if self.edit_mode:
            return
        opponent = side.opponent()
        self.load_theoretical_moves(opponent, False)
        threat_dict = self.threats.get(opponent, {})
        if not threat_dict:
            return
        if not set(ext(('check', 'checkmate'))).intersection(self.end_rules[opponent]):
            return
        if (
            not set(ext(('check',))).intersection(self.end_rules[opponent])
            and not (self.royal_pieces[side] or self.anti_royal_pieces[side])
        ):
            return
        end_rules = self.end_rules[opponent]
        end_data = self.end_data.get(opponent)
        royal_groups = [
            group for group in self.royal_groups[side]
            if group in end_rules.get('check', {})
            or (
                group in end_rules.get('checkmate', {}) and (
                    (need := end_rules.get('checkmate', {})[group]) in {'+', '-'} or isinstance(need, int)
                    and need * sign(need) - end_data.get('checkmate', {}).get(group, 0) <= 1
               )
            )
        ]
        anti_royal_groups = [
            group for group in self.royal_groups[side]
            if group in end_rules.get('!check', {})
            or (
                group in end_rules.get('!checkmate', {}) and (
                    (need := end_rules.get('!checkmate', {})[group]) in {'+', '-'} or isinstance(need, int)
                    and need * sign(need) - end_data.get('!checkmate', {}).get(group, 0) <= 1
               )
            )
        ]
        if not royal_groups and not anti_royal_groups:
            return
        royal_groups, anti_royal_groups = deduplicate(royal_groups), deduplicate(anti_royal_groups)
        safe_royal_groups, safe_anti_royal_groups = set(royal_groups), set(anti_royal_groups)
        all_royal_groups = safe_royal_groups.copy()
        anti_royal_checks = {}
        royal_group = lambda of: self.get_royal_group(of, side, {'check', 'checkmate'})
        insert = lambda group, pos: anti_royal_checks.setdefault(group, set()).add(pos)
        threat_moves = {}
        self.ply_simulation += 1
        for royal_pos in self.royal_markers[side] | self.anti_royal_markers[side]:
            royal = self.get_piece(royal_pos)
            group = royal_group(royal)
            if group not in safe_royal_groups and group not in safe_anti_royal_groups:
                continue
            # we need to check for royal e.p. captures here as well to avoid castling through check
            # but if the royal piece can be captured e.p. after a specific move, we need to check for that too
            # therefore, checking both e.p. target dicts is necessary (albeit redundant for most cases)
            marker_poss = [royal_pos]
            for target_dict in self.en_passant_targets, self.royal_ep_targets:
                marker_poss.extend(target_dict.get(side, {}).get(royal_pos, ()))
            for piece_pos in chain.from_iterable(threat_dict.get(marker_pos, []).copy() for marker_pos in marker_poss):
                piece = self.get_piece(piece_pos)
                if isinstance(piece.movement, ProbabilisticMovement):
                    continue
                if piece.board_pos in threat_moves:
                    moves_checked, moves = True, threat_moves[piece.board_pos]
                else:
                    moves_checked, moves = False, piece.moves()
                for move in moves:
                    chained_move = move
                    while chained_move:
                        if not chained_move.swapped_piece:
                            if chained_move.pos_to == royal_pos:
                                if group in safe_royal_groups:
                                    safe_royal_groups.discard(group)
                                if group in safe_anti_royal_groups:
                                    insert(group, chained_move.pos_to)
                                    if len(anti_royal_checks[group]) == len(self.royal_groups[side].get(group, ())):
                                        safe_anti_royal_groups.discard(group)
                            if not safe_royal_groups and not safe_anti_royal_groups:
                                break
                        for capture in chained_move.captured:
                            if capture.side == side:
                                if capture.board_pos == chained_move.pos_to:
                                    pass  # capture by displacement should be covered by the previous checks
                                elif capture.board_pos in self.royal_markers[side]:
                                    taken = royal_group(capture)
                                    if taken in safe_royal_groups:
                                        safe_royal_groups.discard(taken)
                                elif capture.board_pos in self.anti_royal_markers[side]:
                                    taken = royal_group(capture)
                                    if taken in safe_anti_royal_groups:
                                        insert(taken, capture.board_pos)
                                        if len(anti_royal_checks[taken]) == len(self.royal_groups[side].get(taken, ())):
                                            safe_anti_royal_groups.discard(taken)
                                if not safe_royal_groups and not safe_anti_royal_groups:
                                    break
                        chained_move = chained_move.chained_move
                    if not safe_royal_groups and not safe_anti_royal_groups:
                        break
                    if not moves_checked:
                        threat_moves.setdefault(piece.board_pos, []).append(move)
                if not safe_royal_groups and not safe_anti_royal_groups:
                    break
            if not safe_royal_groups and not safe_anti_royal_groups:
                break
        self.ply_simulation -= 1
        self.check_groups = []
        self.check_groups.extend(all_royal_groups.difference(safe_royal_groups))
        self.check_groups.extend(safe_anti_royal_groups)
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
                    if isinstance(side_needs, str) and side_needs[-1:] == pch['not']:
                        side_needs = side_needs[:-1] or '1'
                if side_needs in {'+', '-'}:
                    side_needs = side_needs + '1'
                side_needs = int(side_needs)
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
                        if isinstance(other_needs, str) and other_needs[-1:] == pch['not']:
                            other_needs = other_needs[:-1] or '1'
                    if other_needs in {'+', '-'}:
                        other_needs = other_needs + '1'
                    other_needs = int(other_needs)
                    if 0 < other_needs <= other_count:
                        loss_side, loss_value, loss_group = side, other_needs, group
                    if 0 > other_needs >= -other_count:
                        loss_side, loss_value, loss_group = opponent, -other_needs, group
                    if 0 == other_needs and other_count:
                        draw = True
                if win_side and not loss_side and not draw:
                    if condition not in self.end_data[side]:
                        side_needs = self.end_rules[side][condition][group]
                        if isinstance(side_needs, str) and side_needs[-1:] == pch['not']:
                            side_needs = side_needs[:-1] or '1'
                            if side_needs in {'+', '-'}:
                                side_needs = side_needs + '1'
                            side_needs = int(side_needs)
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
            resolution_rules = self.end_rules.get(Side.NONE, {}).get(condition, {})
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
                self.game_over, self.end_condition = True, condition.removeprefix(pch['not'])
                if win_side:
                    self.win_side, self.end_group, self.end_value = win_side, win_group, win_value
                elif loss_side:
                    self.win_side, self.end_group, self.end_value = loss_side.opponent(), loss_group, loss_value
                return

    def load_theoretical_moves(self, side: Side | None = None, update: bool = True) -> None:
        def is_changing(movement: BaseMovement) -> bool:
            if isinstance(movement, ChangingMovement):
                return True
            elif isinstance(movement, ChangingLegalMovement):
                return update
            elif isinstance(movement, BaseMultiMovement):
                return any(is_changing(m) for m in movement.movements)
            return False
        if side not in self.theoretical_moves:
            self.theoretical_moves[side] = {}
        if side not in self.threats:
            self.threats[side] = {}
        for piece in self.movable_pieces[side][:]:
            if piece.board_pos in self.theoretical_moves[side]:
                if is_changing(piece.movement):
                    self.clear_theoretical_moves(side, piece.board_pos)
                else:
                    continue
            for move in piece.moves(theoretical=True):
                pos_from, pos_to = move.pos_from, move.pos_to or move.pos_from
                self.theoretical_moves[side].setdefault(pos_from, {}).setdefault(pos_to, []).append(move)
                if 'a' in move.marks:
                    continue
                self.threats[side].setdefault(pos_to, set()).add(pos_from)

    def clear_theoretical_moves(self, side: Side | None = None, poss: Unpacked[Position] | None = None) -> None:
        if side is None:
            sides = [Side.WHITE, Side.BLACK]
        else:
            sides = [side]
        clear_all = poss is None
        if isinstance(poss, tuple):
            poss = [poss]
        for side in sides:
            if side not in self.theoretical_moves:
                continue
            threats = self.threats.get(side, {})
            if clear_all:
                poss = list(self.theoretical_moves[side])
            for pos in poss:
                moves = self.theoretical_moves[side].pop(pos, ())
                for pos_to in moves:
                    if pos_to in threats:
                        threats[pos_to].discard(pos)
                        if not threats[pos_to]:
                            del threats[pos_to]

    def load_moves(
        self,
        force_reload: bool = True,
        moves_for: Side | None = None,
        theoretical_moves_for: Side | None = None
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
        self.update_caption(string="Loading moves...", force=True)
        if force_reload:
            self.game_over = False
            self.end_value = 0
            self.end_group = None
            self.end_condition = None
            self.win_side = Side.NONE
            self.moves_queried = {side: False for side in self.moves_queried}
            self.load_end_conditions()
            if self.game_over and self.win_side is not Side.NONE:
                losing_side = self.win_side.opponent()
                self.moves[losing_side] = {}
                self.moves_queried[losing_side] = True
        # check if the cached piece data matches the current board state, and only update the former if it doesn't
        pieces_loaded = True  # generally speaking, Board.load_pieces() should always be called before this method
        # NB: whenever the board state changes, set the above variable to False forcing a reload after state reset
        # NB: whenever the cached piece data for the current state is reloaded, set to True to reduce reload count
        movable_pieces = {side: self.movable_pieces[side].copy() for side in self.movable_pieces}
        piece_counts = {side: self.piece_counts[side].copy() for side in self.piece_counts}
        area_groups = {side: self.area_groups[side].copy() for side in self.area_groups}
        royal_groups = {side: self.royal_groups[side].copy() for side in self.royal_groups}
        royal_pieces = {side: self.royal_pieces[side].copy() for side in self.royal_pieces}
        royal_markers = {side: self.royal_markers[side].copy() for side in self.royal_markers}
        anti_royal_pieces = {side: self.anti_royal_pieces[side].copy() for side in self.anti_royal_pieces}
        anti_royal_markers = {side: self.anti_royal_markers[side].copy() for side in self.anti_royal_markers}
        probabilistic_pieces = {side: self.probabilistic_pieces[side].copy() for side in self.probabilistic_pieces}
        auto_pieces = {side: self.auto_pieces[side].copy() for side in self.auto_pieces}
        auto_markers = deepcopy(self.auto_markers)
        auto_markers_theoretical = deepcopy(self.auto_markers_theoretical)
        en_passant_targets = deepcopy(self.en_passant_targets)
        en_passant_markers = deepcopy(self.en_passant_markers)
        royal_ep_targets = deepcopy(self.royal_ep_targets)
        royal_ep_markers = deepcopy(self.royal_ep_markers)
        end_data = deepcopy(self.end_data)
        opponent = self.turn_side.opponent()
        check_side = self.check_side
        check_sides = {check_side: True if check_side and check_side is not Side.NONE else False}
        check_groups = copy(self.check_groups)
        last_chain_move = self.chain_start
        if last_chain_move:
            chained_move = last_chain_move
            while chained_move.chained_move:
                if not issubclass(
                    chained_move.movement_type or type, (CastlingPartnerMovement, CloneMovement, AutoActMovement)
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
        self.display_theoretical_moves = {side: False for side in self.display_theoretical_moves}
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
            if turn_side == self.turn_side and probabilistic_pieces.get(turn_side):
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
            order_groups = {}
            for any_rule in self.turn_rules:
                order_groups.setdefault(any_rule['order'], []).append(any_rule)
            for order_group in sorted(order_groups, reverse=True):
                order_rules = order_groups[order_group]
                area_rules = []
                defaults = default_sub_rules.get('at')
                for order_rule in order_rules:
                    if order_rule.get('at'):
                        match = False
                        if not pieces_loaded:
                            self.load_pieces()
                            pieces_loaded = True
                        for condition in order_rule['at']:
                            match = False
                            get_default = lambda x: condition.get(x, defaults.get(x))
                            count = get_default('count')
                            total = 0
                            templates, sides = get_default('side'), set()
                            all_sides = {Side.WHITE, Side.BLACK, Side.NEUTRAL}
                            for template in templates:
                                if template == pch['any']:
                                    sides.update(all_sides)
                                    break
                                for side in all_sides:
                                    if side not in sides and self.fits(template, side):
                                        sides.add(side)
                            for side in sides:
                                for area in get_default('at'):
                                    for piece in get_default('piece'):
                                        total += len(self.area_groups.get(side, {}).get(area, {}).get(piece) or ())
                                        # NB: count could be negative! in this case, the rule is treated as its inverse,
                                        # maintaining consistency with the end conditions, where negative goal is a loss
                                        # is this less intuitive than adding an inverse flag to the condition? perchance
                                        # the only real upside is that a minus sign is less verbose than a separate flag
                                        # you'd think this would be enough to define an actually sensible implementation
                                        match = (total < -count) if count < 0 else (total >= count) # and you'd be wrong
                                        if match:
                                            break
                                    if match:
                                        break
                                if match:
                                    break
                            if not match:  # if the condition is not met, stop checking
                                break
                        if not match:  # if a condition is not met, skip the rule
                            continue
                    area_rules.append(order_rule)
                state_groups = {}
                for area_rule in area_rules:
                    state_groups.setdefault(area_rule['state'], []).append(area_rule)
                if set(ext(('check', 'checkmate'))).intersection(self.end_rules[turn_side]):
                    old_check_side = self.check_side
                    old_check_groups = copy(self.check_groups)
                    if opponent not in check_sides:
                        if {-opponent.value, opponent.value}.intersection(state_groups):
                            if not pieces_loaded:
                                self.load_pieces()
                                pieces_loaded = True
                            self.load_check(opponent)
                            if self.check_side == opponent:
                                check_sides[opponent] = True
                    self.check_side = old_check_side
                    self.check_groups = old_check_groups
                state_rules = list(chain.from_iterable(state_groups.get(k, ()) for k in (
                    0, *(side.value * (-1 if check_sides.get(side, False) else 1) for side in [Side.WHITE, Side.BLACK])
                )))  # 0: any state, +side: side not in check, -side: side in check
                if not state_rules:
                    continue
                last_history_rules = state_rules.copy()
                for rule in last_history_rules:
                    rule['match'] = {}
                if self.move_history:
                    last_history_moves = {}
                    depths = {by for rule in state_rules for last in rule['last'] for by in last['by']}
                    starts, finals = set(), set()
                    _ = [(starts.add(-x) if x < 0 else finals.add(x)) for x in depths]
                    min_index, max_index = min(starts, default=0), max(starts, default=0)
                    i = 1
                    for last_history_move in self.move_history:
                        if i > max_index:
                            break
                        if last_history_move and last_history_move.is_edit:
                            continue
                        if i in starts:
                            last_history_moves[-i] = last_history_move
                        i += 1
                    min_depth, max_depth = min(finals, default=0), max(finals, default=0)
                    i = int(not self.chain_start)
                    for last_history_move in self.move_history[::-1]:
                        if i > max_depth:
                            break
                        if last_history_move and last_history_move.is_edit:
                            continue
                        if i in finals:
                            last_history_moves[i] = last_history_move
                        i += 1
                    for i in sorted(last_history_moves, key=lambda x: (sign(x), -x)):
                        last_history_move = last_history_moves[i]
                        if last_history_move and last_history_move.is_edit:
                            continue
                        old_history_rules = last_history_rules
                        last_history_rules, history_rules = [], []
                        for rule in old_history_rules:
                            if i in {by for last in rule['last'] for by in last['by']}:
                                history_rules.append(rule)
                            else:
                                last_history_rules.append(rule)
                        if not last_history_move:
                            history_rules = self.filter(
                                history_rules, ('last', 'type'), ['pass'], ('match', 'type'), False
                            )
                            for rule in history_rules:
                                rule['match'].setdefault('type', set()).add('pass')
                            last_history_rules += history_rules
                        elif last_history_move.is_edit:
                            continue
                        while last_history_move:
                            side = self.get_turn_side(-i)
                            drop = promotion = False
                            if isinstance(last_history_move.piece, NoPiece) or not last_history_move.pos_from:
                                piece = last_history_move.promotion or last_history_move.piece
                                drop = issubclass(last_history_move.movement_type or type, DropMovement)
                            else:
                                piece = last_history_move.piece
                                promotion = last_history_move.promotion
                            history_rules = self.filter(
                                history_rules, ('last', 'piece'), [type(piece)], ('match', 'piece')
                            )
                            for rule in history_rules:
                                rule['match'].setdefault('piece', set()).add(type(piece))
                            history_rules = self.filter(
                                history_rules, ('last', 'move'), [last_history_move], ('match', 'move')
                            )
                            for rule in history_rules:
                                rule['match'].setdefault('move', []).append(last_history_move)
                            move_types = [s for s in (
                                'move' if not last_history_move.captured else 'capture',
                                'promotion' if promotion else None,
                                'drop' if drop else None,
                            ) if s]
                            history_rules = self.filter(
                                history_rules, ('last', 'type'), move_types, ('match', 'type'), False
                            )
                            for rule in history_rules:
                                rule['match'].setdefault('type', set()).update(move_types)
                            for rule in history_rules:
                                rule['match'].setdefault('pos', [])
                            pos_from = last_history_move.pos_from or last_history_move.pos_to
                            pos_to = last_history_move.pos_to or last_history_move.pos_from
                            history_rules = self.filter(
                                history_rules, ('last', 'from'), [(side, pos_from)], ('match', 'pos')
                            )
                            for rule in history_rules:
                                rule['match'].setdefault('pos', []).append(pos_from)
                                rule['match'].setdefault('from', []).append(pos_from)
                            history_rules = self.filter(
                                history_rules, ('last', 'to'), [(side, pos_to)], ('match', 'pos')
                            )
                            for rule in history_rules:
                                rule['match'].setdefault('pos', []).append(pos_to)
                                rule['match'].setdefault('to', []).append(pos_to)
                            history_rules = self.filter(
                                history_rules, ('last', 'old'), [piece.total_moves], ('match', 'old'), False
                            )
                            if captured := last_history_move.captured:
                                capture_type = 'take' if piece.side == turn_side else 'lose'
                                captured_pieces = [type(x) for x in captured]
                                history_rules = self.filter(
                                    history_rules, ('last', capture_type), captured_pieces, ('match', capture_type)
                                )
                                for rule in history_rules:
                                    rule['match'].setdefault(capture_type, set()).update(captured_pieces)
                            if promotion := last_history_move.promotion:
                                history_rules = self.filter(
                                    history_rules, ('last', 'new'), [type(promotion)], ('match', 'piece')
                                )
                                for rule in history_rules:
                                    rule['match'].setdefault('piece', set()).add(type(promotion))
                            else:
                                history_rules = self.filter(history_rules, ('last', 'new'), last=('match', 'piece'))
                            last_history_rules += history_rules
                            last_history_move = last_history_move.chained_move
                        i -= 1
                if not last_history_rules:
                    continue
                piece_rule_dict = {}
                if not self.chain_start and self.use_drops and turn_side in self.drops:
                    side_drops = self.drops[turn_side]
                    for piece_type in self.captured_pieces[turn_side]:
                        if piece_type not in side_drops:
                            continue
                        if piece_type not in piece_rule_dict:
                            piece_rule_dict[piece_type] = self.filter(
                                last_history_rules, 'piece', [piece_type], ('match', 'piece')
                            )
                        if not piece_rule_dict[piece_type]:
                            continue
                        drop_rules = deepcopy(piece_rule_dict[piece_type])
                        for rule in drop_rules:
                            rule['match'].setdefault('piece', set()).add(piece_type)
                        drop_rules = self.filter(drop_rules, 'move', [DropMovement], ('match', 'move'))
                        drop_rules = self.filter(drop_rules, 'type', ['drop'], ('match', 'type'), False)
                        if not drop_rules:
                            continue
                        for pos in side_drops[piece_type]:
                            if not self.not_a_piece(pos):
                                continue
                            pos_rules = self.filter(drop_rules, 'from', [(turn_side, pos)], ('match', 'pos'))
                            pos_rules = self.filter(pos_rules, 'to', [(turn_side, pos)], ('match', 'pos'))
                            if not pos_rules:
                                continue
                            take_rules = self.filter(pos_rules, 'take', last=('match', 'take'))
                            if not take_rules:
                                continue
                            lose_rules = self.filter(take_rules, 'lose', last=('match', 'lose'))
                            if not lose_rules:
                                continue
                            old_rules = self.filter(take_rules, 'old', last=('match', 'old'))
                            if not old_rules:
                                continue
                            drop_types = set()
                            for drop in side_drops[piece_type][pos]:
                                drop_type = type(drop) if isinstance(drop, AbstractPiece) else drop
                                new_rules = self.filter(old_rules, 'new', [drop_type], ('match', 'piece'))
                                if not new_rules:
                                    continue
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
                                else:
                                    drop_types.add(drop_type)
                            # NB: Querying check status after a move is NYI for drop moves
                            if drop_types:
                                drop_dict = self.moves[turn_side].setdefault('drop', {})
                                pos_drop_dict = drop_dict.setdefault(pos, {})
                                pos_drop_dict[piece_type] = drop_types
                for piece in movable_pieces[turn_side] if chain_moves is None else [last_chain_move.piece]:
                    self.move_tags = set()
                    all_tags = False
                    piece_type = type(piece)
                    if piece_type not in piece_rule_dict:
                        piece_rule_dict[piece_type] = self.filter(
                            last_history_rules, 'piece', [piece_type], ('match', 'piece')
                        )
                    if not piece_rule_dict[piece_type]:
                        continue
                    piece_rules = deepcopy(piece_rule_dict[piece_type])
                    for rule in piece_rules:
                        rule['match'].setdefault('piece', set()).add(piece_type)
                    piece_rules = self.filter(piece_rules, 'old', [piece.total_moves], ('match', 'old'), False)
                    if not piece_rules:
                        continue
                    for rule in piece_rules:
                        rule['match'].setdefault('pos', [])
                    piece_pos = piece.board_pos
                    piece_rules = self.filter(piece_rules, 'from', [(turn_side, piece_pos)], ('match', 'pos'))
                    if not piece_rules:
                        continue
                    for rule in piece_rules:
                        rule['match'].setdefault('pos', []).append(piece_pos)
                        rule['match'].setdefault('from', []).append(piece_pos)
                        if all_tags:
                            continue
                        add_last = set()
                        for full_move_tag in rule.get('move', ()):
                            move_tag = full_move_tag
                            invert = move_tag.startswith(pch['not'])
                            move_tag = move_tag[len(pch['not']):] if invert else move_tag
                            if move_tag.startswith(pch['type']):
                                continue
                            if move_tag.startswith(pch['tag']):
                                move_tag = move_tag[len(pch['tag']):]
                            if move_tag == pch['any']:
                                all_tags = True
                                break
                            if move_tag in pch['last']:
                                if not invert in add_last:
                                    all_tags = True
                                    break
                                add_last.add(invert)
                                continue
                            if invert:
                                if move_tag in self.move_tags:
                                    all_tags = True
                                    break
                                move_tag = pch['not'] + move_tag
                            elif pch['not'] + move_tag in self.move_tags:
                                all_tags = True
                                break
                            self.move_tags.add(move_tag)
                        if all_tags:
                            add_last = set()
                        if add_last:
                            for last_move in rule.get('match', {}).get('move', ()):
                                if last_move.tag:
                                    if False in add_last:
                                        if last_move.tag in self.move_tags:
                                            all_tags = True
                                            break
                                        self.move_tags.add(pch['not'] + last_move.tag)
                                    if True in add_last:
                                        if pch['not'] + last_move.tag in self.move_tags:
                                            all_tags = True
                                            break
                                        self.move_tags.add(last_move.tag)
                        if all_tags:
                            self.move_tags = {pch['any']}
                    if not self.chain_start and not self.moves[turn_side].get('pass'):
                        pass_rules = deepcopy(piece_rules)
                        pass_rules = self.filter(pass_rules, 'type', ['pass'], ('match', 'type'), False)
                        pass_rules = self.filter(pass_rules, 'to', [(turn_side, piece_pos)], ('match', 'pos'))
                        for rule in pass_rules:
                            rule['match'].setdefault('pos', []).append(piece_pos)
                            rule['match'].setdefault('to', []).append(piece_pos)
                        pass_rules = self.filter(pass_rules, 'move', last=('match', 'move'))
                        pass_rules = self.filter(pass_rules, 'take', last=('match', 'take'))
                        pass_rules = self.filter(pass_rules, 'lose', last=('match', 'lose'))
                        pass_rules = self.filter(pass_rules, 'new', last=('match', 'piece'))
                        if pass_rules and self.check_side != turn_side:
                            if self.fits_any(pass_rules, 'check', [0], fit=False):
                                self.moves[turn_side]['pass'] = True
                            else:
                                old_check_side = self.check_side
                                old_check_groups = copy(self.check_groups)
                                if opponent not in check_sides:
                                    if not pieces_loaded:
                                        self.load_pieces()
                                        pieces_loaded = True
                                    self.load_check(opponent)
                                    if self.check_side == opponent:
                                        check_sides[opponent] = True
                                check_requirements = [1 if check_sides.get(opponent, False) else -1]
                                if self.fits_any(pass_rules, 'check', check_requirements, fit=False):
                                    self.moves[turn_side]['pass'] = True
                                self.check_side = old_check_side
                                self.check_groups = old_check_groups
                    move_rule_dict = {}
                    for base_move in piece.moves() if chain_moves is None else chain_moves:
                        if not base_move.is_legal:
                            continue
                        move_tag = tuple(self.keys(base_move))
                        if move_tag not in move_rule_dict:
                            move_rule_dict[move_tag] = self.filter(piece_rules, 'move', [base_move], ('match', 'move'))
                        if not move_rule_dict[move_tag]:
                            continue
                        base_rules = deepcopy(move_rule_dict[move_tag])
                        for rule in base_rules:
                            rule['match'].setdefault('move', []).append(base_move)
                        self.update_move(base_move)
                        skip = False
                        for capture in base_move.captured:
                            if capture.board_pos != base_move.pos_to:
                                continue
                            if base_move.piece.skips(capture) and not base_move.piece.captures(capture):
                                skip = True
                                break
                        if skip:
                            continue
                        base_dict = {'move': True, 'capture': False, 'promotion': False}
                        for rule in base_rules:
                            rule['match'].setdefault('pos', [])
                        pos_to = base_move.pos_to or base_move.pos_from
                        base_rules = self.filter(base_rules, 'to', [(turn_side, pos_to)], ('match', 'pos'))
                        for rule in base_rules:
                            rule['match'].setdefault('pos', []).append(pos_to)
                            rule['match'].setdefault('to', []).append(pos_to)
                        if captured := base_move.captured:
                            capture_type = 'take' if base_move.piece.side == turn_side else 'lose'
                            captured_pieces = [type(x) for x in captured]
                            base_rules = self.filter(base_rules, capture_type, captured_pieces, ('match', capture_type))
                            for rule in base_rules:
                                rule['match'].setdefault(capture_type, set()).update(captured_pieces)
                        if not base_rules:
                            continue
                        base_dict['move'] = base_dict['move'] and not base_move.captured
                        base_dict['capture'] = base_dict['capture'] or bool(base_move.captured)
                        for move in ([base_move] if self.chain_start else self.get_promotions(base_move)):
                            move_rules = deepcopy(base_rules)
                            type_dict = copy(base_dict)
                            type_dict['promotion'] = type_dict['promotion'] or bool(move.promotion)
                            move_types = [k for k, v in type_dict.items() if v]
                            move_rules = self.filter(move_rules, 'type', move_types, ('match', 'type'), False)
                            for rule in move_rules:
                                rule['match'].setdefault('type', set()).update(move_types)
                            if not move_rules:
                                continue
                            if move.promotion:
                                promo = move.promotion
                                p_type = type(promo) if isinstance(promo, AbstractPiece) else promo
                                move_rules = self.filter(move_rules, 'new', [p_type], ('match', 'piece'))
                                for rule in move_rules:
                                    rule['match'].setdefault('piece', set()).add(p_type)
                                if not move_rules:
                                    continue
                                if p_type not in limit_hits:
                                    if p_type not in limit_groups:
                                        limit_groups[p_type] = {g for g in limits if self.fits(g, p_type)}
                                    limit_hits[p_type] = False
                                    for g in limit_groups[p_type]:
                                        if self.piece_counts[turn_side].get(g, 0) >= limits[g]:
                                            limit_hits[p_type] = True
                                            break
                                if limit_hits[p_type]:
                                    continue
                            else:
                                move_rules = self.filter(move_rules, 'new', last=('match', 'piece'))
                            if not move_rules:
                                continue
                            move = self.move(move, False)
                            self.update_auto_markers(move, True)
                            move = self.update_auto_actions(move, turn_side.opponent())
                            if isinstance(move.promotion, AbstractPiece):
                                self.promotion_piece = True
                                self.replace(move.piece, move.promotion, move.movement_type, False)
                                move = self.update_promotion_auto_actions(move)
                                self.promotion_piece = None
                            move_chain = [move]
                            chained_move = move.chained_move
                            skip = False
                            legal = True
                            check_or_mate = {'check', 'checkmate'}
                            any_check_or_mate = set(ext(check_or_mate))
                            if (
                                any_check_or_mate.intersection(self.end_rules[turn_side.opponent()])
                                and chained_move and issubclass(type(move.piece), Slow)
                            ):
                                pieces_loaded = False
                                self.load_pieces()
                                if move.piece.board_pos in self.royal_markers[turn_side]:
                                    self.load_check(turn_side)
                                    if self.check_side == turn_side:
                                        legal = False
                            looks = {by for rule in move_rules for next_r in rule['next'] for by in next_r['by']}
                            min_depth, max_depth = min(looks, default=0), max(looks, default=0)
                            j = 1
                            new_limit_groups = {}
                            new_limit_hits = {}
                            next_future_rules = deepcopy(move_rules)
                            while legal and chained_move:
                                self.update_move(chained_move)
                                for capture in chained_move.captured:
                                    if capture.board_pos != chained_move.pos_to:
                                        continue
                                    if chained_move.piece.skips(capture) and not chained_move.piece.captures(capture):
                                        skip = True
                                        legal = False
                                        break
                                if skip:
                                    break
                                if min_depth <= j <= max_depth:
                                    old_future_rules = next_future_rules
                                    next_future_rules, future_rules = [], []
                                    for rule in old_future_rules:
                                        if j in {by for next_r in rule['next'] for by in next_r['by']}:
                                            future_rules.append(rule)
                                        else:
                                            next_future_rules.append(rule)
                                    future_rules = self.filter(
                                        future_rules, ('next', 'piece'), [type(move.piece)], ('match', 'piece')
                                    )
                                    for rule in future_rules:
                                        rule['match'].setdefault('piece', set()).add(type(move.piece))
                                    future_rules = self.filter(
                                        future_rules, ('next', 'move'), [chained_move], ('match', 'move')
                                    )
                                    for rule in future_rules:
                                        rule['match'].setdefault('move', []).append(chained_move)
                                    for rule in future_rules:
                                        rule['match'].setdefault('pos', [])
                                    pos_from = chained_move.pos_from or chained_move.pos_to
                                    pos_to = chained_move.pos_to or chained_move.pos_from
                                    future_rules = self.filter(
                                        future_rules, ('next', 'from'), [(turn_side, pos_from)], ('match', 'pos')
                                    )
                                    for rule in future_rules:
                                        rule['match'].setdefault('pos', []).append(pos_from)
                                        rule['match'].setdefault('from', []).append(pos_from)
                                    future_rules = self.filter(
                                        future_rules, ('next', 'to'), [(turn_side, pos_to)], ('match', 'pos')
                                    )
                                    for rule in future_rules:
                                        rule['match'].setdefault('pos', []).append(pos_to)
                                        rule['match'].setdefault('to', []).append(pos_to)
                                    if chained_move.piece and chained_move.piece.movement:
                                        future_rules = self.filter(
                                            future_rules, ('next', 'old'),
                                            [chained_move.piece.total_moves],
                                            ('match', 'old'), False
                                        )
                                    if loss := chained_move.captured:
                                        loss_type = 'take' if chained_move.piece.side == turn_side else 'lose'
                                        captured_pieces = [type(x) for x in loss]
                                        future_rules = self.filter(
                                            future_rules, ('next', loss_type), captured_pieces, ('match', loss_type)
                                        )
                                        for rule in future_rules:
                                            rule['match'].setdefault(loss_type, set()).update(captured_pieces)
                                    future_dict = {'move': True, 'capture': False, 'promotion': False}
                                    new_piece = None
                                    if not future_rules:
                                        legal = False
                                    elif chained_move:
                                        ch = chained_move
                                        new_piece = new_piece or ch.promotion
                                        future_dict['move'] = future_dict['move'] and not ch.captured
                                        future_dict['capture'] = future_dict['capture'] or bool(ch.captured)
                                        future_dict['promotion'] = future_dict['promotion'] or bool(ch.promotion)
                                        future_types = [k for k, v in future_dict.items() if v]
                                        future_rules = self.filter(
                                            future_rules, ('next', 'type'), future_types, ('match', 'type')
                                        )
                                        for rule in future_rules:
                                            rule['match'].setdefault('type', set()).update(future_types)
                                    if future_rules:
                                        if new_piece:
                                            np = new_piece
                                            p_type = type(np) if isinstance(np, AbstractPiece) else np
                                            future_rules = self.filter(
                                                future_rules, ('next', 'new'), [p_type], ('match', 'piece')
                                            )
                                            for rule in future_rules:
                                                rule['match'].setdefault('piece', set()).add(p_type)
                                            if not future_rules:
                                                legal = False
                                            else:
                                                pieces_loaded = False
                                                self.load_pieces()  # update piece counts
                                                if p_type not in new_limit_hits:
                                                    if p_type not in new_limit_groups:
                                                        new_limit_groups[p_type] = [
                                                            g for g in limits if self.fits(g, p_type)
                                                        ]
                                                    new_limit_hits[p_type] = [
                                                        self.piece_counts[turn_side].get(g, 0)
                                                        for g in new_limit_groups[p_type]
                                                    ]
                                                for g in new_limit_groups[p_type]:
                                                    if self.piece_counts[turn_side].get(g, 0) >= limits[g]:
                                                        new_limit_hits[p_type] = True
                                                        break
                                                if new_limit_hits[p_type]:
                                                    legal = False
                                        else:
                                            future_rules = self.filter(
                                                future_rules, ('next', 'new'), last=('match', 'piece')
                                            )
                                    next_future_rules += future_rules
                                if legal:
                                    chained_move = self.move(chained_move, False)
                                    if isinstance(chained_move.promotion, AbstractPiece):
                                        self.promotion_piece = True
                                        self.replace(
                                            chained_move.piece, chained_move.promotion,
                                            chained_move.movement_type, False,
                                        )
                                        chained_move = self.update_promotion_auto_actions(chained_move)
                                        self.promotion_piece = None
                                    else:
                                        self.update_auto_markers(chained_move)
                                    move_chain[-1].chained_move = chained_move
                                    move_chain.append(chained_move)
                                    if (
                                        any_check_or_mate.intersection(self.end_rules[turn_side.opponent()])
                                        and chained_move and issubclass(type(move.piece), Slow)
                                    ):
                                        pieces_loaded = False
                                        self.load_pieces()
                                        if move.piece.board_pos in self.royal_markers[turn_side]:
                                            self.load_check(turn_side)
                                            if self.check_side == turn_side:
                                                legal = False
                                if legal:
                                    chained_move = chained_move.chained_move
                                    j += 1
                            move_rules = next_future_rules
                            if legal:
                                pieces_loaded = False
                                self.load_pieces()
                                self.load_check(turn_side)
                                if self.check_side == turn_side:
                                    legal = False
                            if legal:
                                if any_check_or_mate.intersection(self.end_rules[turn_side.opponent()]):
                                    for g in self.get_royal_loss(turn_side, move, check_or_mate):
                                        for condition in self.end_rules.get(turn_side.opponent(), {}):
                                            if condition in any_check_or_mate:
                                                n = self.end_rules[turn_side.opponent()][condition].get(g, 0)
                                                v = self.end_data.get(turn_side.opponent(), {}).get(condition, {})
                                                if n == '+':
                                                    legal = False
                                                elif isinstance(n, int) and n > 0 and n - v.get(g, 0) <= 1:
                                                    legal = False
                                            if not legal:
                                                break
                                        if not legal:
                                            break
                            if legal:
                                if any_check_or_mate.intersection(self.end_rules[turn_side]):
                                    for g in self.get_royal_loss(turn_side.opponent(), move, check_or_mate):
                                        for condition in self.end_rules.get(turn_side, {}):
                                            if condition in any_check_or_mate:
                                                n = self.end_rules[turn_side][condition].get(g, 0)
                                                v = self.end_data.get(turn_side, {}).get(condition, {})
                                                if n == '-':
                                                    legal = False
                                                elif isinstance(n, int) and n < 0 and n + v.get(g, 0) >= -1:
                                                    legal = False
                                            if not legal:
                                                break
                                        if not legal:
                                            break
                            p_not = pch['not']
                            mate = ext(('checkmate',))
                            if not skip and not any(end_data[self.turn_side].get(x, {}).get('', 0) for x in mate):
                                if any_check_or_mate.intersection(self.end_rules[self.turn_side]):
                                    for g in self.get_royal_loss(opponent, move, check_or_mate):
                                        for condition in self.end_rules.get(self.turn_side, {}):
                                            if condition in any_check_or_mate:
                                                n = self.end_rules[self.turn_side][condition].get(g, 0)
                                                v = self.end_data.get(self.turn_side, {}).get(condition, {})
                                                in_check = False
                                                if n == '+':
                                                    in_check = True
                                                elif isinstance(n, int) and n > 0 and n - v.get(g, 0) <= 1:
                                                    in_check = True
                                                if in_check:
                                                    self.moves[opponent] = {}
                                                    self.moves_queried[opponent] = True
                                                    p = p_not if (condition[0:1] == p_not) else ''
                                                    loss_condition = p + 'checkmate'
                                                    end_data[self.turn_side][loss_condition][''] = 1
                            if not skip and not any(end_data[self.turn_side].get(x, {}).get('', 0) for x in mate):
                                if any_check_or_mate.intersection(self.end_rules[opponent]):
                                    for g in self.get_royal_loss(self.turn_side, move, check_or_mate):
                                        for condition in self.end_rules.get(opponent, {}):
                                            if condition in any_check_or_mate:
                                                n = self.end_rules[opponent][condition].get(g, 0)
                                                v = self.end_data.get(opponent, {}).get(condition, {})
                                                in_check = False
                                                if n == '-':
                                                    in_check = True
                                                elif isinstance(n, int) and n < 0 and n + v.get(g, 0) >= -1:
                                                    in_check = True
                                                if in_check:
                                                    self.moves[opponent] = {}
                                                    self.moves_queried[opponent] = True
                                                    p = p_not if (condition[0:1] == p_not) else ''
                                                    loss_condition = p + 'checkmate'
                                                    end_data[self.turn_side][loss_condition][''] = 1
                            if legal:
                                move_fits = self.fits_any(move_rules, 'check', [0], fit=False)
                                if move_rules and not move_fits:
                                    old_check_side = self.check_side
                                    old_check_groups = copy(self.check_groups)
                                    pieces_loaded = False
                                    self.load_pieces()
                                    self.load_check(opponent)
                                    check_requirements = [1 if self.check_side == opponent else -1]
                                    if self.fits_any(move_rules, 'check', check_requirements, fit=False):
                                        move_fits = True
                                    self.check_side = old_check_side
                                    self.check_groups = old_check_groups
                                if move_fits:
                                    p_from, p_to = move.pos_from, move.pos_to or move.pos_from
                                    if p_from == p_to and move.captured:
                                        for p2 in (piece.board_pos for piece in move.captured):
                                            self.moves[turn_side].setdefault(p_from, {}).setdefault(p2, []).append(move)
                                    else:
                                        self.moves[turn_side].setdefault(p_from, {}).setdefault(p_to, []).append(move)
                                    chained = self.chain_start
                                    poss = []
                                    while chained:
                                        poss.extend((chained.pos_from, chained.pos_to))
                                        chained = chained.chained_move
                                    chained = move
                                    while chained and chained.chained_move and (
                                        issubclass(chained.movement_type or type, CastlingMovement) or issubclass(
                                            chained.chained_move.movement_type or type, (CloneMovement, AutoActMovement)
                                        )
                                    ):
                                        poss.extend((chained.pos_from, chained.pos_to))
                                        chained = chained.chained_move
                                    poss.extend((chained.pos_from, chained.pos_to))
                                    chained = chained.chained_move
                                    if chained and (movement_type := chained.movement_type) and not (
                                        issubclass(movement_type, AutoCaptureMovement) and (
                                            (ch_piece := chained.piece) and (ch_piece.side == turn_side.opponent())
                                        ) or issubclass(movement_type, ConvertMovement) and (
                                            (ch_promo := chained.promotion) and (ch_promo.side == turn_side.opponent())
                                        )
                                    ):
                                        self.chain_moves[turn_side].setdefault(tuple(poss), []).append(chained)
                            for chained in move_chain[::-1]:
                                self.undo(chained, False)
                                self.revert_auto_markers(chained)
                            if not pieces_loaded:
                                self.load_pieces()
                                pieces_loaded = True
                            self.load_theoretical_moves(turn_side, False)
                            self.auto_markers = deepcopy(auto_markers)
                            self.auto_markers_theoretical = deepcopy(auto_markers_theoretical)
                            self.en_passant_targets = deepcopy(en_passant_targets)
                            self.en_passant_markers = deepcopy(en_passant_markers)
                            self.royal_ep_targets = deepcopy(royal_ep_targets)
                            self.royal_ep_markers = deepcopy(royal_ep_markers)
                            self.end_data = deepcopy(end_data)
                            self.check_side = check_side
                            self.check_groups = copy(check_groups)
                if self.moves[turn_side]:
                    self.moves_queried[turn_side] = True
                    break
            else:
                self.moves_queried[turn_side] = True
        if not pieces_loaded:
            self.load_pieces()
            # pieces_loaded = True
        self.move_tags = set()
        if not self.theoretical_move_markers:
            theoretical_moves_for = Side.NONE
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
            self.load_theoretical_moves(turn_side)
        self.movable_pieces = movable_pieces
        self.piece_counts = piece_counts
        self.area_groups = area_groups
        self.royal_groups = royal_groups
        self.royal_pieces = royal_pieces
        self.royal_markers = royal_markers
        self.anti_royal_pieces = anti_royal_pieces
        self.anti_royal_markers = anti_royal_markers
        self.probabilistic_pieces = probabilistic_pieces
        self.auto_pieces = auto_pieces
        self.auto_markers = auto_markers
        self.auto_markers_theoretical = auto_markers_theoretical
        self.en_passant_targets = en_passant_targets
        self.en_passant_markers = en_passant_markers
        self.royal_ep_targets = royal_ep_targets
        self.royal_ep_markers = royal_ep_markers
        self.check_side = check_side
        self.check_groups = copy(check_groups)
        self.end_data = end_data
        self.update_caption()

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
                if move.pos_from == move.pos_to and move.captured:
                    move_data.extend(capture.board_pos for capture in move.captured)
                    # note that this diverges from the otherwise expected move data,
                    # but it does match the approach used during legal move searches
                    # the data tuples are not parsed, only compared, so this is fine
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
                        issubclass(chained_move.movement_type or type, CastlingMovement) or
                        issubclass(chained_move.chained_move.movement_type or type, (CloneMovement, AutoActMovement))
                    ):
                        poss.extend((chained_move.pos_from, chained_move.pos_to))
                        chained_move = chained_move.chained_move
                    poss.extend((chained_move.pos_from, chained_move.pos_to))
                    next_chained = chained_move.chained_move
                    if next_chained and (movement_type := next_chained.movement_type) and not (
                        issubclass(movement_type, AutoCaptureMovement) and (
                            (ch_piece := next_chained.piece) and (ch_piece.side == self.turn_side.opponent())
                        ) or issubclass(movement_type, ConvertMovement) and (
                            (ch_promo := next_chained.promotion) and (ch_promo.side == self.turn_side.opponent())
                        )
                    ) or self.chain_moves.get(self.turn_side, {}).get(tuple(poss)):
                        chained_move.chained_move = Unset  # do not chain moves, we are only counting one-move sequences
                    moves[turn_side].setdefault(move.pos_from, []).append(move)
        return moves

    def find_move(self, pos_from: Position, pos_to: Position) -> Move | None:
        if self.turn_side in self.moves:
            if pos_from in (side_moves := self.moves[self.turn_side]):
                if pos_to in (from_moves := side_moves[pos_from]):
                    if to_moves := from_moves[pos_to]:
                        return copy(to_moves[0]).set(captured=sum((move.captured for move in to_moves), []))
        return None

    def show_moves(self, with_markers: bool | None = None, with_move: bool | None = None) -> None:
        self.hide_moves()
        self.skip_caption_update = False
        self.update_caption()
        move_sprites = dict()
        if with_markers is None:
            with_markers = not self.hide_move_markers
        pos = self.selected_square or self.hovered_square
        if not pos and self.is_active:
            pos = self.highlight_square
        if self.on_board(pos) and pos not in self.drop_area and with_markers:
            piece = self.get_piece(pos)
            if self.hide_move_markers is False or not piece.is_hidden:
                move_dict = {}
                piece_side = self.turn_side if isinstance(piece, (NoPiece, Shared)) else piece.side
                use_type_markers = self.move_type_markers
                type_marker_alpha = 255
                if self.display_theoretical_moves.get(piece_side, False):
                    move_dict = self.theoretical_moves.get(piece_side, {})
                    type_marker_alpha = 192
                elif self.display_moves.get(piece_side, False):
                    move_dict = self.moves.get(piece_side, {})
                pos_dict = {k: v for k, v in move_dict.get(pos, {}).items()}
                if pos not in pos_dict:
                    if self.can_pass() and piece_side == self.turn_side and not isinstance(piece, NoPiece):
                        pos_dict[pos] = ['x' if use_type_markers else 'pass']
                    if self.use_drops and pos in self.moves.get(self.turn_side, {}).get('drop', {}):
                        pos_dict[pos] = ['v' if use_type_markers else 'drop']
                for pos_to, moves in pos_dict.items():
                    move_marker_list = []
                    move_marker_set = set()
                    move_marker_seven = ''
                    for move in moves:
                        if not use_type_markers:
                            if move_marker_set or move_marker_list:
                                break
                            if move == 'pass':
                                move_marker_list.append('capture')
                                move_marker_set.add('pass')
                            elif move == 'drop':
                                move_marker_list.append('move')
                                move_marker_set.add('drop')
                            elif isinstance(move, str):
                                continue
                            elif not move.is_legal:
                                continue
                            else:
                                move_marker_list.append('move' if self.not_a_piece(pos_to) else 'capture')
                                move_marker_set.add(move_marker_list[-1])
                        else:
                            marks = move if isinstance(move, str) else move.marks
                            for mark in marks:
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
                        mark = Sprite(f"assets/util/{move_marker_list[0]}.png")
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
                            mark.alpha = type_marker_alpha
                            self.type_sprite_list.append(mark)
                            move_sprites[pos_to].append(mark)
                    if with_move is None:
                        with_move = False
        if with_move is None:
            with_move = True
        if with_move and self.move_history and not self.edit_mode:
            history_moves = []
            draw_for = self.get_turn_side(-1)
            index = -1
            while index >= -len(self.move_history) and self.get_turn_side(index) == draw_for:
                move = self.move_history[index]
                if move is not None:
                    if move.is_edit:
                        break
                    if self.show_history:
                        history_moves.append(move)
                    elif history_moves:
                        if issubclass(history_moves[-1].movement_type or type, DropMovement):
                            if not issubclass(move.movement_type or type, DropMovement):
                                history_moves = [move]
                                break
                        else:
                            break
                    else:
                        history_moves = [move]
                        if self.get_turn_side(index - 1) != draw_for:
                            break
                index -= 1
                if index < -len(self.move_history) or self.get_turn_side(index) != draw_for:
                    break
            for move in history_moves[::-1]:
                pos_from, pos_to, piece = move.pos_from, move.pos_to, move.piece
                last_move = move
                captures = []
                while last_move.chained_move:
                    for capture in last_move.captured:
                        captures.append(capture.board_pos)
                    if last_move.pos_from == pos_to:
                        pos_to, piece = last_move.pos_to, last_move.piece
                    last_move = last_move.chained_move
                if last_move.pos_from == pos_to:
                    pos_to, piece = last_move.pos_to, last_move.piece
                for capture in last_move.captured:
                    captures.append(capture.board_pos)
                pos = piece.board_pos
                if pos_from is not None and pos_from != pos_to:
                    if pos_from in move_sprites and not self.not_a_piece(pos_from):
                        move_sprites[pos_from].color = self.color_scheme['selection_color']
                    else:
                        sprite = Sprite(f"assets/util/{'capture' if pos_from != pos else 'selection'}.png")
                        sprite.color = self.color_scheme['selection_color']
                        sprite.position = self.get_screen_position(pos_from)
                        sprite.scale = self.square_size / sprite.texture.width
                        self.move_sprite_list.append(sprite)
                if pos_to is not None:
                    if pos_to in move_sprites:
                        move_sprites[pos_to].color = self.color_scheme['selection_color']
                    else:
                        sprite = Sprite(f"assets/util/{'capture' if pos_to != pos else 'selection'}.png")
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
                        sprite = Sprite(f"assets/util/{'capture' if capture != pos else 'selection'}.png")
                        sprite.color = self.color_scheme['highlight_color']
                        sprite.position = self.get_screen_position(capture)
                        sprite.scale = self.square_size / sprite.texture.width
                        self.move_sprite_list.append(sprite)

    def hide_moves(self) -> None:
        self.move_sprite_list.clear()
        self.type_sprite_list.clear()

    def can_pass(self, side: Side | None = None) -> bool:
        return not self.game_over and self.moves.get(side if isinstance(side, Side) else self.turn_side, {}).get('pass')

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

    def update_move(self, move: Move) -> Move:
        first_move = move
        if move.pos_from:
            move.set(piece=self.get_piece(move.pos_from))
        elif not move.piece and move.pos_to:
            move.set(piece=self.get_piece(move.pos_to))
        if move.swapped_piece:
            new_piece = self.get_piece(move.swapped_piece.board_pos if move.swapped_piece is not None else move.pos_to)
            if not isinstance(new_piece, NoPiece):
                move.set(swapped_piece=new_piece)
        capture_poss = set()
        captured_pieces = []
        has_end = move.pos_to in {None, move.pos_from}
        for captured in move.captured:
            if not has_end and captured.board_pos == move.pos_to:
                has_end = True
            new_piece = self.get_piece(captured.board_pos)
            if not isinstance(new_piece, NoPiece) and new_piece.board_pos not in capture_poss:
                capture_poss.add(new_piece.board_pos)
                captured_pieces.append(new_piece)
        if not has_end and not move.swapped_piece:
            new_piece = self.get_piece(move.pos_to)
            if not isinstance(new_piece, NoPiece) and new_piece.board_pos not in capture_poss:
                capture_poss.add(new_piece.board_pos)
                captured_pieces.append(new_piece)
        move.set(captured=captured_pieces)
        return first_move

    def update_auto_actions(self, move: Move, side: Side) -> Move:
        if move.is_edit:
            return move
        if side not in self.auto_markers:
            return move
        first_move = move
        while move.chained_move and not (
            (mtype := move.chained_move.movement_type) and (
            issubclass(mtype, AutoCaptureMovement) and ((ch_pc := move.chained_move.piece) and (ch_pc.side == side)) or
            issubclass(mtype, ConvertMovement) and ((ch_pr := move.chained_move.promotion) and (ch_pr.side == side))
        )):
            move = move.chained_move
        if move.promotion is Unset:
            return first_move  # and generate later
        if move.pos_to in self.auto_markers[side]:
            act_types = self.auto_markers[side][move.pos_to]
            if ConvertMovement in act_types:
                moved = self.get_piece(move.pos_to) if isinstance(move.piece, NoPiece) or move.promotion else move.piece
                piece_data = self.auto_markers[side][move.pos_to][ConvertMovement]
                for piece_pos in sorted(list(piece_data)):
                    if piece_data[piece_pos] and not self.fits_one(piece_data[piece_pos], (), moved):
                        continue
                    piece = self.get_piece(piece_pos)
                    if not piece.side or piece.friendly_of(moved):
                        continue
                    if piece.side == side and piece.captures(moved):
                        converted = moved.of(side)
                        converted.set_moves(None)
                        move.chained_move = Move(
                            pos_from=move.pos_to, pos_to=move.pos_to,
                            piece=moved, promotion=converted,
                            movement_type=ConvertMovement,
                        )
                        break
            elif AutoCaptureMovement in act_types:
                moved = self.get_piece(move.pos_to) if isinstance(move.piece, NoPiece) or move.promotion else move.piece
                piece_data = self.auto_markers[side][move.pos_to][AutoCaptureMovement]
                for piece_pos in sorted(list(piece_data)):
                    if piece_data[piece_pos] and not self.fits_one(piece_data[piece_pos], (), moved):
                        continue
                    piece = self.get_piece(piece_pos)
                    if piece.side == side and piece.captures(moved):
                        move.chained_move = Move(
                            pos_from=piece_pos, pos_to=piece_pos,
                            piece=piece, captured=moved,
                            movement_type=AutoCaptureMovement,
                        )
                        break
        return first_move

    def update_promotion_auto_actions(self, move: Move) -> Move:
        piece = self.get_piece(move.pos_to)
        first_move = move
        while move.chained_move and not (
            (mtype := move.chained_move.movement_type) and issubclass(mtype, AutoActMovement)
        ):
            move = move.chained_move
        move.chained_move = None
        if (
            not issubclass(first_move.movement_type or type, ConvertMovement)
            and isinstance(piece.movement, AutoActMovement)
        ):
            first_move = piece.movement.generate(first_move, piece)
            self.update_auto_markers(first_move, True)
            first_move = self.update_auto_actions(first_move, piece.side.opponent())
        else:
            self.update_auto_markers(first_move, True)
        return first_move

    @staticmethod
    def clear_promotion_auto_actions(move: Move) -> Move:
        promotion_found = bool(move.promotion)
        first_move = move
        while move.chained_move and not (issubclass(move.chained_move.movement_type or type, AutoActMovement)):
            if not issubclass(move.movement_type or type, (CloneMovement, ConvertMovement)):
                move.promotion = Unset
            move = move.chained_move
            if not promotion_found and move.promotion:
                promotion_found = True
        if promotion_found:
            move.chained_move = None
        if not issubclass(move.movement_type or type, (CloneMovement, ConvertMovement)):
            move.promotion = Unset
        return first_move

    def load_auto_markers(self, side: Side = Side.ANY) -> None:
        for side in self.auto_pieces if side is Side.ANY else (side,):
            for piece in self.auto_pieces.get(side, []):
                if isinstance(piece.movement, AutoMarkMovement):
                    piece.movement.mark(piece.board_pos, piece)

    def clear_auto_markers(self, side: Side = Side.ANY) -> None:
        for markers in (self.auto_markers, self.auto_markers_theoretical):
            for side in markers if side is Side.ANY else (side,):
                markers.get(side, {}).clear()

    def refresh_auto_markers(self, move: Move, side: Side = Side.ANY) -> None:
        refresh_poss = {move.pos_from, move.pos_to} | {capture.board_pos for capture in move.captured}
        refresh_poss.discard(None)
        refresh_piece_poss = set()
        for side in self.auto_markers_theoretical if side is Side.ANY else (side,):
            theoretical = self.auto_markers_theoretical.get(side, {})
            for pos in refresh_poss:
                if pos not in theoretical:
                    continue
                for marker_type in theoretical[pos]:
                    refresh_piece_poss |= set(theoretical[pos][marker_type])
        for pos in refresh_piece_poss:
            piece = self.get_piece(pos)
            if isinstance(piece.movement, AutoMarkMovement):
                piece.movement.unmark(pos, piece, False)
                piece.movement.mark(pos, piece, False)

    def update_auto_markers(self, move: Move, recursive: bool = False) -> None:
        while move:
            moved_piece = move.piece
            if move.promotion:
                if moved_piece and isinstance(moved_piece.movement, AutoMarkMovement):
                    moved_piece.movement.unmark(move.pos_to, moved_piece)
                moved_piece = self.get_piece(move.pos_to)
            if isinstance(moved_piece.movement, AutoMarkMovement):
                if move.pos_to is None or move.is_edit:
                    moved_piece.movement.unmark(move.pos_from, moved_piece)
                if move.pos_from is None or move.is_edit or move.promotion:
                    moved_piece.movement.mark(move.pos_to, moved_piece)
            for capture in move.captured:
                if isinstance(capture.movement, AutoMarkMovement):
                    capture.movement.unmark(capture.board_pos, capture)
            if move.swapped_piece is not None:
                if isinstance(move.swapped_piece.movement, AutoMarkMovement):
                    move.swapped_piece.movement.unmark(move.pos_to, move.swapped_piece)
                    move.swapped_piece.movement.mark(move.pos_from, move.swapped_piece)
            self.refresh_auto_markers(move)
            if not recursive:
                return
            move = move.chained_move

    def revert_auto_markers(self, move: Move, recursive: bool = False) -> None:
        move_list = []
        if recursive:
            while move:
                move_list.append(move)
                move = move.chained_move
        for move in (reversed(move_list) if recursive else [move]):
            if move.promotion:
                moved_piece = self.get_piece(move.pos_to)
                if isinstance(moved_piece.movement, AutoMarkMovement):
                    moved_piece.movement.unmark(move.pos_to, moved_piece)
            moved_piece = move.piece
            if isinstance(moved_piece.movement, AutoMarkMovement):
                if move.pos_from is None or move.is_edit:
                    moved_piece.movement.unmark(move.pos_to, moved_piece)
                if move.pos_to is None or move.is_edit or move.promotion:
                    moved_piece.movement.mark(move.pos_from, moved_piece)
            for capture in move.captured:
                if isinstance(capture.movement, AutoMarkMovement):
                    capture.movement.mark(capture.board_pos, capture)
            if move.swapped_piece is not None:
                if isinstance(move.swapped_piece.movement, AutoMarkMovement):
                    move.swapped_piece.movement.unmark(move.pos_from, move.swapped_piece)
                    move.swapped_piece.movement.mark(move.pos_to, move.swapped_piece)
            self.refresh_auto_markers(move)

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
                    for marker_pos in list(side_marker_dict):
                        pos_marker_set = side_marker_dict[marker_pos]
                        for target_pos in list(pos_marker_set):
                            pos_target_dict = side_target_dict.get(target_pos, {})
                            pos_target_set = pos_target_dict.get(marker_pos, set())
                            if {Delayed, Delayed1}.intersection(pos_target_set):
                                if not (side == current_side and is_final_turn and chain_end):
                                    continue
                            if CastlingMovement in pos_target_set:
                                continue
                            if target_pos == marker_pos:
                                continue
                            if Covered not in pos_target_set or isinstance(self.get_piece(marker_pos), NoPiece):
                                continue
                            pos_target_dict.pop(marker_pos, None)
                            pos_marker_set.discard(target_pos)
                    for target_pos in list(side_target_dict):
                        if move and target_pos == move.pos_to:
                            continue
                        pos_target_dict = side_target_dict[target_pos]
                        for marker_pos in list(pos_target_dict):
                            pos_marker_set = side_marker_dict.get(marker_pos, set())
                            pos_target_set = pos_target_dict.get(marker_pos, set())
                            if Delayed in pos_target_set and not (side == next_side and is_final_turn and chain_end):
                                continue
                            if Delayed1 in pos_target_set and not (side == last_side and is_first_turn):
                                continue
                            if Slow in pos_target_set:
                                if chain_end:
                                    pos_target_set.discard(Slow)
                                continue
                            if CastlingMovement in pos_target_set:
                                if chain_end:
                                    pos_target_set.discard(CastlingMovement)
                                continue
                            pos_target_dict.pop(marker_pos, None)
                            pos_marker_set.discard(target_pos)
            if move:
                for capture in move.captured:
                    side = capture.side
                    side_target_dict, side_marker_dict = target_dict.get(side, {}), marker_dict.get(side, {})
                    for marker_pos in side_target_dict.pop(capture.board_pos, {}):
                        side_marker_dict.get(marker_pos, set()).discard(capture.board_pos)
                for piece, old_pos in ((move.piece, move.pos_from), (move.swapped_piece, move.pos_to)):
                    if piece is None:
                        continue
                    pos_from, pos_to = old_pos, piece.board_pos
                    if pos_from == pos_to:
                        continue
                    side = piece.side
                    side_target_dict, side_marker_dict = target_dict.get(side, {}), marker_dict.get(side, {})
                    if move.is_edit or not issubclass(type(move.piece), Slow):
                        for marker_pos in side_target_dict.pop(pos_from, {}):
                            side_marker_dict.get(marker_pos, set()).discard(pos_from)
                    elif piece.side in target_dict and not move.swapped_piece:
                        from_markers = side_target_dict.pop(pos_from, {})
                        for marker_pos, marker_set in from_markers.items():
                            side_target_dict.setdefault(pos_to, {})[marker_pos] = marker_set
                            side_marker_dict.setdefault(marker_pos, set()).add(pos_to)

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
                        chained_move.is_edit != 1 and not issubclass(
                            chained_move.movement_type or type, (CloneMovement, DropMovement)
                        )
                    ):
                        if chained_move.piece and chained_move.piece.movement:
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
                move and move.is_edit != 1 and move.movement_type
                and not issubclass(move.movement_type or type, (CloneMovement, DropMovement))
            ):
                if move.piece and move.piece.movement:
                    move.piece.movement.update(move, move.piece)
            self.update_en_passant_markers(move)
            if move:
                chained_move = move.chained_move
                while chained_move:
                    if (
                        chained_move.is_edit != 1 and chained_move.movement_type
                        and not issubclass(chained_move.movement_type or type, (CloneMovement, DropMovement))
                    ):
                        if chained_move.piece and chained_move.piece.movement:
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
            if move.piece and move.pos_from != move.pos_to:
                self.clear_relay_markers_for(move.piece, move.pos_from or move.pos_to)
            if move.promotion:
                self.clear_relay_markers_for(move.promotion, move.pos_to)
            for capture in move.captured:
                self.clear_relay_markers_for(capture, capture.board_pos)
            if move.swapped_piece:
                self.clear_relay_markers_for(move.swapped_piece, move.pos_to)
            move = move.chained_move

    def revert_relay_markers(self, move: Move | None = None):
        move_chain = []
        while move:
            move_chain.append(move)
            move = move.chained_move
        for move in move_chain[::-1]:
            if move.piece and move.pos_from != move.pos_to:
                piece = move.promotion or move.piece
                self.clear_relay_markers_for(piece, move.pos_to or move.pos_from)
            if move.promotion:
                self.clear_relay_markers_for(move.promotion, move.pos_to)
            for capture in move.captured:
                self.clear_relay_markers_for(capture, capture.board_pos)
            if move.swapped_piece:
                self.clear_relay_markers_for(move.swapped_piece, move.pos_to)

    def clear_relay_markers(self) -> None:
        for relay_dict in (self.relay_sources, self.relay_targets, self.coordinate_sources, self.coordinate_targets):
            for side in relay_dict:
                relay_dict[side].clear()

    def clear_relay_markers_for(self, piece: AbstractPiece, pos: Position):
        for source_dict, target_dict in (
            (self.relay_sources, self.relay_targets),
            (self.coordinate_targets, self.coordinate_sources),  # NB: order intentionally reversed!
        ):
            sources = source_dict.get(piece.side, {})
            targets = target_dict.get(piece.side, {})
            for movement, movement_sources in sources.pop(pos, {}).items():
                movement_targets = targets.get(movement, {})
                for source_pos in movement_sources:
                    movement_targets.pop(source_pos, None)

    def update_end_data(self, move: Move | None = None) -> None:
        if self.edit_mode or (move and move.is_edit):
            return
        opponent = self.turn_side.opponent()
        conditions = {x: {x, pch['not'] + x} for x in {'check', 'checkmate', 'stalemate', 'capture'}}
        if conditions['check'].intersection(self.end_rules[opponent]) and self.check_side == self.turn_side:
            for group in ('', *self.check_groups):
                for condition in conditions['check'].intersection(self.end_data[opponent]):
                    if group in self.end_data[opponent][condition]:
                        self.end_data[opponent][condition][group] += 1
        if not move:
            return
        for side in {self.turn_side, self.turn_side.opponent()}:
            for keyword in ('checkmate', 'capture'):
                if conditions[keyword].intersection(self.end_rules[side]):
                    for group in self.get_royal_loss(side.opponent(), move, {keyword}):
                        for condition in conditions[keyword].intersection(self.end_data[side]):
                            if group in self.end_data[side][condition]:
                                self.end_data[side][condition][group] += 1

    def revert_end_data(self, move: Move | None = None) -> None:
        if self.edit_mode or (move and move.is_edit):
            return
        conditions = {x: {x, pch['not'] + x} for x in {'check', 'checkmate', 'stalemate', 'capture'}}
        for side in {self.turn_side, self.turn_side.opponent()}:
            for keyword in ('checkmate', 'stalemate'):
                for condition in conditions[keyword]:
                    if condition in self.end_rules[side]:
                        self.end_data[side][condition][''] = 0
        opponent = self.turn_side.opponent()
        if conditions['check'].intersection(self.end_rules[opponent]) and self.check_side == self.turn_side:
            for group in ('', *self.check_groups):
                for condition in conditions['check'].intersection(self.end_data[opponent]):
                    if group in self.end_data[opponent][condition]:
                        self.end_data[opponent][condition][group] -= 1
        if not move:
            return
        for side in {self.turn_side, self.turn_side.opponent()}:
            for keyword in ('checkmate', 'capture'):
                if conditions[keyword].intersection(self.end_rules[side]):
                    for group in self.get_royal_loss(side.opponent(), move, {keyword}):
                        for condition in conditions[keyword].intersection(self.end_data[side]):
                            if group in self.end_data[side][condition]:
                                self.end_data[side][condition][group] -= 1

    def reload_end_data(self, _: Move | None = None) -> None:
        if self.edit_mode:
            return
        conditions = {x: {x, pch['not'] + x} for x in {'check', 'checkmate', 'stalemate', 'capture'}}
        opponent = self.turn_side.opponent()
        for side in {self.turn_side, self.turn_side.opponent()}:
            if not self.moves.get(side) and self.moves_queried.get(side, False):
                if 'checkmate' in self.end_rules[opponent] and self.check_side == side:
                    for condition in conditions['checkmate'].intersection(self.end_data[opponent]):
                        self.end_data[opponent][condition][''] = 1
                if 'stalemate' in self.end_rules[opponent] and not self.check_side:
                    for condition in conditions['stalemate'].intersection(self.end_data[opponent]):
                        self.end_data[opponent][condition][''] = 1

    def unload_end_data(self, _: Move | None = None) -> None:
        conditions = {x: {x, pch['not'] + x} for x in {'check', 'checkmate', 'stalemate', 'capture'}}
        for side in {self.turn_side, self.turn_side.opponent()}:
            for keyword in ('checkmate', 'stalemate'):
                if conditions[keyword].intersection(self.end_rules[side]):
                    for condition in conditions[keyword].intersection(self.end_data[side]):
                        self.end_data[side][condition][''] = 0

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
        self.auto_moves = False
        finished = False
        next_move = future_move_history.pop()
        while True:
            old_turn_side = self.turn_side
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
                next_move = self.move(next_move)
                self.update_auto_markers(next_move)
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
                    next_move = self.try_drop(next_move)
                    self.move_history.append(next_move)
                    if next_move.promotion is Unset:
                        finished = True
                        break
                    else:
                        self.log(f"Drop: {next_move}")
                        chained_move = next_move
                        while chained_move.chained_move:
                            chained_move.chained_move = self.move(chained_move.chained_move)
                            chained_move = chained_move.chained_move
                            self.update_auto_markers(chained_move)
                            chained_move.set(piece=copy(chained_move.piece))
                            if chained_move.swapped_piece:
                                chained_move.set(swapped_piece=copy(chained_move.swapped_piece))
                            if self.promotion_piece is None:
                                self.log(f"Move: {chained_move}")
                            else:
                                finished = True
                                break
                        self.shift_ply(+1)
                else:
                    finished = False
                    break
            else:
                move = None
                pos_from, pos_to = next_move.pos_from, next_move.pos_to or next_move.pos_from
                if pos_from != pos_to or not next_move.captured:
                    move = self.find_move(pos_from, pos_to)
                else:
                    for capture in next_move.captured:
                        move = self.find_move(pos_from, capture.board_pos)
                        if move is not None:
                            break
                if move is None:
                    finished = False
                    break
                self.update_move(move)
                chained_move = self.chain_start
                poss = []
                while chained_move:
                    poss.extend((chained_move.pos_from, chained_move.pos_to))
                    chained_move = chained_move.chained_move
                chained_move = move
                while chained_move and chained_move.chained_move and (
                    issubclass(chained_move.movement_type or type, CastlingMovement) or
                    issubclass(chained_move.chained_move.movement_type or type, (CloneMovement, AutoActMovement))
                ):
                    poss.extend((chained_move.pos_from, chained_move.pos_to))
                    chained_move = chained_move.chained_move
                poss.extend((chained_move.pos_from, chained_move.pos_to))
                next_chained = chained_move.chained_move
                if next_chained and (movement_type := next_chained.movement_type) and not (
                    issubclass(movement_type, AutoCaptureMovement) and (
                        (ch_piece := next_chained.piece) and (ch_piece.side == self.turn_side.opponent())
                    ) or issubclass(movement_type, ConvertMovement) and (
                        (ch_promo := next_chained.promotion) and (ch_promo.side == self.turn_side.opponent())
                    )
                ) or self.chain_moves.get(self.turn_side, {}).get(tuple(poss)):
                    chained_move.chained_move = Unset  # do not chain moves because we're updating every move separately
                if next_move.promotion is not None:
                    move = self.clear_promotion_auto_actions(move)  # clear the old auto-actions in order to reload them
                    move.promotion = next_move.promotion  # since the legal move we found may have a different promotion
                move = self.move(move)
                self.update_auto_markers(move, True)
                move = self.update_auto_actions(move, self.turn_side.opponent())
                chained_move = move
                while chained_move:
                    chained_move.set(piece=copy(chained_move.piece))
                    if chained_move.swapped_piece:
                        chained_move.set(swapped_piece=copy(chained_move.swapped_piece))
                    if self.promotion_piece is None:
                        self.log(f"Move: {chained_move}")
                    if chained_move.chained_move:
                        chained_move.chained_move = self.move(chained_move.chained_move)
                        self.update_auto_markers(chained_move.chained_move)
                        next_move = next_move.chained_move
                    chained_move = chained_move.chained_move
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
                if old_turn_side != self.turn_side:
                    self.update_alternate_sprites(old_turn_side)
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
        self.auto_moves = True
        return finished

    def try_auto(self, update: bool = True) -> bool:
        moves = self.moves[self.turn_side]
        only_move = None
        for pos_from in moves:
            if isinstance(pos_from, str):
                if only_move is None:
                    only_move = pos_from
                    if only_move == 'drop':
                        if len(moves[pos_from]) != 1:
                            break
                        drop_pos = list(moves[pos_from])[0]
                        if len(moves[pos_from][drop_pos]) != 1:
                            break  # NB: moves[pos_from][drop_pos] here is a set[type[AbstractPiece]]
                        # Note that it is technically possible to have legal drops of the same piece to the same square,
                        # but with the dropped pieces having distinct metadata. The type-based check above is not enough
                        # to unambiguously resolve such cases, but it very likely won't matter for most custom variants.
                        only_move = Move(pos_from=None, pos_to=drop_pos, movement_type=DropMovement, promotion=Unset)
                        self.update_move(only_move)
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
            self.auto(only_move, update)
            return True
        return False

    def auto(self, move: Move, update: bool = True) -> None:
        move = self.move(move, update)
        self.update_auto_markers(move, True)
        move = self.update_auto_actions(move, self.turn_side.opponent())
        chained_move = move
        while chained_move:
            chained_move.set(piece=copy(chained_move.piece))
            if chained_move.swapped_piece:
                chained_move.set(swapped_piece=copy(chained_move.swapped_piece))
            if self.promotion_piece is None:
                move_type = (
                    'Edit' if chained_move.is_edit
                    else 'Drop' if chained_move.movement_type == DropMovement
                    else 'Move'
                )
                self.log(f"{move_type}: {chained_move}")
            if chained_move.chained_move:
                chained_move.chained_move = self.move(chained_move.chained_move, update)
                self.update_auto_markers(chained_move.chained_move)
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
        if move.chained_move is Unset and not self.promotion_piece:
            self.load_pieces()
            self.load_moves()
            if update:
                self.show_moves(with_markers=False)
                self.draw(0)
                self.select_piece(move.pos_to)
            else:
                self.selected_square = move.pos_to
            if self.auto_moves and (
                self.board_config['fast_moves'] or self.board_config['fast_chain']
            ) and not self.game_over:
                self.try_auto(update)
        else:
            self.chain_start = None
            if self.promotion_piece:
                self.load_pieces()
            else:
                old_turn_side = self.turn_side
                self.shift_ply(+1)
                self.load_pieces()
                self.load_check()
                self.update_end_data(self.move_history[-1])
                self.load_moves()
                self.reload_end_data()
                if old_turn_side != self.turn_side:
                    self.update_alternate_sprites(old_turn_side)
                self.compare_history()
            self.advance_turn()

    def move(self, move: Move, update: bool = True) -> Move:
        self.skip_caption_update = True
        self.deselect_piece()
        self.update_drops(False)
        abs_from, abs_to = self.get_absolute(move.pos_from), self.get_absolute(move.pos_to)
        if move.piece is not None and move.pos_to is not None:
            # piece was moved to a different square, set its position to the new square
            self.set_position(move.piece, move.pos_to, update)
        if move.swapped_piece is not None:
            # piece was swapped with another piece, set the swapped piece's position to the square the move started from
            self.set_position(move.swapped_piece, move.pos_from, update)
        if update and isinstance(move.piece, Piece) and move.pos_to is None:
            # piece was removed from the board, empty the square it was on
            self.piece_sprite_list.remove(move.piece.sprite)
        if move.pos_to is not None and move.pos_from != move.pos_to:
            # piece was moved to a different square, empty the square it was moved to and put the piece there
            if update and isinstance(self.pieces[abs_to[0]][abs_to[1]], Piece):
                self.piece_sprite_list.remove(self.pieces[abs_to[0]][abs_to[1]].sprite)
            self.pieces[abs_to[0]][abs_to[1]] = move.piece
        if update:
            for capture in move.captured:
                if not isinstance(capture, Piece) or capture.board_pos == move.pos_to:
                    continue
                # piece was captured on a different square than the one the capturing piece moved to (e.g. en passant)
                # empty the square it was captured on (it was not emptied earlier because it was not the one moved to)
                self.piece_sprite_list.remove(capture.sprite)
        if move.pos_from is not None and move.pos_from != move.pos_to:
            # existing piece was moved to a different square, create a blank piece on the square that was moved from
            self.pieces[abs_from[0]][abs_from[1]] = (
                NoPiece(self, board_pos=move.pos_from) if move.swapped_piece is None else move.swapped_piece
            )
            if update and isinstance(self.pieces[abs_from[0]][abs_from[1]], Piece):
                self.piece_sprite_list.append(self.pieces[abs_from[0]][abs_from[1]].sprite)
        for capture in move.captured:
            if not isinstance(capture, Piece) or capture.board_pos == move.pos_to:
                continue
            # piece was captured on a different square than the one the capturing piece moved to (e.g. en passant)
            # create a blank piece on the square it was captured on
            capture_pos = self.get_absolute(capture.board_pos)
            self.pieces[capture_pos[0]][capture_pos[1]] = NoPiece(self, board_pos=capture.board_pos)
            if update and isinstance(self.pieces[capture_pos[0]][capture_pos[1]], Piece):
                self.piece_sprite_list.append(self.pieces[capture_pos[0]][capture_pos[1]].sprite)
        if update and isinstance(move.piece, Piece) and move.pos_from is None:
            # piece was added to the board, update it and add it to the sprite list
            self.update_piece(move.piece)
            self.piece_sprite_list.append(move.piece.sprite)
        if move.piece is not None and move.piece.side in self.drops and not move.is_edit == 1:
            captures = [move.piece] if move.pos_to is None else move.captured
            for capture in captures:
                if capture is not None and move.piece.side in self.captured_pieces:
                    capture_type = capture.promoted_from or type(capture)
                    if capture_type in self.drops[move.piece.side]:
                        # droppable piece was captured, add it to the roster of captured pieces
                        self.captured_pieces[move.piece.side].append(capture_type)
        for piece, pos in (
            (move.piece, move.pos_from),
            (move.swapped_piece, move.pos_to),
            *((capture, None) for capture in move.captured),
        ):
            if piece is None:
                continue
            if pos is None:
                pos = piece.board_pos
            self.clear_theoretical_moves(piece.side, pos)
        if (
            move.is_edit != 1 and move.movement_type
            and not issubclass(move.movement_type or type, (CloneMovement, DropMovement))
        ):
            # call movement.update() to update movement state after the move (e.g. pawn double move, castling rights)
            if move.piece and move.piece.movement:
                move.piece.movement.update(move, move.piece)
        if move.is_edit != 1:
            if not move.piece or isinstance(move.piece, NoPiece):
                # check if a piece can be dropped
                move = self.try_drop(move, update)
            else:
                # check if the piece needs to be promoted
                move = self.try_promotion(move, update)
        if not self.ply_simulation:
            # update markers for possible en passant captures
            self.update_en_passant_markers(move)
            # as well as for relay moves
            self.update_relay_markers(move)
        if update:
            old_color = self.highlight.color
            self.highlight.color = (0, 0, 0, 0)
            self.hide_moves()
            self.draw(0)
            self.highlight.color = old_color
        return move

    def undo(self, move: Move, update: bool = True) -> None:
        self.skip_caption_update = True
        abs_from, abs_to = self.get_absolute(move.pos_from), self.get_absolute(move.pos_to)
        if move.pos_from != move.pos_to or move.promotion is not None:
            # piece was added, moved, removed, or promoted
            if move.pos_from is not None:
                # existing piece was moved, empty the square it was moved from and restore its position
                self.set_position(move.piece, move.pos_from, update)
                if update and isinstance(self.pieces[abs_from[0]][abs_from[1]], Piece):
                    self.piece_sprite_list.remove(self.pieces[abs_from[0]][abs_from[1]].sprite)
            if move.pos_to is not None:
                if update and isinstance(self.pieces[abs_to[0]][abs_to[1]], Piece) and move.pos_from != move.pos_to:
                    # piece was placed on a different square, empty that square
                    self.piece_sprite_list.remove(self.pieces[abs_to[0]][abs_to[1]].sprite)
            if update and isinstance(move.piece, Piece) and (move.pos_to is None or move.promotion is not None):
                # existing piece was removed from the board (possibly promoted to a different piece type)
                if not self.is_trickster_mode():  # reset_trickster_mode() does not reset removed pieces
                    move.piece.sprite.angle = 0   # so instead we have to do it manually as a workaround
            if update and isinstance(move.piece, Piece):
                # update the piece sprite to reflect current piece hiding mode
                self.update_piece(move.piece)
            if move.pos_from is not None:
                # existing piece was moved, restore it on the square it was moved from
                self.pieces[abs_from[0]][abs_from[1]] = move.piece
                if update and isinstance(move.piece, Piece):
                    self.piece_sprite_list.append(move.piece.sprite)
        capture_poss = set()
        for capture in move.captured:
            capture_poss.add(capture.board_pos)
            # piece was captured, restore it on the square it was captured on
            capture_pos = self.get_absolute(capture.board_pos)
            if move.pos_to != capture.board_pos:
                # piece was captured on a different square than the one the capturing piece moved to (e.g. en passant)
                # empty the square it was captured on (it was not emptied earlier because it was not the one moved to)
                if update and isinstance(self.pieces[capture_pos[0]][capture_pos[1]], Piece):
                    self.piece_sprite_list.remove(self.pieces[capture_pos[0]][capture_pos[1]].sprite)
            self.reset_position(capture, update)
            self.pieces[capture_pos[0]][capture_pos[1]] = capture
            if update and isinstance(capture, Piece):
                if not self.is_trickster_mode():  # reset_trickster_mode() does not reset removed pieces
                    capture.sprite.angle = 0  # so we have to do it manually, etc., whatever
                self.update_piece(capture)  # update the piece to reflect current piece hiding mode
                self.piece_sprite_list.append(capture.sprite)
        if move.piece is not None and move.piece.side in self.drops and move.is_edit != 1:
            captures = [move.piece] if move.pos_to is None else move.captured
            for capture in captures:
                if capture is not None and move.piece.side in self.captured_pieces:
                    capture_type = capture.promoted_from or type(capture)
                    if capture_type in self.drops.get(move.piece.side, {}):
                        # droppable piece was captured, remove it from the roster of captured pieces
                        for i, piece in enumerate(self.captured_pieces[move.piece.side][::-1]):
                            if piece == capture_type:
                                self.captured_pieces[move.piece.side].pop(-(i + 1))
                                break
        if move.pos_to is not None and move.pos_from != move.pos_to:
            # piece was added on or moved to a different square, restore the piece that was there before
            old_piece = None
            if move.swapped_piece is not None:
                # piece was swapped with another piece, move the swapped piece to the square that was moved to
                old_piece = move.swapped_piece
                self.set_position(move.swapped_piece, move.pos_to, update)
            elif move.pos_to not in capture_poss:
                # no piece was on the square that was moved to (e.g. non-capturing move, en passant)
                old_piece = NoPiece(self, board_pos=move.pos_to)  # so create a blank piece on that square
            if old_piece is not None:
                self.pieces[abs_to[0]][abs_to[1]] = old_piece
                if update and isinstance(old_piece, Piece):
                    self.update_piece(old_piece)  # update the piece to reflect current piece hiding mode
                    self.piece_sprite_list.append(old_piece.sprite)
        for piece, pos in (
            (move.promotion or move.piece, move.pos_to),
            (move.swapped_piece, move.pos_from),
        ):
            if piece is None:
                continue
            if pos is None:
                pos = piece.board_pos
            self.clear_theoretical_moves(piece.side, pos)
        if move.is_edit != 1 and not issubclass(move.movement_type or type, (CloneMovement, DropMovement)):
            # call movement.undo() to restore movement state before the move (e.g. pawn double move, castling rights)
            if move.piece and move.piece.movement:
                move.piece.movement.undo(move, move.piece)
        if not self.ply_simulation:
            # revert markers for relay moves
            self.revert_relay_markers(move)
        if update:
            old_color = self.highlight.color
            self.highlight.color = (0, 0, 0, 0)
            self.hide_moves()
            self.draw(0)
            self.highlight.color = old_color

    def undo_last_move(self) -> None:
        self.deselect_piece()
        self.update_drops(False)
        if not self.move_history:
            return
        old_turn_side = self.turn_side
        in_promotion = self.promotion_piece is not None
        partial_move = self.chain_start is not None or in_promotion
        if in_promotion:
            if self.move_history and self.future_move_history:
                past, future = self.move_history[-1], self.future_move_history[-1]
                opt = lambda x: x or self.no_piece
                while (
                    past and future and past.pos_from == future.pos_from and past.pos_to == future.pos_to
                    and (opt(past.swapped_piece).board_pos == opt(future.swapped_piece).board_pos) and all(
                        opt(x).board_pos == opt(y).board_pos for x, y in zip_longest(past.captured, future.captured)
                    )
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
        last_move_copy = deepcopy(last_move)
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
                self.revert_auto_markers(chained_move)
                if chained_move.promotion is not None:
                    if chained_move.placed_piece is not None:
                        turn_side = self.get_turn_side()
                        if chained_move.placed_piece in self.drops.get(turn_side, {}):
                            self.captured_pieces[turn_side].append(chained_move.placed_piece)
                    if isinstance(chained_move.piece, Piece):
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
                if move.piece and move.piece.movement:
                    move.piece.movement.reload(move, move.piece)
        self.reload_en_passant_markers()
        future_move_history = self.future_move_history.copy()
        self.unload_end_data()
        self.load_pieces()
        self.load_check()
        self.load_moves()
        self.reload_end_data()
        if old_turn_side != self.turn_side:
            self.update_alternate_sprites(old_turn_side)
        self.advance_turn()
        self.future_move_history = future_move_history
        if partial_move and self.future_move_history:
            last_history_move = self.future_move_history[-1]
            last_chain_move = last_move
            matches = True
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
                        matches = False
                        break
                    last_history_move = last_history_move.chained_move
                    last_chain_move = last_chain_move.chained_move
                else:
                    matches = False
                    break
            if not matches:
                self.clear_future_history(self.ply_count)
                self.future_move_history.append(last_move_copy)
        else:
            self.future_move_history.append(last_move_copy)

    def redo_last_move(self) -> None:
        self.deselect_piece()
        self.update_drops(False)
        piece_was_moved = False
        if self.promotion_piece is not None:
            if self.move_history and self.future_move_history:
                past, future = self.move_history[-1], self.future_move_history[-1]
                opt = lambda x: x or self.no_piece
                while past and future:
                    if (
                        past.pos_from == future.pos_from and past.pos_to == future.pos_to and
                        (opt(past.swapped_piece).board_pos == opt(future.swapped_piece).board_pos) and all(
                            opt(x).board_pos == opt(y).board_pos for x, y in zip_longest(past.captured, future.captured)
                        )
                    ):
                        if past.promotion is Unset:
                            if future.promotion is Unset:
                                return
                            past.promotion = future.promotion
                            if future.promotion is not None:
                                if future.placed_piece is not None:
                                    past.placed_piece = future.placed_piece
                                    for i, piece in enumerate(self.captured_pieces[self.turn_side][::-1]):
                                        if piece == future.placed_piece:
                                            self.captured_pieces[self.turn_side].pop(-(i + 1))
                                            break
                                self.replace(self.promotion_piece, future.promotion, future.movement_type)
                            self.move_history[-1] = self.update_promotion_auto_actions(self.move_history[-1])
                            self.end_promotion()
                            # The following two lines are a workaround for the fact that PyCharm insisted that
                            # "piece_was_moved = True" here was useless, despite the variable being used later
                            # (I explicitly checked if removing it introduces side effects, and yes, it does).
                            while not piece_was_moved:
                                piece_was_moved = True
                            break
                        past, future = past.chained_move, future.chained_move
                    else:
                        return
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
                if chained_move.chained_move:
                    chained_move.chained_move = self.move(chained_move.chained_move)
                last_chain_move = chained_move
                chained_move = chained_move.chained_move
                if chained_move:
                    self.update_auto_markers(chained_move)
                    chained_move.set(piece=copy(chained_move.piece))
                    if chained_move.swapped_piece:
                        chained_move.set(swapped_piece=copy(chained_move.swapped_piece))
        else:
            if last_move.pos_from is None:
                last_move = self.move(last_move)
            else:
                self.update_move(last_move)
                last_move = self.move(last_move)
                self.update_auto_markers(last_move, True)
                last_move = self.update_auto_actions(last_move, self.turn_side.opponent())
            chained_move = last_move
            while chained_move:
                chained_move.set(piece=copy(chained_move.piece))
                if chained_move.swapped_piece:
                    chained_move.set(swapped_piece=copy(chained_move.swapped_piece))
                move_type = (
                    'Edit' if chained_move.is_edit
                    else 'Drop' if chained_move.movement_type == DropMovement
                    else 'Move'
                )
                self.log(f"Redo: {move_type}: {chained_move}")
                self.apply_edit_promotion(chained_move)
                if chained_move.chained_move:
                    self.update_move(chained_move.chained_move)
                    chained_move.chained_move = self.move(chained_move.chained_move)
                    self.update_auto_markers(chained_move.chained_move)
                last_chain_move = chained_move
                chained_move = chained_move.chained_move
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
            if self.promotion_piece is None:
                old_turn_side = self.turn_side
                offset = last_move is None or not last_move.is_edit
                if offset:
                    self.shift_ply(+1)
                    self.load_pieces()
                    self.load_check()
                    self.update_end_data(last_move)
                else:
                    self.load_pieces()
                    self.load_check()
                    self.update_end_data()
                self.load_moves()
                self.reload_end_data()
                if old_turn_side != self.turn_side:
                    self.update_alternate_sprites(old_turn_side)
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
        count = self.get_turn_index()
        start_count = count
        while self.get_turn_side() != side:
            index += 1
            if side is None:
                break
            count = self.get_turn_index(index)
            if count == start_count:
                return
        for _ in range(index - self.ply_count):
            log_pass = self.board_config['log_pass']
            if log_pass is None:
                log_pass = set(self.moves[self.turn_side]) != {'pass'}
            turn_side = self.get_turn_side(+1)
            if log_pass:
                self.log(f"Pass: {turn_side} to move")
            old_turn_side = self.turn_side
            self.update_en_passant_markers()
            self.move_history.append(None)
            self.shift_ply(+1)
            self.unload_end_data()
            self.load_pieces()
            self.load_check()
            self.update_end_data()
            self.load_moves()
            self.reload_end_data()
            if old_turn_side != self.turn_side:
                self.update_alternate_sprites(old_turn_side)
            self.compare_history()
            self.advance_turn()

    def advance_turn(self) -> None:
        self.deselect_piece()
        self.update_drops(False)
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
        if self.is_started:
            self.sync(get=True, post=True)
        if self.edit_mode:
            self.load_end_conditions()
            self.color_pieces()  # reverting the piece colors to normal in case they were changed
            self.update_caption()  # updating the caption to reflect the edit that was just made
            return  # let's not advance the turn while editing the board to hopefully make things easier for everyone
        self.update_status()
        if self.auto_moves and not self.game_over:
            if self.board_config['fast_sequences'] or self.board_config['fast_turn_pass']:
                if 'pass' in self.moves[self.turn_side] and len(self.moves[self.turn_side]) == 1:
                    self.pass_turn()
            if self.board_config['fast_moves']:
                self.try_auto()
            elif self.board_config['fast_sequences'] and self.turn_side == self.get_turn_side(-1):
                self.try_auto()

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
                    string += f"{end_group} lost!"
                else:
                    string += f"{pluralize(self.end_value, 'Piece')} lost!"
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
        return None

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

    def update_caption(self, string: str | None = None, force: bool = False) -> None:
        if self.skip_caption_update and not force:
            return
        if self.board_config['status_string'] is None:
            self.set_caption(self.custom_variant or ("???" if self.hide_pieces else self.variant))
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
                self.set_caption(self.custom_variant or ("???" if self.hide_pieces else self.variant))
            return
        if prefix:
            prefix = f"[{prefix}]"
        if string is not None:
            self.set_caption(f"{prefix} {string}")
            return
        selected_square = self.selected_square
        hovered_square = None
        if self.is_active:
            hovered_square = self.hovered_square or self.highlight_square
        if self.promotion_piece:
            piece = self.promotion_piece
            skip = hovered_square in self.promotion_area_drops and self.promotion_area_drops[hovered_square] is None
            if isinstance(piece, NoPiece):
                if hovered_square in self.promotion_area:
                    message = "Nothing" if skip else f"{self.promotion_area[hovered_square]}"
                else:
                    message = ''
                    if self.edit_mode and self.edit_piece_set_id is not None:
                        if find_string('custom', self.edit_piece_set_id, -1):
                            message += "Custom piece"
                        elif find_string('wall', self.edit_piece_set_id, -1):
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
            if skip:
                message += " does not promote"
                self.set_caption(f"{prefix} {message}")
                return
            if not self.edit_mode or (self.move_history and ((m := self.move_history[-1]) and m.is_edit != 1)):
                message += " promotes"
            else:
                message += " is promoted"
            if hovered_square in self.promotion_area:
                promotion = self.promotion_area[hovered_square]
                if promotion.is_hidden:
                    message += " to ???"
                elif isinstance(promotion, AbstractPiece) and promotion.side not in {piece.side, Side.NONE}:
                    message += f" to {promotion}"
                else:
                    message += f" to {promotion.name}"
            elif self.edit_mode and self.edit_piece_set_id is not None:
                if find_string('custom', self.edit_piece_set_id, -1):
                    message += " to a custom piece"
                elif find_string('wall', self.edit_piece_set_id, -1):
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
                self.update_move(move)
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
                    issubclass(chained_move.movement_type or type, CastlingMovement) or
                    issubclass(chained_move.chained_move.movement_type or type, (CloneMovement, AutoActMovement))
                ):
                    # let's also not show all auto-actions because space in the caption is VERY limited
                    if issubclass(chained_move.chained_move.movement_type or type, AutoActMovement):
                        chained_move.chained_move = Unset
                        break
                    poss.extend((chained_move.pos_from, chained_move.pos_to))
                    chained_move = chained_move.chained_move
                if chained_move.chained_move is not Unset:
                    poss.extend((chained_move.pos_from, chained_move.pos_to))
                    # normally the check below would not mark auto-actions as Unset, but there is just not enough space.
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
            if self.show_drops and hovered_square in self.drop_area:
                drop_piece, drop_count = self.drop_area[hovered_square]
                if drop_piece:
                    if drop_count == 1:
                        self.set_caption(f"{prefix} {drop_piece} in the piece bank")
                    else:
                        self.set_caption(f"{prefix} {drop_piece} (×{drop_count}) in the piece bank")
                    return
                piece = self.no_piece
            if not isinstance(piece, NoPiece) and (self.edit_mode or not isinstance(piece, Border)):
                self.set_caption(f"{prefix} {piece} on {toa(piece.board_pos)}")
                return
        if self.edit_mode:
            self.set_caption(f"{prefix} Editing board")
            return
        message = self.get_status_string()
        if message:
            self.set_caption(f"{prefix} {message}")
        elif self.board_config['status_prefix'] == 0 and self.turn_data[0] > 0:
            self.set_caption(f"{prefix} {self.turn_data[1]} to move")
        elif self.board_config['status_prefix'] == 1 and self.turn_data[0] > 0:
            self.set_caption(f"[{prefix[1:-1] or '???'} to move]")
        else:
            self.set_caption(prefix)

    def try_drop(self, move: Move, update: bool = True) -> Move:
        if move.promotion:
            if move.placed_piece is not None:
                for i, piece in enumerate(self.captured_pieces[self.turn_side][::-1]):
                    if piece == move.placed_piece:
                        self.captured_pieces[self.turn_side].pop(-(i + 1))
                        break
            promotion_piece = self.promotion_piece
            self.promotion_piece = True
            self.replace(move.piece, move.promotion, move.movement_type, update)
            move = self.update_promotion_auto_actions(move)
            self.promotion_piece = promotion_piece
            return move
        if move.promotion is not Unset:
            return move
        if self.turn_side not in self.drops:
            return move
        if not self.captured_pieces[self.turn_side]:
            return move
        valid_drops = {}
        if not self.edit_mode:
            if not self.use_drops:
                return move
            valid_drops = self.moves[self.turn_side].get('drop', {}).get(move.piece.board_pos, {})
            if not valid_drops:
                return move
        side_drops = self.drops[self.turn_side]
        drop_list = []
        drop_type_list = []
        drop_indexes = {k: i for i, k in enumerate(side_drops)}
        for piece_type in sorted(self.captured_pieces[self.turn_side], key=lambda x: drop_indexes.get(x, 0)):
            if piece_type not in side_drops:
                continue
            piece_drops = set()
            if not self.edit_mode:
                if piece_type not in valid_drops:
                    continue
                if not valid_drops[piece_type]:
                    continue
                piece_drops = valid_drops[piece_type]
            drop_squares = side_drops[piece_type]
            if move.piece.board_pos not in drop_squares:
                continue
            drops = []
            for drop in drop_squares[move.piece.board_pos]:
                drop_type = type(drop) if isinstance(drop, AbstractPiece) else drop
                if not self.edit_mode and drop_type not in piece_drops:
                    continue
                drops.append(drop)
            drop_list.extend(drops)
            drop_type_list.extend(piece_type for _ in drops)
        if not drop_list:
            return move
        auto_drop = False
        if self.auto_moves and self.board_config['fast_drops']:
            if len(drop_list) == 1:
                auto_drop = True
            elif len(set(drop_type_list)) == 1:
                auto_drop = True
                for drop in drop_list[1:]:
                    if isinstance(drop, AbstractPiece) != isinstance(drop_list[0], AbstractPiece):
                        auto_drop = False
                    elif isinstance(drop, AbstractPiece):
                        auto_drop = drop.matches(drop_list[0])
                    else:
                        auto_drop = drop == drop_list[0]
                    if not auto_drop:
                        break
        if auto_drop:
            promotion_piece = self.promotion_piece
            self.promotion_piece = True
            drop = drop_list[0]
            if isinstance(drop, AbstractPiece):
                drop = drop.of(drop.side or self.turn_side).on(move.pos_to)
            else:
                drop = drop(board=self, board_pos=move.piece.board_pos, side=self.turn_side)
                drop.set_moves(None)
            move.set(promotion=drop, placed_piece=drop_type_list[0])
            for i, piece in enumerate(self.captured_pieces[self.turn_side][::-1]):
                if piece == move.placed_piece:
                    self.captured_pieces[self.turn_side].pop(-(i + 1))
                    break
            self.replace(move.piece, move.promotion, move.movement_type, update)
            move = self.update_promotion_auto_actions(move)
            self.promotion_piece = promotion_piece
            return move
        self.start_promotion(self.get_piece(move.piece.board_pos), drop_list, drop_type_list)
        return move

    def try_promotion(self, move: Move, update: bool = True) -> Move:
        promotion_piece = self.promotion_piece
        if move.promotion:
            self.promotion_piece = True
            promoted_from = move.promotion.promoted_from or move.piece.promoted_from
            if not isinstance(move.piece, NoPiece):
                promoted_from = promoted_from or type(move.piece)
            if type(move.promotion) != promoted_from:
                move.promotion.promoted_from = promoted_from
            self.replace(move.piece, move.promotion, move.movement_type, update)
            move = self.update_promotion_auto_actions(move)
            self.promotion_piece = promotion_piece
            return move
        if move.promotion is not Unset:
            return move
        if is_active(move.chained_move):
            return move
        if move.piece.side not in self.promotions:
            return move
        side_promotions = self.promotions[move.piece.side]
        if type(move.piece) not in side_promotions:
            return move
        promotion_squares = side_promotions[type(move.piece)]
        if not {move.pos_from, move.pos_to}.intersection(promotion_squares):
            return move
        has_promotion = False
        promotions = []
        for promotion_move in self.moves.get(self.turn_side, {}).get(move.pos_from, {}).get(move.pos_to, []):
            if promotion_move.promotion:
                promotions.append(promotion_move.promotion)
                has_promotion = True
            else:
                promotions.append(None)
        if not has_promotion:
            return move
        if self.auto_moves and self.board_config['fast_promotion'] and len(promotions) == 1:
            promotion = promotions[0]
            if promotion is None:
                move.set(promotion=Default)
                return move
            self.promotion_piece = True
            if isinstance(promotion, AbstractPiece):
                promotion = promotion.of(promotion.side or move.piece.side).on(move.pos_to)
            elif isinstance(promotion, type) and issubclass(promotion, AbstractPiece):
                promotion = promotion(board=self, board_pos=move.pos_to, side=move.piece.side)
                promotion.set_moves(None)
            promoted_from = promotion.promoted_from or move.piece.promoted_from
            if not isinstance(move.piece, NoPiece):
                promoted_from = promoted_from or type(move.piece)
            if type(promotion) != promoted_from:
                promotion.promoted_from = promoted_from
            move.set(promotion=promotion)
            self.replace(move.piece, move.promotion, move.movement_type, update)
            move = self.update_promotion_auto_actions(move)
            self.promotion_piece = promotion_piece
            return move
        self.start_promotion(move.piece, promotions)
        return move

    def get_promotions(self, move: Move, promotions: list[TypeOr[AbstractPiece] | None] | None = None):
        if promotions is None:
            if not is_active(move):
                yield move
                return
            chained_move = move
            while chained_move and is_active(chained_move.chained_move):
                chained_move = chained_move.chained_move
            if move.piece.side not in self.promotions:
                yield move
                return
            side_promotions = self.promotions[move.piece.side]
            if type(move.piece) not in side_promotions:
                yield move
                return
            promotion_squares = side_promotions[type(move.piece)]
            for square in (chained_move.pos_to, chained_move.pos_from):
                if square in promotion_squares:
                    promotions = promotion_squares[square]
                    break
        if not promotions:
            yield move
            return
        for piece in promotions:
            if piece is None:
                yield move
                continue
            elif isinstance(piece, AbstractPiece):
                piece = piece.of(piece.side or move.piece.side)
            else:
                piece = piece(board=self, side=move.piece.side)
                piece.set_moves(None)
            promoted_from = piece.promoted_from or move.piece.promoted_from
            if not isinstance(move.piece, NoPiece):
                promoted_from = promoted_from or type(move.piece)
            if type(piece) != promoted_from:
                piece.promoted_from = promoted_from
            copy_move = copy(move)
            chained_copy = copy_move
            while chained_copy and is_active(chained_copy.chained_move):
                chained_copy.set(chained_move=copy(chained_copy.chained_move))
                chained_copy = chained_copy.chained_move
            chained_copy.set(promotion=piece)
            yield copy_move

    def start_promotion(
        self,
        piece: AbstractPiece,
        promotions: list[TypeOr[AbstractPiece] | str | None],
        drops: list[type[AbstractPiece]] | None = None,
    ) -> None:
        if drops is None:
            drops = {}
        self.hide_moves()
        self.promotion_piece = piece
        piece_pos = piece.board_pos
        direction = (
            Side.WHITE if piece_pos[0] - self.notation_offset[1] < self.board_height / 2 else Side.BLACK
        ).direction
        area = min(len(promotions), self.board_height * self.board_width)
        area_height = min(area, max(self.board_height // 2, 1 + isqrt(area - 1)))
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
        total = 0
        for promotion, drop, pos in zip_longest(promotions, drops, area_squares):
            total += 1
            if total > len(area_squares):
                break
            background_sprite = Sprite("assets/util/square.png")
            background_sprite.color = self.color_scheme['promotion_area_color']
            background_sprite.position = self.get_screen_position(pos)
            background_sprite.scale = self.square_size / background_sprite.texture.width
            self.promotion_area_sprite_list.append(background_sprite)
            if total > area:
                continue
            no_promotion = False
            if promotion is None:
                no_promotion = True
                new_piece = piece.on(pos)
                promotion = type(promotion)
            elif not promotion:
                continue
            elif isinstance(promotion, AbstractPiece):
                new_piece = promotion.of(promotion.side or side).on(pos)
                promotion = type(promotion)
            else:
                new_piece = promotion(board=self, board_pos=pos, side=side)
                new_piece.set_moves(None)
            if not self.edit_mode or (self.move_history and ((m := self.move_history[-1]) and m.is_edit != 1)):
                promoted_from = new_piece.promoted_from or piece.promoted_from
                if not isinstance(piece, NoPiece):
                    promoted_from = promoted_from or type(piece)
                if type(new_piece) != promoted_from:
                    new_piece.promoted_from = promoted_from
            alternate_sprites = True if self.alternate_pieces == 0 else None
            if isinstance(new_piece, Piece):
                if issubclass(promotion, (King, CBKing)) and promotion not in self.piece_sets[side]:
                    self.update_piece(new_piece, asset_folder='other')
                elif self.edit_mode and self.edit_piece_set_id is not None and not isinstance(new_piece, Obstacle):
                    new_piece.should_hide = self.hide_edit_pieces
                    self.update_piece(new_piece, penultima_hide=False, alternate_sprite=alternate_sprites)
                else:
                    self.update_piece(new_piece, penultima_flip=True, alternate_sprite=alternate_sprites)
                new_piece_size = self.square_size
                if isinstance(new_piece, (Border, Wall, Void)):
                    new_piece_size *= 0.8
                if isinstance(new_piece, Shield):
                    new_piece_size *= 0.9
                new_piece.set_size(new_piece_size)
                new_piece.set_color(
                    self.color_scheme.get(
                        f"{new_piece.side.key()}piece_color",
                        self.color_scheme['piece_color']
                    ),
                    self.color_scheme['colored_pieces']
                )
                self.promotion_piece_sprite_list.append(new_piece.sprite)
            self.promotion_area[pos] = new_piece
            if no_promotion:
                self.promotion_area_drops[pos] = None
            elif drop is not None:
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
                self.replace(move.piece, move.promotion, move.movement_type)
                self.update_promotion_auto_actions(move)
                self.promotion_piece = None

    def end_promotion(self) -> None:
        self.promotion_piece = None
        self.promotion_area = {}
        self.promotion_area_drops = {}
        self.promotion_area_sprite_list.clear()
        self.promotion_piece_sprite_list.clear()

    def replace(
        self,
        piece: AbstractPiece,
        new_piece: AbstractPiece,
        promotion_type: type[BaseMovement] | None = None,
        update: bool = True,
    ) -> None:
        move_offset = 0
        if issubclass(promotion_type or type, DropMovement):
            move_offset = 1
        elif issubclass(promotion_type or type, ConvertMovement):
            move_offset = -1
        new_piece.board_pos = None
        new_piece = copy(new_piece)
        new_piece.set_moves(piece, move_offset)
        pos = self.get_absolute(piece.board_pos)
        if update and isinstance(self.pieces[pos[0]][pos[1]], Piece):
            self.piece_sprite_list.remove(self.pieces[pos[0]][pos[1]].sprite)
        self.pieces[pos[0]][pos[1]] = new_piece
        self.set_position(new_piece, piece.board_pos, update)
        if update and isinstance(new_piece, Piece):
            self.update_piece(new_piece)
            if not isinstance(piece, (NoPiece, Obstacle)):
                new_piece.set_color(
                    self.color_scheme.get(
                        f"{new_piece.side.key()}piece_color",
                        self.color_scheme['piece_color']
                    ),
                    self.color_scheme['colored_pieces']
                )
            new_piece.set_size(self.square_size)
            self.piece_sprite_list.append(new_piece.sprite)
        if type(new_piece) == self.past_custom_pieces.get(new_type := save_piece_type(type(new_piece))):
            self.custom_pieces[new_type] = self.past_custom_pieces[new_type]
            del self.past_custom_pieces[new_type]
        if update:
            old_color = self.highlight.color
            self.highlight.color = (0, 0, 0, 0)
            self.hide_moves()
            self.draw(0)
            self.highlight.color = old_color

    def color_pieces(self, side: Side = Side.ANY, color: tuple[int, int, int] | None = None) -> None:
        for piece in self.movable_pieces.get(side, sum(self.movable_pieces.values(), [])):
            if not isinstance(piece, Piece):
                continue
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
        for label_list in (self.row_label_list, self.col_label_list):
            for sprite in label_list:
                sprite.color = self.color_scheme['text_color']
        for sprite in self.board_sprite_list:
            position = self.get_board_position(sprite.position)
            sprite.color = self.color_scheme[f"{'light' if self.is_light_square(position) else 'dark'}_square_color"]
        for sprite_list in (self.promotion_area_sprite_list, self.drop_area_sprite_list):
            for sprite in sprite_list:
                sprite.color = self.color_scheme['promotion_area_color']
        for piece_list in (self.obstacles, self.promotion_area.values(), [x[0] for x in self.drop_area.values()]):
            for piece in piece_list:
                piece.set_color(
                    self.color_scheme.get(
                        f"{piece.side.key()}piece_color",
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
        penultima_flip: bool | None = None,
        penultima_hide: bool | None = None,
        alternate_sprite: bool | None = None,
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
        if alternate_sprite is None:
            if self.alternate_pieces > 0:
                alternate_sprite = self.alternate_pieces == piece.side.value
            else:
                alternate_sprite = self.alternate_pieces == -1
        piece.reload(
            is_hidden=is_hidden,
            asset_folder=asset_folder,
            file_name=file_name,
            alternate=alternate_sprite,
            flipped_horizontally=flip,
        )
        piece.set_size(self.square_size)

    def update_pieces(self) -> None:
        for piece in sum(self.movable_pieces.values(), []):
            if isinstance(piece, Piece):
                self.update_piece(piece)
        alternate_sprites = True if self.alternate_pieces == 0 else None
        for piece in self.promotion_area.values():
            if isinstance(piece, Piece):
                if isinstance(piece, (King, CBKing)) and type(piece) not in self.piece_sets[piece.side]:
                    self.update_piece(piece, asset_folder='other')
                elif self.edit_mode and self.edit_piece_set_id is not None and not isinstance(piece, Obstacle):
                    piece.should_hide = self.hide_edit_pieces
                    self.update_piece(piece, penultima_hide=False, alternate_sprite=alternate_sprites)
                else:
                    self.update_piece(piece, penultima_flip=True, alternate_sprite=alternate_sprites)
        self.update_drops()

    def update_sprite(
        self,
        sprite: Sprite | AbstractPiece,
        from_size: float,
        from_origin: tuple[float, float],
        from_width: int,
        from_height: int,
        from_cols: list[int],
        from_rows: list[int],
        from_offset: tuple[int, int],
        from_flip_mode: bool
    ) -> None:
        if isinstance(sprite, AbstractPiece):
            if not isinstance(sprite, Piece):
                return
            sprite.set_size(self.square_size)
            sprite = sprite.sprite
        else:
            sprite.scale = self.square_size / sprite.texture.width
        old_position = sprite.position
        sprite.position = self.get_screen_position(self.get_board_position(
            old_position, from_size, from_origin, from_width, from_height,
            from_cols, from_rows, from_offset, from_flip_mode
        ))

    def update_sprites(
        self,
        size: float,
        origin: tuple[float, float],
        width: int,
        height: int,
        border_cols: list[int],
        border_rows: list[int],
        offset: tuple[int, int],
        flip_mode: bool
    ) -> None:
        args = size, origin, width, height, border_cols, border_rows, offset, flip_mode
        selected_square = self.selected_square
        self.update_sprite(self.highlight, *args)
        self.update_sprite(self.selection, *args)
        if self.active_piece is not None:
            self.update_sprite(self.active_piece, *args)
        for sprite_list in (
            self.board_sprite_list,
            self.move_sprite_list,
            *self.movable_pieces.values(),
            self.promotion_area.values(),
            self.promotion_area_sprite_list,
            self.obstacles,
        ):
            for sprite in sprite_list:
                self.update_sprite(sprite, *args)
        self.update_drops()
        for label in self.row_label_list:
            position = label.position
            label.font_size = self.square_size / max(2, len(label.text))
            label.x, label.y = self.get_screen_position(
                self.get_board_position(position, *args, between_cols=True), between_cols=True
            )
        for label in self.col_label_list:
            position = label.position
            label.font_size = self.square_size / max(2, len(label.text))
            label.x, label.y = self.get_screen_position(
                self.get_board_position(position, *args, between_rows=True), between_rows=True
            )
        self.deselect_piece()
        self.select_piece(selected_square)
        if self.highlight_square:
            self.update_highlight(self.highlight_square)
            self.hovered_square = None
        else:
            self.update_highlight(self.get_board_position(self.highlight.position, *args))
        if self.skip_mouse_move == 2:
            self.skip_mouse_move = 1

    def update_alternate_sprites(self, from_side: Side = Side.NONE) -> None:
        if from_side == Side.NONE:
            self.update_pieces()
        elif self.alternate_swap and self.alternate_pieces > 0:
            new_side = self.turn_side if self.alternate_pieces == from_side.value else self.turn_side.opponent()
            if self.alternate_pieces != new_side.value:
                self.alternate_pieces = new_side.value
                self.update_pieces()

    def update_drops(self, show: bool | None = None) -> None:
        if show is not None:
            if self.show_drops == show:
                return
            self.show_drops = show
        self.drop_area = {}
        self.drop_area_sprite_list.clear()
        self.drop_piece_sprite_list.clear()
        self.drop_piece_label_list.clear()
        no_drops = True
        if self.show_drops:
            origins = {
                Side.WHITE: (0, 0),
                Side.BLACK: (self.board_height - 1, self.board_width - 1),
            }
            label_kwargs = {
                'anchor_x': 'center',
                'anchor_y': 'center',
                'font_name': 'Courier New',
                'bold': True,
                'color': self.color_scheme['text_color'],
            }
            piece_scale_ratio = 0.66
            label_scale_ratio = 0.33
            for side, pieces in self.captured_pieces.items():
                if side not in origins:
                    continue
                if not pieces:
                    continue
                piece_counts = {}
                for piece_type in pieces:
                    piece_counts[piece_type] = piece_counts.get(piece_type, 0) + 1
                if not piece_counts:
                    continue
                direction = side.direction
                area = min(len(piece_counts), (self.board_height // 2) * self.board_width)
                area_width = min(ceil(len(piece_counts) / self.board_width), 1) * self.board_width
                area_height = ceil(area / area_width)
                area_origin = origins[side]
                area_squares = []
                for row, col in product(range(area_height), range(area_width)):
                    current_row = area_origin[0] + direction(row)
                    current_col = area_origin[1] + direction(col)
                    area_squares.append((current_row, current_col))
                total = 0
                for piece_type, pos in zip_longest(piece_counts, area_squares):
                    total += 1
                    if total > len(area_squares):
                        break
                    background_sprite = Sprite("assets/util/square.png")
                    background_sprite.color = self.color_scheme['promotion_area_color']
                    background_sprite.position = self.get_screen_position(pos)
                    background_sprite.scale = self.square_size / background_sprite.texture.width
                    self.drop_area_sprite_list.append(background_sprite)
                    new_piece = None
                    if not piece_type:
                        self.drop_area[pos] = (None, 0)
                        continue
                    elif issubclass(piece_type, AbstractPiece):
                        new_piece = piece_type(board=self, board_pos=pos, side=side)
                        new_piece.set_moves(None)
                    alternate_sprites = True if self.alternate_pieces == 0 else None
                    if isinstance(new_piece, Piece):
                        if isinstance(new_piece, (King, CBKing)) and piece_type not in self.piece_sets[side]:
                            self.update_piece(new_piece, asset_folder='other')
                        elif (
                            self.edit_mode and self.edit_piece_set_id is not None
                            and not isinstance(new_piece, Obstacle)
                        ):
                            new_piece.should_hide = self.hide_edit_pieces
                            self.update_piece(new_piece, penultima_hide=False, alternate_sprite=alternate_sprites)
                        else:
                            self.update_piece(new_piece, penultima_flip=True, alternate_sprite=alternate_sprites)
                        new_piece_size = self.square_size
                        if isinstance(new_piece, (Border, Wall, Void)):
                            new_piece_size *= 0.8
                        if isinstance(new_piece, Shield):
                            new_piece_size *= 0.9
                        new_piece.set_size(new_piece_size * piece_scale_ratio)
                        new_piece.set_color(
                            self.color_scheme.get(
                                f"{new_piece.side.key()}piece_color",
                                self.color_scheme['piece_color']
                            ),
                            self.color_scheme['colored_pieces']
                        )
                        new_piece.sprite.position = (
                            new_piece.sprite.position[0] - self.square_size * (1 - piece_scale_ratio) / 2,
                            new_piece.sprite.position[1] + self.square_size * (1 - piece_scale_ratio) / 2,
                        )
                        self.drop_piece_sprite_list.append(new_piece.sprite)
                    text = str(piece_counts[piece_type])
                    text_pos = (
                        background_sprite.position[0] + self.square_size * label_scale_ratio / 2,
                        background_sprite.position[1] - self.square_size * label_scale_ratio / 2,
                    )
                    font_size = self.square_size / len(text) * label_scale_ratio
                    self.drop_piece_label_list.append(Text(text, *text_pos, font_size=font_size, **label_kwargs))
                    self.drop_area[pos] = (new_piece, piece_counts[piece_type])
                    no_drops = False
        if show is not None:
            if no_drops:
                self.show_drops = False
            else:
                self.deselect_piece()
            if self.is_started and show != no_drops:
                self.log(f"Info: Piece banks {'shown' if show else 'hidden'}", False)
                self.update_caption()

    def flip_board(self) -> None:
        self.flip_mode = not self.flip_mode
        self.update_sprites(
            self.square_size, self.origin,
            self.visual_board_width, self.visual_board_height,
            self.border_cols, self.border_rows,
            self.notation_offset, not self.flip_mode
        )

    def is_trickster_mode(self) -> bool:
        return self.trickster_color_index != 0

    def update_trickster_mode(self) -> None:
        if not self.is_trickster_mode():
            self.trickster_color_delta = 0
            return  # trickster mode is disabled
        if self.trickster_color_delta > 1 / 11:
            self.trickster_color_delta %= 1 / 11  # ah yes, modulo assignment. derpy step-brother of the walrus operator
            self.trickster_color_index = self.trickster_color_index % len(trickster_colors) + 1
            self.update_colors()
        active_list = [self.active_piece.sprite] if self.active_piece is not None else []
        for sprite_list in (self.piece_sprite_list, self.promotion_piece_sprite_list, active_list):
            for sprite in sprite_list:
                pos = self.get_board_position(sprite.position)
                direction = 1 if self.is_light_square(pos) else -1
                delta = self.trickster_angle_delta / 11 * 360 * direction
                if not self.edit_mode:
                    side = self.get_side(pos)
                    if self.game_over:
                        if self.win_side == side:
                            delta *= 2
                        elif self.win_side == side.opponent():
                            delta = 0
                    elif self.check_side == side:
                        delta /= 1.25
                    elif self.check_side == side.opponent():
                        delta *= 1.5
                sprite.angle += delta
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
        active_list = [self.active_piece.sprite] if self.active_piece is not None else []
        for sprite_list in (self.piece_sprite_list, self.promotion_piece_sprite_list, active_list):
            for sprite in sprite_list:
                sprite.angle = 0

    def update_labels(
        self,
        width: int = 0,
        height: int = 0,
        border_cols: list[int] | None = None,
        border_rows: list[int] | None = None,
        offset: tuple[int, int] | None = None,
    ):
        width, height = width or self.visual_board_width, height or self.visual_board_height
        border_cols = self.border_cols if border_cols is None else border_cols
        border_rows = self.border_rows if border_rows is None else border_rows
        offset = self.notation_offset if offset is None else offset

        self.row_label_list.clear()
        self.col_label_list.clear()

        position_kwargs = {
            'width': width,
            'height': height,
            'border_cols': border_cols,
            'border_rows': border_rows,
            'offset': offset,
        }

        label_kwargs = {
            'anchor_x': 'center',
            'anchor_y': 'center',
            'font_name': 'Courier New',
            'bold': True,
            'color': self.color_scheme['text_color'],
        }

        for row in range(self.board_height):
            rel_row = row + self.notation_offset[1]
            text = str(rel_row + 1)
            font_size = self.square_size / max(2, len(text))
            label_pos_kwargs = copy(position_kwargs)
            label_pos_kwargs['between_cols'] = True
            label_cols = [-1, *(col - self.notation_offset[0] for col in self.border_cols), self.board_width]
            label_poss = []
            for i, col in enumerate(label_cols):
                if not self.extra_labels and col not in {-1, self.board_width}:
                    continue
                label_poss.append(self.get_screen_position(self.get_relative((row, col)), **label_pos_kwargs))
            self.row_label_list.extend(Text(text, *pos, font_size=font_size, **label_kwargs) for pos in label_poss)

        for col in range(self.board_width):
            rel_col = col + self.notation_offset[0]
            text = b26(rel_col + (0 if rel_col < 0 else 1))
            font_size = self.square_size / max(2, len(text))
            label_pos_kwargs = copy(position_kwargs)
            label_pos_kwargs['between_rows'] = True
            label_rows = [-1, *(row - self.notation_offset[1] for row in self.border_rows), self.board_height]
            label_poss = []
            for i, row in enumerate(label_rows):
                if not self.extra_labels and row not in {-1, self.board_height}:
                    continue
                label_poss.append(self.get_screen_position(self.get_relative((row, col)), **label_pos_kwargs))
            self.col_label_list.extend(Text(text, *pos, font_size=font_size, **label_kwargs) for pos in label_poss)

    def resize_board(
        self,
        width: int = 0,
        height: int = 0,
        border_cols: list[int] | None = None,
        border_rows: list[int] | None = None,
        notation_offset_x: int | None = None,
        notation_offset_y: int | None = None,
        update: bool = True,
    ) -> None:
        width, height = width or self.board_width, height or self.board_height
        border_cols = self.border_cols if border_cols is None else border_cols
        border_rows = self.border_rows if border_rows is None else border_rows
        notation_offset_x = self.notation_offset[0] if notation_offset_x is None else notation_offset_x
        notation_offset_y = self.notation_offset[1] if notation_offset_y is None else notation_offset_y
        if (
            self.game_loaded and self.board_width == width and self.board_height == height
            and self.border_cols == border_cols and self.border_rows == border_rows
            and self.notation_offset[0] == notation_offset_x and self.notation_offset[1] == notation_offset_y
        ):
            return

        old_highlight = self.get_board_position(self.highlight.position) if self.highlight_square else None
        self.board_width, self.board_height = width, height
        old_offset = self.notation_offset
        self.notation_offset = (notation_offset_x, notation_offset_y)
        old_cols, old_rows = self.border_cols, self.border_rows
        self.border_cols, self.border_rows = sorted(border_cols), sorted(border_rows)
        while self.border_cols and self.border_cols[0] - self.notation_offset[0] <= 0:
            self.border_cols.pop(0)
        while self.border_rows and self.border_rows[0] - self.notation_offset[1] <= 0:
            self.border_rows.pop(0)
        while self.border_cols and self.border_cols[-1] - self.notation_offset[0] >= self.board_width:
            self.border_cols.pop()
        while self.border_rows and self.border_rows[-1] - self.notation_offset[1] >= self.board_height:
            self.border_rows.pop()
        old_width, old_height = self.visual_board_width, self.visual_board_height
        self.visual_board_width = self.board_width + len(self.border_cols)
        self.visual_board_height = self.board_height + len(self.border_rows)
        old_board_size = old_width, old_height

        self.board_sprite_list.clear()

        position_kwargs = {
            'width': old_width,
            'height': old_height,
            'border_cols': old_cols,
            'border_rows': old_rows,
            'offset': old_offset,
        }

        for row, col in product(range(self.board_height), range(self.board_width)):
            pos = self.get_relative((row, col))
            sprite = Sprite("assets/util/square.png")
            sprite.color = self.color_scheme[f"{'light' if self.is_light_square(pos) else 'dark'}_square_color"]
            sprite.position = self.get_screen_position(pos, **position_kwargs)
            sprite.scale = self.square_size / sprite.texture.width
            self.board_sprite_list.append(sprite)

        self.update_labels(**position_kwargs)

        self.reset_drops()
        self.reset_promotions()

        for row in range(len(self.pieces), self.board_height):
            self.pieces += [[]]
        for row in range(self.board_height, len(self.pieces)):
            for col in range(len(self.pieces[row])):
                if isinstance(self.pieces[row][col], Piece):
                    self.piece_sprite_list.remove(self.pieces[row][col].sprite)
        self.pieces = self.pieces[:self.board_height]
        for row in range(self.board_height):
            for col in range(min(len(self.pieces[row]), self.board_width)):
                self.pieces[row][col].board_pos = self.get_relative((row, col))
            for col in range(len(self.pieces[row]), self.board_width):
                self.pieces[row].append(NoPiece(self, board_pos=self.get_relative((row, col))))
                if isinstance(self.pieces[row][col], Piece):
                    self.piece_sprite_list.append(self.pieces[row][col].sprite)
            for col in range(self.board_width, len(self.pieces[row])):
                if isinstance(self.pieces[row][col], Piece):
                    self.piece_sprite_list.remove(self.pieces[row][col].sprite)
            self.pieces[row] = self.pieces[row][:self.board_width]

        if (
            self.game_loaded or self.board_width != default_board_width or self.board_height != default_board_height
            or self.border_cols or self.border_rows or self.notation_offset != (0, 0)
        ):
            if self.board_width != old_width or self.board_height != old_height:
                self.log(f"Info: Changed board size to {self.board_width}x{self.board_height}")
            if self.notation_offset != old_offset:
                offset_string = ', '.join(f"{x:+}" if x else "0" for x in self.notation_offset)
                self.log(f"Info: Changed notation offset to ({offset_string})")
            if self.border_cols != old_cols:
                if self.border_cols:
                    s26 = lambda x: b26(x + (0 if x < 0 else 1))
                    file_splits = list(f'{s26(x)}/{s26(x + 1)}' for x in self.border_cols)
                    self.log(f"Info: Changed file borders to {', '.join(file_splits)}")
                else:
                    self.log("Info: Removed file borders")
            if self.border_rows != old_rows:
                if self.border_rows:
                    rank_splits = list(f'{x}/{x + 1}' for x in self.border_rows)
                    self.log(f"Info: Changed rank borders to {', '.join(rank_splits)}")
                else:
                    self.log("Info: Removed rank borders")
            self.update_sprites(
                self.square_size, self.origin,
                old_width, old_height,
                old_cols, old_rows,
                old_offset, self.flip_mode
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
                    self.notation_offset,
                    self.flip_mode
                )
            else:
                self.resize(new_width, new_height)
            self.update_highlight(old_highlight)

        if update and self.game_loaded:
            self.clear_theoretical_moves()
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
        if self.square_size == square_size:
            self.log(f"Info: Resized to {self.width}x{self.height}")
        else:
            self.log(f"Info: Resized to {self.width}x{self.height} (Size: {round(square_size, 5)}px)")
        self.set_location(x - (self.width - old_width) // 2, y - (self.height - old_height) // 2)
        if not self.fullscreen:
            self.windowed_size = self.width, self.height
            self.windowed_square_size = min(
                self.width / (self.visual_board_width + 2),
                self.height / (self.visual_board_height + 2)
            )
        self.set_visible(True)

    def to_windowed(self) -> None:
        self.log("Info: Fullscreen disabled", False)
        self.set_fullscreen(False)
        if self.size != self.windowed_size:
            self.resize(*self.windowed_size)
        else:
            self.log(f"Info: Resized to {self.width}x{self.height}", False)

    def to_fullscreen(self) -> None:
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
        if self.board_config['update_mode'] < 0 and not self.is_started:
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
        self.clear()
        for label_list in (self.row_label_list, self.col_label_list):
            for label in label_list:
                label.draw()
        self.board_sprite_list.draw()
        if not self.promotion_area and not self.show_drops:
            draw_sprite(self.highlight)
            draw_sprite(self.selection)
        self.move_sprite_list.draw()
        self.piece_sprite_list.draw()
        self.type_sprite_list.draw()
        if self.active_piece:
            draw_sprite(self.active_piece.sprite)
        self.promotion_area_sprite_list.draw()
        self.drop_area_sprite_list.draw()
        if self.promotion_area or self.show_drops:
            draw_sprite(self.highlight)
        self.promotion_piece_sprite_list.draw()
        self.drop_piece_sprite_list.draw()
        for label in self.drop_piece_label_list:
            label.draw()

    def on_update(self, delta_time: float) -> None:
        if self.is_trickster_mode():
            self.trickster_color_delta += delta_time
            self.trickster_angle_delta += delta_time
        self.save_interval += delta_time
        self.sync_interval += delta_time
        if self.board_config['autosave_time'] and self.save_interval >= self.board_config['autosave_time']:
            self.save_interval %= self.board_config['autosave_time']
            self.auto_save()
        if self.board_config['sync_time'] and self.sync_interval >= self.board_config['sync_time']:
            self.sync_interval %= self.board_config['sync_time']
            self.sync(get=True)

    def on_resize(self, width: int, height: int) -> None:
        self.skip_mouse_move = 2
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
            self.notation_offset,
            self.flip_mode,
        )
        if self.is_started:
            self.draw(0)

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
        if self.sync(get=True) is not None:
            return
        self.piece_was_selected = False
        if buttons & MOUSE_BUTTON_LEFT:
            self.held_buttons = MOUSE_BUTTON_LEFT
            if self.show_drops:
                return
            if self.game_over and not self.edit_mode:
                return
            pos = self.get_board_position((x, y))
            if self.promotion_piece:
                if pos in self.promotion_area:
                    last_chain_move = None
                    chained_move = self.move_history[-1]
                    while chained_move.chained_move:
                        if chained_move.promotion is Unset:
                            break
                        last_chain_move = chained_move
                        chained_move = chained_move.chained_move
                    if pos in self.promotion_area_drops and (drop := self.promotion_area_drops[pos]) is not None:
                        chained_move.set(placed_piece=drop)
                        for i, piece in enumerate(self.captured_pieces[self.turn_side][::-1]):
                            if piece == drop:
                                self.captured_pieces[self.turn_side].pop(-(i + 1))
                                break
                        self.update_en_passant_markers(chained_move)
                    if pos not in self.promotion_area_drops or self.promotion_area_drops[pos] is not None:
                        chained_move.set(promotion=self.promotion_area[pos])
                        self.replace(self.promotion_piece, self.promotion_area[pos], chained_move.movement_type)
                    else:
                        chained_move.set(promotion=Default)
                    chained_move = self.update_promotion_auto_actions(chained_move)
                    if last_chain_move:
                        last_chain_move.chained_move = chained_move
                    else:
                        self.move_history[-1] = chained_move
                    self.end_promotion()
                    current_move = chained_move
                    while chained_move:
                        move_type = (
                            'Edit' if chained_move.is_edit
                            else 'Drop' if chained_move.movement_type == DropMovement
                            else 'Move'
                        )
                        self.log(f"{move_type}: {chained_move}")
                        if chained_move.chained_move:
                            chained_move.chained_move = self.move(chained_move.chained_move)
                        chained_move = chained_move.chained_move
                        if chained_move:
                            self.update_auto_markers(chained_move)
                            chained_move.set(piece=copy(chained_move.piece))
                            if chained_move.swapped_piece:
                                chained_move.set(swapped_piece=copy(chained_move.swapped_piece))
                    self.unload_end_data()
                    old_turn_side = self.turn_side
                    if not current_move.is_edit:
                        self.shift_ply(+1)
                        self.load_pieces()
                        self.load_check()
                        self.update_end_data(self.move_history[-1])
                    else:
                        self.load_pieces()
                        self.load_check()
                        self.update_end_data()
                    self.load_moves()
                    self.reload_end_data()
                    if old_turn_side != self.turn_side:
                        self.update_alternate_sprites(old_turn_side)
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
                and pos not in self.moves.get(self.turn_side, {}).get(self.selected_square, {})
                and not self.not_a_piece(pos)
                and (
                    (piece := self.get_piece(pos)).side == self.turn_side
                    or isinstance(piece, Shared)
                    or self.edit_mode
                )
            ):
                self.deselect_piece()  # just in case we had something previously selected
                self.select_piece(pos)
                self.piece_was_selected = True
            self.square_was_clicked = True
            self.clicked_square = pos
        if buttons & MOUSE_BUTTON_RIGHT:
            self.held_buttons = MOUSE_BUTTON_RIGHT
            if self.show_drops:
                return
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
                    piece = self.get_piece(self.selected_square)
                    if isinstance(piece, Piece):
                        piece.sprite.position = x, y
        elif self.skip_mouse_move == 1:
            self.skip_mouse_move = 0

    def on_mouse_release(self, x: int, y: int, buttons: int, modifiers: int) -> None:
        if not self.is_active:
            return
        held_buttons = buttons & self.held_buttons
        self.held_buttons = 0
        if not held_buttons:
            return
        if self.show_drops:
            self.update_drops(False)
            return
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
                        move.set(captured=self.get_piece(pos))
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
                        move.set(captured=self.get_piece(pos))
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
                            if isinstance(piece, AbstractPiece):
                                piece = piece.of(piece.side or side).on(pos)
                            else:
                                piece = piece(board=self, board_pos=move.pos_to, side=side)
                                piece.set_moves(None)
                            promoted_from = piece.promoted_from or move.piece.promoted_from
                            if not isinstance(move.piece, NoPiece):
                                promoted_from = promoted_from or type(move.piece)
                            if type(piece) != promoted_from:
                                piece.promoted_from = promoted_from
                            move.set(promotion=piece)
                        elif len(self.edit_promotions[side]) > 1:
                            move.set(promotion=Unset)
                        else:
                            self.deselect_piece()
                            return
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
                        if isinstance(piece, AbstractPiece):
                            piece = piece.of(piece.side or side).on(pos)
                        else:
                            piece = piece(board=self, board_pos=move.pos_to, side=side)
                        move.set(promotion=piece)
                    elif len(self.edit_promotions[side]) > 1:
                        move.set(promotion=Unset)
                    else:
                        self.deselect_piece()
                        return
                else:
                    if self.not_a_piece(pos):
                        self.deselect_piece()
                        return
                    move.set(pos_from=pos, pos_to=None, piece=self.get_piece(pos))
            else:
                return
            move = self.move(move)
            if move.promotion is Unset and move.movement_type == DropMovement and not self.promotion_piece:
                return
            self.update_auto_markers(move)
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
                move = Move(pos_from=None, pos_to=pos, movement_type=DropMovement, piece=piece, promotion=Unset)
                move = self.try_drop(move)
                if self.promotion_piece:
                    self.move_history.append(move)
                    self.update_caption()
                elif move.promotion:
                    self.move_history.append(move)
                    self.log(f"Drop: {move}")
                    if move.chained_move:
                        move.chained_move = self.move(move.chained_move)
                    chained_move = move.chained_move
                    if chained_move:
                        self.update_auto_markers(chained_move)
                        chained_move.set(piece=copy(chained_move.piece))
                        if chained_move.swapped_piece:
                            chained_move.set(swapped_piece=copy(chained_move.swapped_piece))
                    while chained_move:
                        move_type = (
                            'Edit' if chained_move.is_edit
                            else 'Drop' if chained_move.movement_type == DropMovement
                            else 'Move'
                        )
                        self.log(f"{move_type}: {chained_move}")
                        if chained_move.chained_move:
                            chained_move.chained_move = self.move(chained_move.chained_move)
                        chained_move = chained_move.chained_move
                        if chained_move:
                            self.update_auto_markers(chained_move)
                            chained_move.set(piece=copy(chained_move.piece))
                            if chained_move.swapped_piece:
                                chained_move.set(swapped_piece=copy(chained_move.swapped_piece))
                    self.unload_end_data()
                    old_turn_side = self.turn_side
                    if not move.is_edit:
                        self.shift_ply(+1)
                        self.load_pieces()
                        self.load_check()
                        self.update_end_data(self.move_history[-1])
                    else:
                        self.load_pieces()
                        self.load_check()
                        self.update_end_data()
                    self.load_moves()
                    self.reload_end_data()
                    if old_turn_side != self.turn_side:
                        self.update_alternate_sprites(old_turn_side)
                    self.compare_history()
                    self.advance_turn()
                return
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
                chained_move = self.chain_start
                poss = []
                while chained_move:
                    poss.extend((chained_move.pos_from, chained_move.pos_to))
                    chained_move = chained_move.chained_move
                chained_move = move
                while chained_move and chained_move.chained_move and (
                    issubclass(chained_move.movement_type or type, CastlingMovement) or
                    issubclass(chained_move.chained_move.movement_type or type, (CloneMovement, AutoActMovement))
                ):
                    poss.extend((chained_move.pos_from, chained_move.pos_to))
                    chained_move = chained_move.chained_move
                poss.extend((chained_move.pos_from, chained_move.pos_to))
                next_chained = chained_move.chained_move
                if next_chained and (movement_type := next_chained.movement_type) and not (
                    issubclass(movement_type, AutoCaptureMovement) and (
                        (ch_piece := next_chained.piece) and (ch_piece.side == self.turn_side.opponent())
                    ) or issubclass(movement_type, ConvertMovement) and (
                        (ch_promo := next_chained.promotion) and (ch_promo.side == self.turn_side.opponent())
                    )
                ) or self.chain_moves.get(self.turn_side, {}).get(tuple(poss)):
                    chained_move.chained_move = Unset  # do not chain moves since we are selecting chained move manually
                    is_final = False
                else:
                    is_final = True
                move = self.clear_promotion_auto_actions(move)  # clear the old auto-actions and unset promotion choices
                move = self.move(move)
                self.update_auto_markers(move, True)
                move = self.update_auto_actions(move, self.turn_side.opponent())
                chained_move = move
                while chained_move:
                    chained_move.set(piece=copy(chained_move.piece))
                    if chained_move.swapped_piece:
                        chained_move.set(swapped_piece=copy(chained_move.swapped_piece))
                    if self.promotion_piece is None:
                        if chained_move.promotion is Unset:
                            chained_move.set(promotion=Default)
                        self.log(f"Move: {chained_move}")
                    if chained_move.chained_move:
                        chained_move.chained_move = self.move(chained_move.chained_move)
                        self.update_auto_markers(chained_move.chained_move)
                    chained_move = chained_move.chained_move
                if self.chain_start is None:
                    self.chain_start = deepcopy(move)
                    self.move_history.append(self.chain_start)
                else:
                    last_move = self.chain_start
                    while last_move.chained_move:
                        last_move = last_move.chained_move
                    last_move.chained_move = deepcopy(move)
                self.unload_end_data()
                if not is_final and not self.promotion_piece:
                    self.load_pieces()
                    self.load_moves()
                    self.show_moves(with_markers=False)
                    self.draw(0)
                    self.select_piece(move.pos_to)
                    if self.auto_moves and (
                        self.board_config['fast_moves'] or self.board_config['fast_chain']
                    ) and not self.game_over:
                        self.try_auto()
                else:
                    self.chain_start = None
                    if self.promotion_piece:
                        self.load_pieces()
                    else:
                        old_turn_side = self.turn_side
                        self.shift_ply(+1)
                        self.load_pieces()
                        self.load_check()
                        self.update_end_data(self.move_history[-1])
                        self.load_moves()
                        self.reload_end_data()
                        if old_turn_side != self.turn_side:
                            self.update_alternate_sprites(old_turn_side)
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
            start_row, start_col = self.get_absolute(self.get_board_position(self.highlight.position))
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
            row, col = self.get_relative((row, col))
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
            else:
                start_row, start_col = self.get_absolute((start_row, start_col))
            for row, col in product(range(self.board_height), range(self.board_width)):
                if not self.highlight.alpha or row or col:
                    current_col = (start_col + col * direction) % self.board_width
                    row_shift = int(current_col < start_col) if direction == 1 else -int(current_col > start_col)
                    current_row = (start_row + row * direction + row_shift) % self.board_height
                    current_row, current_col = self.get_relative((current_row, current_col))
                    if (current_row, current_col) in positions:
                        self.update_highlight((current_row, current_col))
                        self.highlight_square = (current_row, current_col)
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
                self.quick_save()
            elif modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Save as
                if self.fullscreen:
                    self.to_windowed()
                self.deactivate()
                self.draw(0)
                self.log("Info: Selecting a file to save to", False)
                if not self.save_name and self.load_name:
                    save_path = save_menu(self.load_path, self.load_name)
                else:
                    save_path = save_menu(self.save_path, self.save_name or get_file_name('save', 'json'))
                if save_path:
                    self.save(save_path)
                else:
                    self.log("Info: Saving cancelled", False)
                self.activate()
        if symbol == key.R:  # Restart
            if modifiers & key.MOD_ALT:  # Reload save
                which = 'saved' if modifiers & key.MOD_SHIFT else 'loaded'
                if modifiers & key.MOD_SHIFT:
                    path = join(self.save_path, self.save_name) if self.save_path and self.save_name else None
                else:
                    path = join(self.load_path, self.load_name) if self.load_path and self.load_name else None
                path = normalize(path) if path else None
                if not path:
                    self.log(f"Error: No file {which} yet")
                elif modifiers & key.MOD_ACCEL:  # Reload save data
                    data = self.save_data if modifiers & key.MOD_SHIFT else self.load_data
                    if data is not None:
                        state = '' if isfile(path) else '(deleted) '
                        self.log(f"Info: Loading from last {which} state in {state}\"{path}\"")
                        if self.load_board(data):
                            self.sync(post=True)
                elif isfile(path):  # Reload save file
                    self.log(f"Info: Loading from last {which} file")
                    if self.load(path):
                        if not self.save_imported:
                            self.reset_custom_data(True)
                            self.reset_board()
                            self.log_special_modes()
                else:
                    self.log(f"Error: Last {which} file not found at \"{path}\"")
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
                self.load_chaos_sets(1 + bool(modifiers & key.MOD_ALT), bool(modifiers & key.MOD_ACCEL))
            elif modifiers & key.MOD_ACCEL:  # Config
                self.save_config()
        if symbol == key.X:
            if modifiers & (key.MOD_SHIFT | key.MOD_ALT):  # Extreme chaos mode
                self.load_chaos_sets(3 + bool(modifiers & key.MOD_ALT), bool(modifiers & key.MOD_ACCEL))
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
        if symbol == key.COMMA and modifiers & key.MOD_ACCEL and not partial_move:  # Offset notation (-)
            offset_x = self.notation_offset[0] - (0 if modifiers & key.MOD_ALT else 1)
            offset_y = self.notation_offset[1] - (1 if modifiers & key.MOD_ALT else 0)
            self.resize_board(notation_offset_x=offset_x, notation_offset_y=offset_y)
        if symbol == key.PERIOD and modifiers & key.MOD_ACCEL and not partial_move:  # Offset notation (+)
            offset_x = self.notation_offset[0] + (0 if modifiers & key.MOD_ALT else 1)
            offset_y = self.notation_offset[1] + (1 if modifiers & key.MOD_ALT else 0)
            self.resize_board(notation_offset_x=offset_x, notation_offset_y=offset_y)
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
                self.resize_board(
                    self.board_height, self.board_width,
                    self.border_rows, self.border_cols,
                    self.notation_offset[1],
                    self.notation_offset[0],
                )
            else:  # Reset board size
                self.resize_board(default_board_width, default_board_height, [], [], 0, 0)
        if symbol == key.F11:  # Full screen (toggle)
            self.to_windowed() if self.fullscreen else self.to_fullscreen()
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
                self.save_log()
                self.save_debug_log()
                self.quick_save()
                if modifiers & key.MOD_ACCEL:
                    self.save_verbose_log()
                if modifiers & key.MOD_SHIFT:
                    self.save_debug_data()
            elif modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Erase custom data
                self.log("Info: Clearing custom data")
                self.reset_custom_data()
                self.log("Info: Starting new game", bool(self.hide_pieces))
                self.reset_board()
            elif modifiers & key.MOD_SHIFT:  # Empty board
                self.empty_board()
            elif modifiers & key.MOD_ACCEL and not partial_move:  # Edit mode (toggle)
                self.edit_mode = not self.edit_mode
                self.log(f"Mode: {'EDIT' if self.edit_mode else 'PLAY'}", False)
                self.deselect_piece()
                self.update_drops(False)
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
        if symbol == key.O:
            if modifiers & key.MOD_ALT:  # Online play
                if self.fullscreen:
                    self.to_windowed()
                self.deactivate()
                self.draw(0)
                if modifiers & key.MOD_SHIFT:  # Request interval
                    self.log(f"Info: Setting request interval", False)
                    new_interval = prompt_integer(
                        prompt="Request Interval (seconds)",
                        default=self.board_config['sync_time'],
                        minimum=0,
                    )
                    if new_interval is not None:
                        self.sync_interval = 0.0
                        self.board_config['sync_time'] = new_interval
                        if new_interval:
                            self.log(f"Info: Request interval set to {new_interval} seconds", False)
                        else:
                            self.log(f"Info: Request interval disabled", False)
                    else:
                        self.log("Info: Request interval change cancelled", False)
                elif modifiers & key.MOD_ALT:  # Server address
                    self.log(f"Info: Setting server address", False)
                    current_address = f"{self.board_config['sync_host']}:{self.board_config['sync_port']}"
                    new_address = prompt_string(prompt="Multiplayer Server Address", default=current_address)
                    if new_address is not None:
                        parts = new_address.split('://')
                        if parts:
                            parts = parts[-1].split(':')
                            if parts[0]:
                                self.board_config['sync_host'] = parts[0]
                            if len(parts) > 1 and parts[1]:
                                try:
                                    port = int(parts[1])
                                    if not (0 < port < 65536):
                                        raise ValueError
                                    self.board_config['sync_port'] = port
                                except ValueError:
                                    self.log("Error: Invalid port number", False)
                            new_address = f"http://{self.board_config['sync_host']}:{self.board_config['sync_port']}"
                            self.log(f"Info: Server address set to {new_address}", False)
                        if not self.board_config['sync_data']:
                            self.board_config['sync_data'] = True
                            self.log("Info: Online mode enabled")
                        self.sync(get=True, post=True)
                    else:
                        self.log("Info: Server connection cancelled", False)
                self.activate()
            elif modifiers & key.MOD_SHIFT and not self.promotion_piece:  # Toggle drop banks
                self.update_drops(not self.show_drops)
            elif modifiers & key.MOD_ACCEL and not partial_move:  # Toggle drops (Crazyhouse mode)
                self.use_drops = not self.use_drops
                self.log(f"Info: Drops {'enabled' if self.use_drops else 'disabled'}")
                self.future_move_history = []  # we don't know if we can redo all the future moves anymore so clear them
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
            if modifiers & key.MOD_ALT:  # Reload save (with history)
                which = 'saved' if modifiers & key.MOD_SHIFT else 'loaded'
                if modifiers & key.MOD_SHIFT:
                    path = join(self.save_path, self.save_name) if self.save_path and self.save_name else None
                else:
                    path = join(self.load_path, self.load_name) if self.load_path and self.load_name else None
                path = normalize(path) if path else None
                if not path:
                    self.log(f"Error: No file {which} yet")
                elif modifiers & key.MOD_ACCEL:  # Reload save data (with history)
                    data = self.save_data if modifiers & key.MOD_SHIFT else self.load_data
                    if data is not None:
                        state = '' if isfile(path) else '(deleted) '
                        self.log(f"Info: Reloading last {which} state in {state}\"{path}\"")
                        if self.load_board(data, with_history=True):
                            self.sync(post=True)
                elif isfile(path):  # Reload save file (with history)
                    self.log(f"Info: Reloading last {which} file")
                    if self.load(path, True):
                        if not self.save_imported:
                            self.reset_custom_data(True)
                            self.reset_board()
                            self.log_special_modes()
                else:
                    self.log(f"Error: Last {which} file not found at \"{path}\"")
            elif modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:  # Flip board
                self.flip_board()
                self.log("Info: Board flipped", False)
            elif not modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Fast-forward
                self.auto_moves = False
                if self.future_move_history:
                    self.log("Info: Fast-forwarding", False)
                while self.future_move_history:
                    self.redo_last_move()
                self.auto_moves = True
            elif modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Fast-forward, but slowly. (Reload history)
                self.log("Info: Reloading history", False)
                self.log("Info: Starting new game", bool(self.hide_pieces))
                if not self.reload_history():
                    self.log("Error: Failed to reload history")
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
        if symbol == key.J:  # Alternate piece sprites (J was chosen due to closeness with other "hiding" hotkeys)
            old_alternate_pieces, old_alternate_swap = self.alternate_pieces, self.alternate_swap
            if modifiers & key.MOD_ALT:  # Alternate piece sprites for moving player (non-moving if Shift)
                self.alternate_swap = not self.alternate_pieces > 0 or not self.alternate_swap
                new_side = self.turn_side.opponent() if modifiers & key.MOD_SHIFT else self.turn_side
                self.alternate_pieces = new_side.value
            else:
                self.alternate_swap = False
                if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Default (promotion/drop UI only)
                    self.alternate_pieces = 0
                elif modifiers & key.MOD_ACCEL:  # Show
                    self.alternate_pieces = -1
                elif modifiers & key.MOD_SHIFT:  # Hide
                    self.alternate_pieces = -2
            if old_alternate_pieces != self.alternate_pieces or old_alternate_swap != self.alternate_swap:
                if self.alternate_pieces == -2:
                    self.log("Info: Alternate piece sprites hidden")
                elif self.alternate_pieces == -1:
                    self.log("Info: Alternate piece sprites shown")
                elif self.alternate_pieces > 0:
                    if self.alternate_swap:
                        player = f"{'' if self.turn_side == Side(self.alternate_pieces) else 'non-'}moving player"
                        self.log(f"Info: Alternate piece sprites shown for {player}")
                    else:
                        self.log(f"Info: Alternate piece sprites shown for {Side(self.alternate_pieces)}")
                else:
                    self.log("Info: Alternate piece sprites shown in promotion")
                self.update_pieces()
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
            if modifiers & key.MOD_ALT and not modifiers & key.MOD_SHIFT:  # Move type markers
                self.move_type_markers = not self.move_type_markers
                self.log(f"Info: Using {'typed' if self.move_type_markers else 'regular'} move markers", False)
            elif modifiers & key.MOD_ALT:  # Theoretical move markers
                self.theoretical_move_markers = not self.theoretical_move_markers
                if self.theoretical_move_markers:
                    self.log(f"Info: Theoretical move markers enabled", False)
                else:
                    self.log(f"Info: Theoretical move markers disabled", False)
                self.load_moves(False)
            elif modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Default (legal for moving player only)
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
        if symbol == key.I:  # Info
            if modifiers & key.MOD_ALT:  # In-between labels
                self.extra_labels = not self.extra_labels
                self.log(f"Info: In-between labels {'enabled' if self.extra_labels else 'disabled'}", False)
                self.update_labels()
            elif modifiers & key.MOD_SHIFT:  # Info
                self.show_history = not self.show_history
                self.log(f"Info: Intermediate moves {'shown' if self.show_history else 'hidden'}", False)
                self.show_moves()
            elif modifiers & key.MOD_ACCEL:  # Info
                self.log_info()
        if symbol == key.L:
            if modifiers & key.MOD_ALT:  # Load save data
                if self.fullscreen:
                    self.to_windowed()
                self.deactivate()
                self.draw(0)
                self.log(f"Info: Selecting a file to {'reload' if modifiers & key.MOD_SHIFT else 'load from'}", False)
                if not self.load_name and self.save_name:
                    load_path = load_menu(self.save_path, self.save_name)
                else:
                    load_path = load_menu(self.load_path, self.load_name or None)
                if load_path:
                    if self.load(load_path, with_history=bool(modifiers & key.MOD_SHIFT)):
                        if not self.save_imported:
                            self.reset_custom_data(True)
                            self.reset_board()
                            self.log_special_modes()
                else:
                    self.log("Info: Loading cancelled", False)
                self.activate()
            else:  # Log
                if modifiers & key.MOD_ACCEL:  # Save log
                    self.save_log()
                if modifiers & key.MOD_SHIFT:  # Save verbose log
                    self.save_verbose_log()
        if symbol == key.D:  # Debug
            if modifiers & key.MOD_ACCEL:  # Save debug log
                self.save_debug_log()
            if modifiers & key.MOD_SHIFT:  # Print debug log
                self.print_debug_log()
            if modifiers & key.MOD_ALT:  # Save debug listings
                self.save_debug_data()
        if symbol == key.V:
            if modifiers & key.MOD_ALT and not modifiers & key.MOD_SHIFT:  # Toggle verbose console output
                self.verbose = not self.verbose
                self.log(f"Info: Verbose logging {'enabled' if self.verbose else 'disabled'}", False)
            elif modifiers & key.MOD_ALT:  # Toggle console output
                self.verbose = False if self.verbose is None else None
                self.log(f"Info: Logging {'enabled' if self.verbose is not None else 'disabled'}", False)
        if symbol == key.SLASH:  # (?) Random
            if self.edit_mode:
                return
            moves = self.unique_moves()[self.turn_side]
            if modifiers & key.MOD_SHIFT:  # Random piece
                self.deselect_piece()
                self.update_drops(False)
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

    def load(self, path: str | None, with_history: bool = False) -> bool:
        if not path:
            return False
        path = normalize(path)
        update_mode = abs(self.board_config['update_mode'])
        should_update = bool(update_mode)
        if should_update:
            update_mode -= 1
        load_attempted = False
        # noinspection PyBroadException
        try:
            if not isfile(path):
                return False
            if (limit := self.board_config['size_limit']) and (save_size := getsize(path)) > limit:
                units = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
                parts = [save_size, limit]
                i = 0
                while parts[1] >= 1024:
                    parts = [x / 1024 for x in parts]
                    i += 1
                ratio = '/'.join(f"{x:.{max(0, 3 - len(str(int(x))))}f}" for x in parts)
                self.log(f"Error: File \"{path}\" is too large to load ({ratio} {units[i]})")
                return False
            self.log(f"Info: Loading from \"{path}\"")
            with open(path, mode='r', encoding='utf-8') as file:
                save_data = file.read()
            load_attempted = True
            if self.load_board(save_data, with_history=update_mode & 1 if should_update else with_history):
                self.sync(post=True)
                self.load_path, self.load_name = split(path)
                if should_update:
                    self.save(path)
        except Exception:
            self.log(f"Error: Failed to load data from \"{path}\"")
            print_exc()
        return load_attempted

    def save(self, path: str | None, auto: bool = False) -> None:
        if not path:
            return
        path = normalize(path)
        data = self.dump_board(trim=self.board_config[f"trim_{'auto' * auto}save"])
        if auto and data == self.auto_data:
            return
        makedirs(dirname(path), exist_ok=True)
        with open(path, mode='w', encoding='utf-8') as file:
            file.write(data)
        if auto:
            self.auto_data = data
            self.auto_path, self.auto_name = split(path)
            self.log(f"Info: Auto-saved to \"{path}\"", False)
        else:
            self.save_data = data
            self.save_path, self.save_name = split(path)
            self.log(f"Info: Saved to \"{path}\"", False)

    def quick_save(self) -> None:
        self.save(get_file_path('save', 'json', self.board_config['save_path']))

    def auto_save(self) -> None:
        self.save(get_file_path('auto', 'json', self.board_config['autosave_path']), auto=True)

    def sync(self, get: bool = False, post: bool = False) -> bool | None:
        if not self.board_config['sync_data']:
            return None
        url = f"http://{self.board_config['sync_host']}:{self.board_config['sync_port']}/"
        finished = False
        offline = False
        value = None
        if get and not finished:
            self.update_caption(string="Getting data...", force=True)
            try:
                r = request('get', url, json={
                    'time': self.sync_timestamp.isoformat() if self.sync_timestamp else None,
                })
                if r.status_code == 200:
                    data = r.json()
                    if data.get('data') is not None:
                        save_data = self.dump_board(data=data['data'], trim=sync_trim_fields)
                        was_active = self.is_active
                        if was_active:
                            self.deactivate()
                        if self.load_board(save_data):
                            self.log(f"Info: Game data loaded from {url}")
                            value = True
                        else:
                            self.log(f"Error: Failed to load game data from {url}")
                            value = False
                        if was_active:
                            self.activate()
                        finished = True
                    if data.get('time') is not None:
                        self.sync_timestamp = datetime.fromisoformat(data['time']).astimezone(UTC)
                else:
                    error_message = ''
                    try:
                        data = r.json()
                        if data.get('error'):
                            error_message = f": {data['error']}"
                    except JsonDecodeError:
                        pass
                    self.log(f"Error: Failed to get game data from {url} (status code {r.status_code}){error_message}")
                    finished = True
                    offline = True
            except RequestException as e:
                self.log(f"Error: Failed to get game data from {url} ({e})")
                finished = True
                offline = True
        if post and not finished:
            self.sync_timestamp = datetime.now().astimezone(UTC)
            self.update_caption(string="Sending data...", force=True)
            try:
                r = request('post', url, json={
                    'data': self.dump_board(string=False),
                    'time': self.sync_timestamp.isoformat() if self.sync_timestamp else None,
                })
                if r.status_code == 200:
                    data = r.json()
                    if data.get('saved'):
                        self.log(f"Info: Game data sent to {url}", False)
                    else:
                        self.log(f"Info: Game data needs update from {url}", False)
                        value = self.sync(get=True)
                else:
                    error_message = ''
                    try:
                        data = r.json()
                        if data.get('error'):
                            error_message = f": {data['error']}"
                    except JsonDecodeError:
                        pass
                    self.log(f"Error: Failed to send game data to {url} (status code {r.status_code}){error_message}")
                    offline = True
            except RequestException as e:
                self.log(f"Error: Failed to send game data to {url} ({e})")
                offline = True
        if offline:
            self.board_config['sync_data'] = False
            self.log("Info: Online mode disabled")
        self.update_caption()
        return value


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
        timestamp = ''
        if self.board_config['timestamp'] is not False:
            timestamp = f"[{datetime.now().strftime(self.board_config['timestamp_format'])}] "
        timestamp_string = f"{timestamp}{string}"
        log_string = timestamp_string if self.board_config['timestamp'] is True else string
        verbose_string = timestamp_string if self.board_config['timestamp'] is not False else string
        self.verbose_data.append(verbose_string)
        if important:
            self.log_data.append(log_string)
        if self.verbose is None:
            return
        if self.verbose:
            print(verbose_string)
        elif important:
            print(log_string)

    def log_info(self, info: list[str | None] | None = None):
        if not self.board_config['log_info']:
            return
        if info is None:
            info = self.save_info
        for line in info:
            self.log(line, False, prefix='Note')

    def log_armies(self):
        if self.custom_variant or self.custom_layout:
            self.log(f"Game: {self.custom_variant or 'Custom'}")
            return
        if self.piece_set_ids[Side.WHITE] == self.piece_set_ids[Side.BLACK] == 0:
            self.variant = 'Chess'
        else:
            self.variant = f"{self.piece_set_names[Side.WHITE]} vs. {self.piece_set_names[Side.BLACK]}"
        self.log(f"Game: {'???' if self.hide_pieces else self.variant}")

    def log_special_modes(self):
        if self.alternate_pieces == -2:
            self.log("Info: Alternate piece sprites hidden")
        elif self.alternate_pieces == -1:
            self.log("Info: Alternate piece sprites shown")
        elif self.alternate_pieces > 0:
            if self.alternate_swap:
                player = f"{'' if self.turn_side == Side(self.alternate_pieces) else 'non-'}moving player"
                self.log(f"Info: Alternate piece sprites shown for {player}")
            else:
                self.log(f"Info: Alternate piece sprites shown for {Side(self.alternate_pieces)}")
        if self.hide_pieces == 1:
            self.log("Info: Pieces hidden")
        if self.hide_pieces == 2:
            self.log("Info: Penultima mode active")
        if self.use_drops:
            self.log("Info: Drops enabled")

    def save_log_data(self, log_data: list[str] | None = None, log_name: str = 'log') -> str | None:
        if not log_data:
            log_data = self.log_data
        if log_data:
            save_path = get_file_path(log_name, 'txt', self.board_config['log_path'])
            with open(save_path, mode='w', encoding='utf-8') as log_file:
                log_file.write('\n'.join(log_data))
            return str(save_path)
        return None

    def save_debug_data(self) -> None:
        self.log("Info: Saving debug listings", False)
        data_path = save_piece_data(self)
        self.log(f"Info: Piece data listings saved to \"{data_path}\"", False)
        sets_path = save_piece_sets()
        self.log(f"Info: Piece set listings saved to \"{sets_path}\"", False)
        type_path = save_piece_types()
        self.log(f"Info: Piece type listings saved to \"{type_path}\"", False)

    def print_debug_log(self) -> None:
        self.log("Info: Printing debug information", False)
        debug_log_data = debug_info(self)
        for string in debug_log_data:
            print(f"[Debug] {string}")
        self.log("Info: Debug information printed", False)

    def save_debug_log(self) -> None:
        self.log("Info: Saving debug information", False)
        debug_log_data = debug_info(self)
        debug_log_path = normalize(self.save_log_data(debug_log_data, 'debug'))
        self.log(f"Info: Debug information saved to \"{debug_log_path}\"", False)

    def save_verbose_log(self) -> None:
        log_path = normalize(self.save_log_data(self.verbose_data, 'verbose'))
        self.log(f"Info: Verbose log file saved to \"{log_path}\"", False)

    def save_log(self) -> None:
        log_path = normalize(self.save_log_data())
        self.log(f"Info: Log file saved to \"{log_path}\"", False)

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
        config['edit_mode'] = self.edit_mode
        config['flip_board'] = self.flip_mode
        config['alter_pieces'] = self.alternate_pieces
        config['alter_swap'] = self.alternate_swap
        config['hide_pieces'] = self.hide_pieces
        config['hide_moves'] = self.hide_move_markers
        config['use_drops'] = self.use_drops
        config['chaos_mode'] = self.chaos_mode
        config['chaos_seed'] = self.chaos_seed
        config['set_seed'] = self.set_seed
        config['roll_seed'] = self.roll_seed
        config['verbose'] = self.verbose
        for name, path in (('load_path', self.load_path), ('save_path', self.save_path)):
            try:
                path = relpath(path, base_dir)
            except ValueError:
                pass
            config[name] = normalize(path, '/')
        save_path = get_file_path('config', 'ini')
        config.save(save_path)
        self.log(f"Info: Configuration saved to \"{save_path}\"", False)

    def run(self, view: View | None = None) -> None:
        if self.board_config['update_mode'] < 0 and self.save_loaded:
            self.close()
        else:
            self.set_visible()
            super().run()
