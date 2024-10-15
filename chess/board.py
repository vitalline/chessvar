from __future__ import annotations

from copy import copy, deepcopy
from datetime import datetime
from itertools import product, zip_longest
from json import dumps, loads, JSONDecodeError
from math import ceil, sqrt
from os import makedirs, name as os_name, system
from os.path import dirname, isfile, join
from random import Random
from sys import argv, stdout
from tkinter import filedialog
from traceback import print_exc
from typing import Any, Type, TextIO

from PIL.ImageColor import getrgb
from arcade import key, MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT, Text
from arcade import Sprite, SpriteList, Window
from arcade import get_screens, start_render

from chess.color import colors, default_colors, trickster_colors
from chess.color import average, darken, desaturate, lighten, saturate
from chess.config import Config
from chess.movement import movement
from chess.movement.move import Move
from chess.movement.util import Position, add, to_alpha as b26
from chess.movement.util import to_algebraic as toa, from_algebraic as fra
from chess.movement.util import from_algebraic_map as frm
from chess.pieces.groups import classic as fide
from chess.pieces.groups import amazon as am, amontillado as ao, asymmetry as ay, avian as av
from chess.pieces.groups import backward as bw, beast as bs, breakfast as bk, burn as br, buzz as bz
from chess.pieces.groups import camel as ca, cannon as cn, color as co, colorbound as cb
from chess.pieces.groups import crash as cs, crook as cr, cylindrical as cy
from chess.pieces.groups import demirifle as de, drip as dr
from chess.pieces.groups import fairy as fa, fizz as fi, fly as fl, forward as fw
from chess.pieces.groups import hobbit as hb, horse as hs
from chess.pieces.groups import inadjacent as ia, iron as ir
from chess.pieces.groups import knight as kn
from chess.pieces.groups import martian as mr, mash as ms, multimove as mu
from chess.pieces.groups import narrow as na, nocturnal as no
from chess.pieces.groups import pawn as pa, perimeter as pe, pizza as pz, probable as pr
from chess.pieces.groups import rookie as rk
from chess.pieces.groups import splash as sp, starbound as st, stone as so, switch as sw
from chess.pieces.groups import thrash as th
from chess.pieces.groups import wide as wd
from chess.pieces.groups import zebra as zb
from chess.pieces.groups.util import NoPiece, Obstacle, Block, Wall
from chess.pieces.piece import Piece
from chess.pieces.side import Side
from chess.pieces.util import QuasiRoyal, Royal, Slow
from chess.save import condense, expand
from chess.save import condense_algebraic as cnd_alg, expand_algebraic as exp_alg
from chess.save import load_move, load_piece, load_rng, load_piece_type, load_custom_type
from chess.save import save_move, save_piece, save_rng, save_piece_type, save_custom_type
from chess.util import Default, Unset, base_dir

piece_groups: list[dict[str, str | list[Type[Piece]]]] = [
    {
        'name': "Fabulous FIDEs",
        'set': [fide.Rook, fide.Knight, fide.Bishop, fide.Queen, fide.King, fide.Bishop, fide.Knight, fide.Rook],
    },
    {
        'name': "Colorbound Clobberers",
        'set': [cb.Bede, cb.Waffle, cb.Fad, cb.Archbishop, cb.King, cb.Fad, cb.Waffle, cb.Bede],
    },
    {
        'name': "Remarkable Rookies",
        'set': [rk.Fork, rk.Woodrook, rk.Dove, rk.Chancellor, fide.King, rk.Dove, rk.Woodrook, rk.Fork],
    },
    {
        'name': "Nutty Knights",
        'set': [kn.Forerook, kn.Fibnif, kn.Foreknight, kn.Colonel, fide.King, kn.Foreknight, kn.Fibnif, kn.Forerook],
    },
    {
        'name': "Amazonian Armada",
        'set': [am.Cannon, am.Camel, am.NightRdr, am.Amazon, fide.King, am.NightRdr, am.Camel, am.Cannon],
    },
    {
        'name': "Amontillado Arbiters",
        'set': [ao.Hasdrubal, ao.Barcfil, ao.Bed, ao.Hamilcar, fide.King, ao.Bed, ao.Barcfil, ao.Hasdrubal],
    },
    {
        'name': "Asymmetrical Assaulters",
        'set': [ay.RQue, ay.Knish, ay.Blizzard, ay.Chanqueen, fide.King, ay.Blizzard, ay.Knish, ay.LQue],
    },
    {
        'name': "Avian Airforce",
        'set': [av.Wader, av.Darter, av.Falcon, av.Kingfisher, fide.King, av.Falcon, av.Darter, av.Wader],
    },
    {
        'name': "Backward Barnacles",
        'set': [bw.Whelk, bw.Walrus, bw.Seagull, bw.Shark, fide.King, bw.Seagull, bw.Walrus, bw.Whelk],
    },
    {
        'name': "Beautiful Beasts",
        'set': [bs.Ouroboros, bs.Quagga, bs.Roc, bs.Buffalo, fide.King, bs.Roc, bs.Quagga, bs.Ouroboros],
    },
    {
        'name': "Breakfast Blasters",
        'set': [bk.Belwaffle, bk.Pancake, bk.Bacon, bk.Omelet, fide.King, bk.Bacon, bk.Pancake, bk.Belwaffle],
    },
    {
        'name': "Burning Barbarians",
        'set': [br.Champion, br.DraHorse, br.Wizard, br.DraKing, fide.King, br.Wizard, br.DraHorse, br.Champion],
    },
    {
        'name': "Buzzing Busters",
        'set': [bz.Mosquito, bz.Dragonfly, bz.Locust, bz.Mantis, fide.King, bz.Locust, bz.Dragonfly, bz.Mosquito],
    },
    {
        'name': "Cartankerous Camelids",
        'set': [ca.Llama, ca.Cashier, ca.Cabbage, ca.Warlock, fide.King, ca.Cabbage, ca.Cashier, ca.Llama],
    },
    {
        'name': "Claustrophobic Cannoneers",
        'set_w': [cn.Mortar, cn.Napoleon, cn.Carronade, cn.Bertha, fide.King, cn.Carronade, cn.Napoleon, cn.Howitzer],
        'set_b': [cn.Howitzer, cn.Napoleon, cn.Carronade, cn.Bertha, fide.King, cn.Carronade, cn.Napoleon, cn.Mortar],
    },
    {
        'name': "Colorful Characters",
        'set_w': [co.ElkRdr, co.DCannon, co.Nightlight, co.Nanqueen, fide.King, co.Nightlight, co.DCannon, co.CaribRdr],
        'set_b': [co.CaribRdr, co.DCannon, co.Nightlight, co.Nanqueen, fide.King, co.Nightlight, co.DCannon, co.ElkRdr],
    },
    {
        'name': "Contrarian Crashers",
        'set': [cs.Merlion, cs.Biskni, cs.IStewardess, cs.IPaladess, fide.King, cs.IStewardess, cs.Biskni, cs.Merlion],
    },
    {
        'name': "Cruel Crooks",
        'set': [cr.LionCub, cr.Rhino, cr.Boyscout, cr.Griffon, fide.King, cr.Boyscout, cr.Rhino, cr.LionCub],
    },
    {
        'name': "Cylindrical Cinders",
        'set': [cy.Waffle, cy.Knight, cy.Bishop, cy.Chancellor, fide.King, cy.Bishop, cy.Knight, cy.Waffle],
    },
    {
        'name': "Demirifle Destroyers",
        'set': [de.Snail, de.Crab, de.Lobster, de.Crabsnail, fide.King, de.Lobster, de.Crab, de.Snail],
    },
    {
        'name': "Dripping Droogs",
        'set': [dr.Lobefin, dr.CrabRdr, dr.Sandbar, dr.Oyster, cb.King, dr.Sandbar, dr.CrabRdr, dr.Lobefin],
    },
    {
        'name': "Fearful Fairies",
        'set': [fa.Frog, fa.Dullahan, fa.Elephant, fa.Unicorn, fide.King, fa.Elephant, fa.Dullahan, fa.Frog],
    },
    {
        'name': "Fighting Fizzies",
        'set': [fi.LRhino, fi.Wyvern, fi.Crabinal, fi.EagleScout, fide.King, fi.Crabinal, fi.Wyvern, fi.RRhino],
    },
    {
        'name': "Flying Flagellants",
        'set': [fl.Quetzal, fl.Owl, fl.Hoatzin, fl.Eagle, fide.King, fl.Hoatzin, fl.Owl, fl.Quetzal],
    },
    {
        'name': "Forward Forgers",
        'set': [fw.IvoryRook, fw.Knishop, fw.Bishight, fw.Forequeen, fide.King, fw.Bishight, fw.Knishop, fw.IvoryRook],
    },
    {
        'name': "Horseback Harassers",
        'set': [hs.Naysayer, hs.HorseRdr, hs.Tapir, hs.Marauder, fide.King, hs.Tapir, hs.HorseRdr, hs.Naysayer],
    },
    {
        'name': "Hopping Hobbitses",
        'set': [hb.Heart, hb.Drake, hb.Barcinal, hb.Hannibal, fide.King, hb.Barcinal, hb.Drake, hb.Heart],
    },
    {
        'name': "Inadjacent Intimidators",
        'set': [ia.Bireme, ia.Tigon, ia.Bicycle, ia.Biplane, fide.King, ia.Bicycle, ia.Tigon, ia.Bireme],
    },
    {
        'name': "Irritant Irons",
        'set': [ir.Musth, ir.Officer, ir.SilverRdr, ir.GoldRdr, fide.King, ir.SilverRdr, ir.Officer, ir.Musth],
    },
    {
        'name': "Magnificent Multimovers",
        'set': [mu.MachineRdr, mu.Allnight, mu.Tusker, mu.Hierophant, fide.King, mu.Tusker, mu.Allnight, mu.MachineRdr],
    },
    {
        'name': "Martian Manglers",
        'set': [mr.Padwar, mr.Marker, mr.Walker, mr.Chief, fide.King, mr.Walker, mr.Marker, mr.Padwar],
    },
    {
        'name': "Meticulous Mashers",
        'set': [ms.Forfer, ms.Scout, ms.Bandit, ms.Rancher, fide.King, ms.Bandit, ms.Scout, ms.Forfer],
    },
    {
        'name': "Narrow Nightmares",
        'set': [na.Deerfly, na.Ship, na.Filescout, na.Horsefly, fide.King, na.Filescout, na.Ship, na.Deerfly],
    },
    {
        'name': "Nocturnal Naysayers",
        'set': [no.Bard, no.Nightsling, no.MoaRdr, no.Nanking, fide.King, no.MoaRdr, no.Nightsling, no.Bard],
    },
    {
        'name': "Pawnshop Praetorians",
        'set': [pa.Paladin, pa.Guarddog, pa.Stewardess, pa.Dowager, fide.King, pa.Stewardess, pa.Guarddog, pa.Paladin],
    },
    {
        'name': "Perimeter Prancers",
        'set': [pe.Fencer, pe.Castle, pe.Kirin, pe.Fort, fide.King, pe.Kirin, pe.Castle, pe.Fencer],
    },
    {
        'name': "Pizza Pounders",
        'set': [pz.Pepperoni, pz.Mushroom, pz.Sausage, pz.Meatball, fide.King, pz.Sausage, pz.Mushroom, pz.Pepperoni],
    },
    {
        'name': "Probable Prowlers",
        'set': [pr.Veteran, pr.RedPanda, pr.Tempofad, pr.WaterBuffalo, fide.King, pr.Tempofad, pr.RedPanda, pr.Veteran],
    },
    {
        'name': "Seeping Switchers",
        'set': [sw.Panda, sw.Marquis, sw.Bear, sw.Earl, fide.King, sw.Bear, sw.Marquis, sw.Panda],
    },
    {
        'name': "Starbound Sliders",
        'set': [st.Star, st.Lancer, st.SineRdr, st.Turneagle, fide.King, st.SineRdr, st.Lancer, st.Star],
    },
    {
        'name': "Stoic Stones",
        'set': [so.Caecilian, so.Brick, so.Stele, so.Caryatid, fide.King, so.Stele, so.Brick, so.Caecilian],
    },
    {
        'name': "Superior Splashers",
        'set': [sp.Mammoth, sp.Gecko, sp.Deacon, sp.Brigadier, fide.King, sp.Deacon, sp.Gecko, sp.Mammoth],
    },
    {
        'name': "Threeleaping Thrashers",
        'set': [th.Trident, th.Nipper, th.Bullfrog, th.Duchess, fide.King, th.Bullfrog, th.Nipper, th.Trident],
    },
    {
        'name': "Wide Wildmen",
        'set': [wd.Ogre, wd.Sidesail, wd.Sidewinder, wd.Ogress, fide.King, wd.Sidewinder, wd.Sidesail, wd.Ogre],
    },
    {
        'name': "Zany Zebroids",
        'set': [zb.Eliphas, zb.Sorcerer, zb.Adze, zb.IMarauder, fide.King, zb.Adze, zb.Sorcerer, zb.Eliphas],
    }
]

penultima_textures = [f'ghost{s}' if s else None for s in ('R', 'N', 'B', 'Q', None, 'B', 'N', 'R')]

board_width = 8
board_height = 8

pawn_row: list[Type[Piece]] = [fide.Pawn] * board_width
empty_row: list[Type[Piece]] = [NoPiece] * board_width

white_row = [Side.WHITE] * board_width
black_row = [Side.BLACK] * board_width
neutral_row = [Side.NONE] * board_width

types = [white_row, pawn_row] + [empty_row] * (board_height - 4) + [pawn_row, black_row]
sides = [white_row, white_row] + [neutral_row] * (board_height - 4) + [black_row, black_row]

default_size = 50.0
min_size = 25.0
max_size = 100.0
size_step = 5.0

base_rng = Random()
max_seed = 2 ** 32 - 1

config_path = join(base_dir, 'config.ini')

invalid_chars = ':<>|"?*'
invalid_chars_trans_table = str.maketrans(invalid_chars, '_' * len(invalid_chars))


def get_filename(
    name: str, ext: str, in_dir: str = base_dir, ts: datetime | None = None, ts_format: str = "%Y-%m-%d_%H-%M-%S"
) -> str:
    name_args = [name, (ts or datetime.now()).strftime(ts_format)]
    full_name = '_'.join(s for s in name_args if s).translate(invalid_chars_trans_table)
    return join(in_dir, f"{full_name}.{ext}")


def get_piece_types(side: Side = Side.WHITE) -> dict[Type[Piece], str]:
    piece_types = {
        get_set(side, i)[j]
        for i in range(len(piece_groups)) for j in [i for i in range(4)] + [7]
        if j < 4 or get_set(side, i)[j] != get_set(side, i)[7 - j]
    } | {fide.Pawn, fide.King, cb.King}
    return {t: t.name + (' (CB)' if t.is_colorbound() or t == cb.King else '') for t in piece_types}


def get_set(side: Side, set_id: int) -> list[Type[Piece]]:
    piece_group = piece_groups[set_id]
    return piece_group.get(f"set_{side.key()[0]}", piece_group.get('set', empty_row))


def get_set_name(piece_set: list[Type[Piece]]) -> str:
    piece_name_order = [[0, 7], [1, 6], [2, 5], [3]]
    piece_names = []
    for group in piece_name_order:
        name_order = []
        used_names = set()
        for pos in group:
            name = piece_set[pos].name
            if name not in used_names:
                name_order.append(name)
                used_names.add(name)
        piece_names.append('/'.join(name_order))
    piece_set_name = ', '.join(piece_names)
    return f"({piece_set_name})"


def is_prefix_of(string: Any, prefix: Any) -> bool:
    return isinstance(string, str) and isinstance(prefix, str) and string.lower().startswith(prefix.lower())


def is_prefix_in(strings: list[Any], prefix: Any) -> bool:
    return any(is_prefix_of(string, prefix) for string in strings)


def print_piece_data(board: Board, fp: TextIO = stdout, side: Side = Side.WHITE) -> None:
    fp.write('{\n')
    for i, t in enumerate(sorted(get_piece_types(side), key=lambda x: save_piece_type(x))):
        if i:
            fp.write(',\n')
        fp.write(f'  "{save_piece_type(t)}":')
        p = t(board=board, side=side)  # type: ignore
        fp.write(dumps(save_custom_type(p), separators=(',', ':'), ensure_ascii=False))
    fp.write('\n}')


def print_piece_sets(fp: TextIO = stdout) -> None:
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


def print_piece_types(fp: TextIO = stdout, side: Side = Side.WHITE) -> None:
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


def select_save_data() -> str:
    return filedialog.askopenfilename(
        initialdir=base_dir,
        filetypes=[("JSON save file", "*.json")],
    )


def select_save_name() -> str:
    return filedialog.asksaveasfilename(
        initialdir=base_dir,
        initialfile=get_filename('save', 'json', in_dir=''),
        filetypes=[("JSON save file", "*.json")],
        defaultextension='.json',
    )


class Board(Window):

    def __init__(self):
        # super boring initialization stuff (bluh bluh)
        self.board_config = Config(config_path)
        if not isfile(config_path):
            self.board_config.save(config_path)

        self.board_width, self.board_height = board_width, board_height
        self.square_size = default_size

        super().__init__(
            width=round((self.board_width + 2) * self.square_size),
            height=round((self.board_height + 2) * self.square_size),
            title='Chess',
            resizable=True,
            vsync=True,
            center_window=True,
            visible=False,
        )

        self.origin = self.width / 2, self.height / 2
        self.set_minimum_size(round((self.board_width + 2) * min_size), round((self.board_height + 2) * min_size))

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
        self.load_data = None  # last loaded data
        self.load_dict = None  # last loaded data, parsed from JSON
        self.load_path = None  # path to the last loaded data file
        self.save_data = None  # last saved data
        self.save_path = None  # path to the last saved data file
        self.save_loaded = False  # whether a save was successfully loaded
        self.game_loaded = False  # whether the game had successfully loaded
        self.skip_mouse_move = 0  # setting this to >=1 skips mouse movement events
        self.highlight_square = None  # square that is being highlighted with the keyboard
        self.hovered_square = None  # square we are currently hovering over
        self.clicked_square = None  # square we clicked on
        self.selected_square = None  # square selected for moving
        self.square_was_clicked = False  # used to discern two-click moving from dragging
        self.piece_was_selected = False  # used to discern between selecting a piece and moving it
        self.held_buttons = 0  # mouse button that was pressed
        self.en_passant_target = None  # piece that can be captured en passant
        self.en_passant_markers = set()  # squares where it can be captured
        self.castling_ep_target = None  # piece that can be captured en passant after castling
        self.castling_ep_markers = set()  # squares where it can be captured that way
        self.promotion_piece = None  # piece that is currently being promoted
        self.promotion_area = {}  # squares to draw possible promotions on
        self.promotion_area_drops = {}  # dropped pieces matching the squares above
        self.action_count = 0  # current number of actions taken
        self.ply_count = 0  # current half-move number
        self.ply_simulation = 0  # current number of look-ahead half-moves
        self.move_history = []  # list of moves made so far
        self.future_move_history = []  # list of moves that were undone, in reverse order
        self.roll_history = []  # list of rolls made so far (used for ProbabilisticMovement)
        self.move_seed = None  # seed for move selection
        self.move_rng = None  # random number generator for move selection
        self.roll_seed = None  # seed for probabilistic movement
        self.roll_rng = None  # random number generator for probabilistic movement
        self.set_seed = None  # seed for piece set selection
        self.set_rng = None  # random number generator for piece set selection
        self.turn_order = [Side.WHITE, Side.BLACK]  # order of turns
        self.turn_side = self.turn_order[0]  # side whose turn it is
        self.turn_pieces = None  # pieces that can be moved this turn
        self.check_side = Side.NONE  # side that is currently in check
        self.use_drops = self.board_config['use_drops']  # whether pieces can be dropped
        self.use_check = self.board_config['use_check']  # whether to check for check after each move
        self.stalemate_rule = 0  # 0: draw, 1: win for moving, -1: win for stalemated. can be {side: side is stalemated}
        self.royal_piece_mode = self.board_config['royal_mode'] % 3  # 0: normal, 1: force royal, 2: force quasi-royal
        self.should_hide_pieces = self.board_config['hide_pieces'] % 3  # 0: don't hide, 1: hide all, 2: penultima mode
        self.should_hide_moves = self.board_config['hide_moves']  # whether to hide the move markers; None uses above
        self.flip_mode = False  # whether the board is flipped
        self.edit_mode = False  # allows to edit the board position if set to True
        self.game_over = False  # act 6 act 6 intermission 3 (game over)
        self.trickster_color_index = 0  # hey wouldn't it be funny if there was an easter egg here
        self.trickster_color_delta = 0  # but it's not like that's ever going to happen right
        self.trickster_angle_delta = 0  # this is just a normal chess game after all
        self.pieces = []  # list of pieces on the board
        self.piece_set_ids = {Side.WHITE: 0, Side.BLACK: 0}  # ids of piece sets to use for each side
        self.piece_set_names = {Side.WHITE: '', Side.BLACK: ''}  # names of piece sets to use for each side
        self.edit_piece_set_id = None  # id of piece set used when placing pieces in edit mode, None uses current sets
        self.chaos_mode = self.board_config['chaos_mode']  # 0: no, 1: match pos, 2: match pos asym, 3: any, 4: any asym
        self.chaos_sets = {}  # piece sets generated in chaos mode
        self.piece_sets = {Side.WHITE: [], Side.BLACK: []}  # types of pieces each side starts with
        self.drops = {Side.WHITE: {}, Side.BLACK: {}}  # drop options, as {side: {was: {pos: as}}}
        self.promotions = {Side.WHITE: {}, Side.BLACK: {}}  # promotion options, as {side: {from: {pos: [to]}}}
        self.edit_promotions = {Side.WHITE: [], Side.BLACK: []}  # types of pieces each side can place in edit mode
        self.movable_pieces = {Side.WHITE: [], Side.BLACK: []}  # pieces that can be moved by each side
        self.royal_pieces = {Side.WHITE: [], Side.BLACK: []}  # these have to stay on the board and should be protected
        self.quasi_royal_pieces = {Side.WHITE: [], Side.BLACK: []}  # at least one of these has to stay on the board
        self.auto_ranged_pieces = {Side.WHITE: [], Side.BLACK: []}  # pieces that auto-capture anywhere they can move to
        self.auto_capture_markers = {Side.WHITE: {}, Side.BLACK: {}}  # squares where the side's pieces can auto-capture
        self.probabilistic_pieces = {Side.WHITE: [], Side.BLACK: []}  # pieces that can move probabilistically
        self.probabilistic_piece_history = []  # list of probabilistic piece positions for every ply
        self.obstacles = []  # list of obstacles (neutral pieces that block movement and cannot move)
        self.penultima_pieces = {Side.WHITE: {}, Side.BLACK: {}}  # piece textures that are used for penultima mode
        self.custom_pieces = {}  # custom piece types
        self.custom_layout = {}  # custom starting layout of the board
        self.custom_promotions = {}  # custom promotion options
        self.custom_drops = {}  # custom drop options
        self.custom_extra_drops = {}  # custom extra drops, as {side: [was]}
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
        self.piece_sprite_list = SpriteList()  # sprites for the pieces
        self.promotion_area_sprite_list = SpriteList()  # sprites for the promotion area background tiles
        self.promotion_piece_sprite_list = SpriteList()  # sprites for the possible promotion pieces
        self.save_interval = 0  # time since the last autosave

        # initialize turn order data for the first move
        if isinstance(self.turn_side, list):
            self.turn_side, self.turn_pieces = self.turn_side[0], set(self.turn_side[1])

        # load stalemate rules from the config
        if isinstance(self.board_config['stalemate'], dict):
            self.stalemate_rule = {Side(k + 1): (v + 1) % 3 - 1 for k, v in self.board_config['stalemate'].items()}
        else:
            self.stalemate_rule = self.board_config['stalemate']

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
        self.log(f"[Ply {self.ply_count}] Info: Verbose output: {'ON' if self.verbose else 'OFF'}", False)
        self.log(f"[Ply {self.ply_count}] Info: Roll seed: {self.roll_seed}", False)
        self.log(f"[Ply {self.ply_count}] Info: Piece set seed: {self.set_seed}", False)
        self.log(f"[Ply {self.ply_count}] Info: Chaos set seed: {self.chaos_seed}", False)

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
        size: float = 0,
        origin: tuple[float, float] | None = None,
        flip: bool | None = None
    ) -> Position:
        x, y = pos
        size = size or self.square_size
        origin = origin or self.origin
        flip = flip if flip is not None else self.flip_mode
        if flip:
            col = round((origin[0] - x) / size + (self.board_width - 1) / 2)
            row = round((origin[1] - y) / size + (self.board_height - 1) / 2)
        else:
            col = round((x - origin[0]) / size + (self.board_width - 1) / 2)
            row = round((y - origin[1]) / size + (self.board_height - 1) / 2)
        return row, col

    def get_screen_position(
        self,
        pos: tuple[float, float],
        size: float = 0,
        origin: tuple[float, float] | None = None,
        flip: bool | None = None
    ) -> tuple[float, float]:
        row, col = pos
        size = size or self.square_size
        origin = origin or self.origin
        flip = flip if flip is not None else self.flip_mode
        if flip:
            x = origin[0] - (col - (self.board_width - 1) / 2) * size
            y = origin[1] - (row - (self.board_height - 1) / 2) * size
        else:
            x = (col - (self.board_width - 1) / 2) * size + origin[0]
            y = (row - (self.board_height - 1) / 2) * size + origin[1]
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
        return NoPiece(self, pos=pos) if self.not_on_board(pos) else self.pieces[pos[0]][pos[1]]

    def get_side(self, pos: Position | None) -> Side:
        return self.get_piece(pos).side

    def get_promotion_side(self, piece: Piece):
        return (
            piece.side if piece.side in {Side.WHITE, Side.BLACK} else
            (Side.WHITE if piece.board_pos[0] < self.board_height / 2 else Side.BLACK)
        )

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
        return self.get_piece(pos).is_empty()

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
        self.clear_en_passant()
        self.clear_castling_ep()
        self.clear_auto_capture_markers()
        self.reset_captures()

        self.turn_side = self.turn_order[0]
        if isinstance(self.turn_side, list):
            self.turn_side, self.turn_pieces = self.turn_side[0], set(self.turn_side[1])
        else:
            self.turn_pieces = None

        self.game_over = False
        self.edit_mode = False
        self.chain_start = None
        self.promotion_piece = None
        self.action_count = 0
        self.ply_count = 0

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
        self.ply_count += 1

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
                if isinstance(piece_type, Side):
                    piece_type = self.piece_sets[piece_side][col]
                self.pieces[row].append(
                    piece_type(board=self, pos=(row, col), side=piece_side)
                )
            if not self.pieces[row][col].is_empty() and not isinstance(self.pieces[row][col], Obstacle):
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

        self.update_status()

    def dump_board(self, partial: bool = False) -> str:
        wh = self.board_width, self.board_height
        data = {
            'board_size': [*wh],
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
                side.value: [save_piece_type(t) for t in piece_set] for side, piece_set in self.piece_sets.items()
            },
            'pieces': cnd_alg({
                p.board_pos: save_piece(p.on(None))
                for pieces in [*self.movable_pieces.values(), self.obstacles] for p in pieces
            }, *wh),
            'custom': {k: save_custom_type(v) for k, v in self.custom_pieces.items()},
            'layout': cnd_alg({pos: save_piece(p.on(None)) for pos, p in self.custom_layout.items()}, *wh),
            'promotions': {
                side.value: {
                    save_piece_type(f): cnd_alg({
                        p: [
                            (save_piece if isinstance(t, Piece) else save_piece_type)(t) for t in l
                        ] for p, l in s.items()
                    }, *wh) for f, s in d.items()
                } for side, d in self.custom_promotions.items()
            },
            'drops': {
                side.value: {
                    save_piece_type(f): cnd_alg({
                        p: (save_piece if isinstance(t, Piece) else save_piece_type)(t)
                        for p, t in s.items()
                    }, *wh) for f, s in d.items()
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
            'side': (self.ply_count - 1) % len(self.turn_order) + 1,
            'order': [
                [s[0].value, sorted(save_piece_type(t) for t in s[1])]
                if isinstance(s, list) else s.value
                for s in self.turn_order
            ],
            'edit': self.edit_mode,
            'edit_promotion': self.edit_piece_set_id,
            'hide_pieces': self.should_hide_pieces,
            'hide_moves': self.should_hide_moves,
            'use_drops': self.use_drops,
            'use_check': self.use_check,
            'stalemate': (
                {side.value: rule for side, rule in self.stalemate_rule.items()}
                if isinstance(self.stalemate_rule, dict) else self.stalemate_rule
            ),
            'royal_mode': self.royal_piece_mode,
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

    def load_board(self, dump: str, with_history: bool = False) -> None:
        try:
            data = loads(dump)
        except JSONDecodeError:
            self.log(f"[Ply {self.ply_count}] Error: Malformed save data")
            print_exc()
            return

        if not isinstance(data, dict):
            self.log(f"[Ply {self.ply_count}] Error: Invalid save format (expected dict, but got {type(data)})")
            return

        self.save_interval = 0
        self.save_loaded = False
        success = True

        self.deselect_piece()
        self.clear_en_passant()
        self.clear_castling_ep()
        self.clear_auto_capture_markers()
        self.game_over = False
        self.action_count = 0

        for sprite_list in self.piece_sprite_list, self.promotion_piece_sprite_list, self.promotion_area_sprite_list:
            sprite_list.clear()
            for sprite in sprite_list:
                sprite_list.remove(sprite)

        self.alias_dict = data.get('alias', {})
        if 'alias' in data:
            del data['alias']
        if self.alias_dict:
            data = expand(data, self.alias_dict, self.board_config['recursive_aliases'])

        # might have to add more error checking to saving/loading, even if at the cost of slight redundancy.
        # who knows when someone decides to introduce a breaking change and absolutely destroy all the saves
        board_size = tuple(data.get('board_size', (self.board_width, self.board_height)))
        self.resize_board(*board_size)
        wh = self.board_width, self.board_height

        window_size = data.get('window_size')
        square_size = data.get('square_size')
        if window_size is not None:
            self.resize(*window_size)
        elif square_size is not None:
            self.resize(round((self.board_width + 2) * square_size), round((self.board_height + 2) * square_size))
        self.update_sprites(data.get('flip_mode', self.flip_mode))
        if window_size is not None and square_size is not None and self.square_size != square_size:
            self.log(
                f"[Ply {self.ply_count}] Error: Square size does not match "
                f"(was {square_size}, but is {self.square_size})"
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
                    self.log(f"[Ply {self.ply_count}] Error: Color scheme doesn't match ({k} was {old}, but is {v})")
        for k, old in old_color_scheme.items():
            if k not in self.color_scheme:
                self.color_scheme[k] = old
                if self.color_index is not None:
                    v = 'undefined'
                    self.log(f"[Ply {self.ply_count}] Error: Color scheme doesn't match ({k} was {old}, but is {v})")

        self.board_config['block_ids'] = data.get('set_blocklist', self.board_config['block_ids'])
        self.board_config['block_ids_chaos'] = data.get('chaos_blocklist', self.board_config['block_ids_chaos'])

        stalemate_data = data.get('stalemate')
        if stalemate_data is not None:
            self.stalemate_rule = {
                Side(int(value)): (rule + 1) % 3 - 1 for value, rule in stalemate_data.items()
            } if isinstance(stalemate_data, dict) else stalemate_data

        self.should_hide_pieces = data.get('hide_pieces', self.should_hide_pieces)
        self.should_hide_moves = data.get('hide_moves', self.should_hide_moves)
        self.use_drops = data.get('use_drops', self.use_drops)
        self.use_check = data.get('use_check', self.use_check)
        self.royal_piece_mode = data.get('royal_mode', self.royal_piece_mode)
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

        custom_data = data.get('custom', {})
        self.custom_pieces = {k: load_custom_type(v, k) for k, v in custom_data.items()}
        c = self.custom_pieces
        self.custom_promotions = {
            Side(int(v)): {
                load_piece_type(f, c): {
                    p: [
                        (load_piece_type(t, c) if isinstance(t, str) else load_piece(t, self, c)) for t in l
                    ] for p, l in exp_alg(s, *wh).items()
                } for f, s in d.items()
            } for v, d in data.get('promotions', {}).items()
        }
        self.custom_drops = {
            Side(int(v)): {
                load_piece_type(f, c): {
                    p: (load_piece_type(t, c) if isinstance(t, str) else load_piece(t, self, c))
                    for p, t in exp_alg(s, *wh).items()
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
        }
        update_sets = False
        for side in self.piece_sets:
            if self.piece_set_ids[side] is None:
                self.piece_sets[side] = saved_piece_sets[side]
                self.piece_set_names[side] = get_set_name(self.piece_sets[side])
                continue
            for i, pair in enumerate(zip(saved_piece_sets[side], self.piece_sets[side])):
                if pair[0] != pair[1]:
                    # this can mean a few things, namely the RNG implementation changing or new sets/pieces being added.
                    # either way, we should at least try to load the old pieces defined in the save to recreate the game
                    self.log(
                        f"[Ply {self.ply_count}] Error: Piece set does not match "
                        f"({side}: {toa(((0 if side == Side.WHITE else 7), i))} "
                        f"was {pair[0].name}, but is {pair[1].name})"
                    )
                    update_sets = True
        if update_sets:
            self.piece_sets = {side: saved_piece_sets[side] for side in self.piece_sets}
            self.piece_set_names = {side: get_set_name(self.piece_sets[side]) for side in self.piece_sets}

        self.reset_drops()
        self.reset_promotions()
        self.reset_edit_promotions()
        self.reset_penultima_pieces()

        self.custom_layout = {p: load_piece(v, self, c).on(p) for p, v in exp_alg(data.get('layout', {}), *wh).items()}

        ply_count = data.get('ply', self.ply_count)
        self.turn_order = [
            [Side(int(s[0])), [load_piece_type(t, c) for t in s[1]]]
            if isinstance(s, list) else Side(int(s))
            for s in data.get('order', [])
        ]
        if not self.turn_order:
            self.turn_order = [Side.WHITE, Side.BLACK]
        self.turn_side = self.turn_order[data.get('side', (self.ply_count - 1) % len(self.turn_order) + 1) - 1]
        if isinstance(self.turn_side, list):
            self.turn_side, self.turn_pieces = self.turn_side[0], set(self.turn_side[1])
        else:
            self.turn_pieces = None

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
        } if self.chain_start else {}

        if 'chaos_state' in data:
            self.chaos_rng = load_rng(data['chaos_state'])
        if 'set_state' in data:
            self.set_rng = load_rng(data['set_state'])
        if 'roll_state' in data:
            self.roll_rng = load_rng(data['roll_state'])

        if self.roll_rng is None:
            self.roll_rng = Random(self.roll_seed)

        pieces = exp_alg(data.get('pieces', {}), *wh)
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

        if self.move_history:
            last_move = self.move_history[-1]
            if last_move and last_move.is_edit != 1 and last_move.movement_type != movement.DropMovement:
                last_move.piece.movement.reload(last_move, last_move.piece)

        self.load_pieces()
        self.update_pieces()
        self.update_colors()
        for side in self.auto_ranged_pieces:
            if self.auto_ranged_pieces[side]:
                self.load_auto_capture_markers(side)

        starting = 'Starting new' if with_history else 'Resuming saved'
        if self.custom_layout:
            self.log(f"[Ply {self.ply_count}] Info: {starting} game (with custom starting layout)")
        elif None in self.piece_set_ids.values():
            self.log(f"[Ply {self.ply_count}] Info: {starting} game (with custom piece sets)")
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
            self.log(f"[Ply {self.ply_count}] Info: {starting} game (with {some} piece {sets})")
        self.ply_count = 0 if with_history else ply_count
        self.log_armies()
        self.ply_count = 1 if with_history else ply_count
        self.log_special_modes()
        if with_history:
            success = self.reload_history()
            if not success:
                self.log(f"[Ply {self.ply_count}] Error: Failed to reload history!")
        else:
            if self.turn_pieces is not None:
                turn_pieces = f" ({', '.join(sorted(piece.name for piece in self.turn_pieces))})"
            else:
                turn_pieces = ''
            self.log(f"[Ply {self.ply_count}] Info: {self.turn_side} to move{turn_pieces}", False)
        if self.edit_mode:
            self.log(f"[Ply {self.ply_count}] Mode: EDIT", False)
            self.moves = {side: {} for side in self.moves}
            self.chain_moves = {side: {} for side in self.chain_moves}
            self.theoretical_moves = {side: {} for side in self.theoretical_moves}
            self.show_moves()

        if not success:
            return

        if self.promotion_piece:
            piece = self.promotion_piece
            self.end_promotion()
            if self.move_history and self.move_history[-1]:
                if self.move_history[-1].is_edit == 1:
                    self.start_promotion(piece, self.edit_promotions[self.get_promotion_side(piece)])
                elif self.move_history[-1].piece.board_pos == piece.board_pos:
                    if piece.is_empty():
                        self.try_drop(self.move_history[-1])
                    else:
                        self.try_promotion(self.move_history[-1])
        else:
            if not with_history and not self.edit_mode:
                self.update_status()
            selection = data.get('selection')
            if selection:
                self.select_piece(fra(selection))

        self.load_data = dump
        self.load_dict = data
        self.save_loaded = success

    def empty_board(self) -> None:
        self.save_interval = 0

        self.deselect_piece()
        self.clear_en_passant()
        self.clear_castling_ep()
        self.clear_auto_capture_markers()
        self.reset_captures()

        self.turn_side = self.turn_order[0]
        if isinstance(self.turn_side, list):
            self.turn_side, self.turn_pieces = self.turn_side[0], set(self.turn_side[1])
        else:
            self.turn_pieces = None

        self.game_over = False
        self.chain_start = None
        self.promotion_piece = None
        self.action_count = 0
        self.ply_count = 0

        for sprite_list in self.piece_sprite_list, self.promotion_piece_sprite_list, self.promotion_area_sprite_list:
            sprite_list.clear()
            for sprite in sprite_list:
                sprite_list.remove(sprite)

        self.log(f"[Ply {self.ply_count}] Info: Board cleared")
        self.ply_count += 1
        if not self.edit_mode:
            self.log(f"[Ply {self.ply_count}] Mode: EDIT", False)
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

        self.update_status()

    def reset_custom_data(self) -> None:
        self.alias_dict = {}
        self.custom_drops = {}
        self.custom_pieces = {}
        self.custom_layout = {}
        self.custom_promotions = {}
        if isinstance(self.board_config['stalemate'], dict):
            self.stalemate_rule = {Side(k + 1): (v + 1) % 3 - 1 for k, v in self.board_config['stalemate'].items()}
        else:
            self.stalemate_rule = self.board_config['stalemate']
        self.turn_order = [Side.WHITE, Side.BLACK]

    def reset_captures(self) -> None:
        self.captured_pieces = {Side.WHITE: [], Side.BLACK: []}
        for side in self.captured_pieces:
            if side in self.custom_extra_drops:
                self.captured_pieces[side].extend(self.custom_extra_drops[side])

    def reset_drops(self, piece_sets: dict[Side, list[Type[Piece]]] | None = None) -> None:
        if self.custom_drops:
            self.drops = deepcopy(self.custom_drops)
            return
        if piece_sets is None:
            piece_sets = self.piece_sets
        self.drops = {}
        drop_squares = {
            Side.WHITE: [(i, j) for i in range(self.board_height) for j in range(self.board_width)],
            Side.BLACK: [(i, j) for i in range(self.board_height) for j in range(self.board_width)],
        }
        pawn_drop_squares = {
            Side.WHITE: [(i, j) for i in range(2, self.board_height) for j in range(self.board_width)],
            Side.BLACK: [(i, j) for i in range(0, self.board_height - 2) for j in range(self.board_width)],
        }
        pawn_drop_squares_2 = {
            Side.WHITE: [(1, j) for j in range(self.board_width)],
            Side.BLACK: [(self.board_height - 2, j) for j in range(self.board_width)],
        }
        for drop_side in piece_sets:
            drops = {}
            for side in (drop_side, drop_side.opponent()):
                if not piece_sets[side]:
                    continue
                drops[fide.Pawn] = {}
                pawn = fide.Pawn(self)
                pawn.movement.set_moves(1)
                for pos in pawn_drop_squares[side]:
                    drops[fide.Pawn][pos] = pawn
                for pos in pawn_drop_squares_2[side]:
                    drops[fide.Pawn][pos] = fide.Pawn
                piece_type = piece_sets[side][0]
                drops[piece_type] = {}
                piece = piece_type(self)
                piece.movement.set_moves(1)
                for pos in drop_squares[side]:
                    drops[piece_type][pos] = piece
                for piece_type in piece_sets[side][1:-1]:
                    if piece_type not in drops and not issubclass(piece_type, Royal):
                        drops[piece_type] = {pos: piece_type for pos in drop_squares[side]}
                if piece_sets[side][-1] not in drops:
                    piece_type = piece_sets[side][-1]
                    drops[piece_type] = {}
                    piece = piece_type(self)
                    piece.movement.set_moves(1)
                    for pos in drop_squares[side]:
                        drops[piece_type][pos] = piece
            self.drops[drop_side] = drops

    def reset_promotions(self, piece_sets: dict[Side, list[Type[Piece]]] | None = None) -> None:
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
        for side in promotion_squares:
            if not piece_sets[side]:
                continue
            promotions = []
            used_piece_set = set()
            for pieces in (
                piece_sets[side][3::-1], piece_sets[side.opponent()][3::-1],
                piece_sets[side][5:], piece_sets[side.opponent()][5:],
            ):
                promotion_types = []
                for piece in pieces:
                    if piece not in used_piece_set and not issubclass(piece, Royal):
                        used_piece_set.add(piece)
                        promotion_types.append(piece)
                promotions.extend(promotion_types[::-1])
            self.promotions[side] = {fide.Pawn: {pos: promotions.copy() for pos in promotion_squares[side]}}

    def reset_edit_promotions(self, piece_sets: dict[Side, list[Type[Piece]]] | None = None) -> None:
        if is_prefix_of('custom', self.edit_piece_set_id):
            self.edit_promotions = {
                side: [piece_type for _, piece_type in self.custom_pieces.items()] + [Block, Wall]
                for side in self.edit_promotions
            }
            return
        if is_prefix_of('wall', self.edit_piece_set_id):
            self.edit_promotions = {side: [Block, Wall] for side in self.edit_promotions}
            return
        if piece_sets is None:
            if self.edit_piece_set_id is None:
                piece_sets = self.piece_sets
            else:
                piece_sets = self.get_piece_sets(self.edit_piece_set_id)[0]
        self.edit_promotions = {side: [] for side in self.edit_promotions}
        for side in self.edit_promotions:
            used_piece_set = set()
            for pieces in (
                piece_sets[side][3::-1], piece_sets[side.opponent()][3::-1],
                piece_sets[side][5:], piece_sets[side.opponent()][5:],
                [piece_sets[side.opponent()][4], fide.Pawn, piece_sets[side][4]]
            ):
                promotion_types = []
                for piece in pieces:
                    if piece not in used_piece_set:
                        used_piece_set.add(piece)
                        promotion_types.append(piece)
                self.edit_promotions[side].extend(promotion_types[::-1])

    def reset_penultima_pieces(self, piece_sets: dict[Side, list[Type[Piece]]] | None = None) -> None:
        if piece_sets is None:
            piece_sets = self.piece_sets
        self.penultima_pieces = {side: {} for side in self.penultima_pieces}
        for player_side in self.penultima_pieces:
            for piece_side in (player_side, player_side.opponent()):
                for i, piece in enumerate(piece_sets[piece_side]):
                    if penultima_textures[i]:
                        texture = penultima_textures[i]
                        if piece_side == player_side.opponent():
                            texture += 'O'
                        if i > 4 and piece != piece_sets[player_side][7 - i]:
                            texture += '|'
                        if piece not in self.penultima_pieces[player_side]:
                            self.penultima_pieces[player_side][piece] = texture

    def get_piece_sets(
            self,
            piece_set_ids: dict[Side, int] | int | None = None
    ) -> tuple[dict[Side, list[Type[Piece]]], dict[Side, str]]:
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
            elif piece_set_ids[side] < 0:
                for i in range(-piece_set_ids[side]):
                    if i + 1 not in self.chaos_sets:
                        self.chaos_sets[i + 1] = self.get_chaos_set(side)
                chaos_set = self.chaos_sets.get(-piece_set_ids[side], [empty_row, '-'])
                piece_sets[side] = chaos_set[0].copy()
                piece_names[side] = chaos_set[1]
            else:
                piece_group = piece_groups[piece_set_ids[side]]
                piece_sets[side] = get_set(side, piece_set_ids[side]).copy()
                piece_names[side] = piece_group.get('name', '-')
            if not piece_sets[side]:
                piece_sets[side] = empty_row.copy()
                piece_names[side] = '-'
        return piece_sets, piece_names

    def get_random_set(self, side: Side, asymmetrical: bool = False) -> tuple[list[Type[Piece]], str]:
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
        piece_set = empty_row.copy()
        for i, group in enumerate(random_set_poss):
            random_set_ids = self.chaos_rng.sample(piece_set_ids, k=len(group))
            for j, poss in enumerate(group):
                for pos in poss:
                    piece_set[pos] = get_set(side, random_set_ids[j])[pos]
        return piece_set, get_set_name(piece_set)

    def get_extremely_random_set(self, side: Side, asymmetrical: bool = False) -> tuple[list[Type[Piece]], str]:
        blocked_ids = set(self.board_config['block_ids_chaos'])
        piece_set_ids = list(i for i in range(len(piece_groups)) if i not in blocked_ids)
        piece_pos_ids = [i for i in range(4)] + [7]
        piece_poss = [
            (i, j) for i in piece_set_ids for j in piece_pos_ids
            if j < 4 or get_set(side, i)[j] != get_set(side, i)[7 - j]
        ]
        random_set_ids = self.chaos_rng.sample(piece_poss, k=7 if asymmetrical else 4)
        if asymmetrical:
            random_set_poss = [[i] for i in range(8) if i != 4]
        else:
            random_set_poss = [[0, 7], [1, 6], [2, 5], [3]]
        piece_set = empty_row.copy()
        for i, group in enumerate(random_set_poss):
            set_id, set_pos = random_set_ids[i]
            for j, pos in enumerate(group):
                random_set = get_set(side, set_id)
                piece_set[pos] = random_set[set_pos]
                if self.chaos_mode == 3 and set_pos != 3 and j > 0:
                    if random_set[set_pos] != random_set[7 - set_pos]:
                        piece_set[pos] = random_set[7 - set_pos]
        piece_set[4] = cb.King if piece_set[0].is_colorbound() else fide.King
        return piece_set, get_set_name(piece_set)

    def get_chaos_set(self, side: Side) -> tuple[list[Type[Piece]], str]:
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
        self.log(f"[Ply {self.ply_count}] Info: Starting new game (with {chaotic} piece {sets})")
        self.chaos_mode = mode
        self.chaos_sets = {}
        self.chaos_seed = self.chaos_rng.randint(0, max_seed)
        self.chaos_rng = Random(self.chaos_seed)
        self.piece_set_ids = {Side.WHITE: -1, Side.BLACK: -1 if same else -2}
        self.reset_custom_data()
        self.reset_board()

    def load_pieces(self):
        self.movable_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.royal_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.quasi_royal_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.probabilistic_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.auto_ranged_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.obstacles = []
        for row, col in product(range(self.board_height), range(self.board_width)):
            piece = self.get_piece((row, col))
            side = piece.side
            if side in self.movable_pieces and not piece.is_empty():
                self.movable_pieces[side].append(piece)
                if isinstance(piece, Royal):
                    self.royal_pieces[side].append(piece)
                elif isinstance(piece, QuasiRoyal):
                    self.quasi_royal_pieces[side].append(piece)
                if isinstance(piece.movement, movement.ProbabilisticMovement):
                    self.probabilistic_pieces[side].append(piece)
                if isinstance(piece.movement, movement.AutoRangedAutoCaptureRiderMovement):
                    self.auto_ranged_pieces[side].append(piece)
            elif isinstance(piece, Obstacle):
                self.obstacles.append(piece)
        if self.royal_piece_mode == 1:  # Force royal pieces
            for side in (Side.WHITE, Side.BLACK):
                self.royal_pieces[side].extend(self.quasi_royal_pieces[side])
                self.quasi_royal_pieces[side].clear()
        if self.royal_piece_mode == 2:  # Force quasi-royal pieces
            for side in (Side.WHITE, Side.BLACK):
                self.quasi_royal_pieces[side].extend(self.royal_pieces[side])
                self.royal_pieces[side].clear()
        if self.royal_piece_mode != 1:  # If not forcing to royal and there is only one quasi-royal piece, make it royal
            for side in (Side.WHITE, Side.BLACK):
                if len(self.quasi_royal_pieces[side]) == 1:
                    self.royal_pieces[side].append(self.quasi_royal_pieces[side].pop())
        if self.ply_count == 1:
            for side in self.auto_ranged_pieces:
                if self.auto_ranged_pieces[side] and not self.auto_capture_markers[side]:
                    self.load_auto_capture_markers(side)

    def load_check(self, side: Side = None) -> bool:
        if side is None:
            side = self.turn_side
        self.load_pieces()
        self.check_side = Side.NONE
        if not self.use_check:
            return False
        for royal in self.royal_pieces[side]:
            self.ply_simulation += 1
            for piece in self.movable_pieces[side.opponent()]:
                if isinstance(piece.movement, movement.ProbabilisticMovement):
                    continue
                for move in piece.moves():
                    last_move = copy(move)
                    self.update_move(last_move)
                    if last_move.promotion and not last_move.is_edit:
                        piece = last_move.promotion
                        if isinstance(piece.movement, movement.RangedAutoCaptureRiderMovement):
                            piece.movement.generate_captures(last_move, piece)
                    else:
                        self.update_auto_captures(last_move, side)
                    while last_move:
                        if last_move.pos_to == royal.board_pos or last_move.captured_piece == royal:
                            self.check_side = side
                            break
                        last_move = last_move.chained_move
                    if self.check_side:
                        break
                if self.check_side:
                    break
            self.ply_simulation -= 1
            if self.check_side:
                break

    def load_moves(
        self,
        force_reload: bool = True,
        moves_for: Side | None = None,
        theoretical_moves_for:  Side | None = None
    ) -> None:
        if force_reload:
            self.game_over = False
            self.moves_queried = {side: False for side in self.moves_queried}
            self.theoretical_moves_queried = {side: False for side in self.theoretical_moves_queried}
        self.load_check()
        movable_pieces = {side: self.movable_pieces[side].copy() for side in self.movable_pieces}
        royal_pieces = {side: self.royal_pieces[side].copy() for side in self.royal_pieces}
        quasi_royal_pieces = {side: self.quasi_royal_pieces[side].copy() for side in self.quasi_royal_pieces}
        probabilistic_pieces = {side: self.probabilistic_pieces[side].copy() for side in self.probabilistic_pieces}
        auto_ranged_pieces = {side: self.auto_ranged_pieces[side].copy() for side in self.auto_ranged_pieces}
        auto_capture_markers = deepcopy(self.auto_capture_markers)
        check_side = self.check_side
        en_passant_target = self.en_passant_target
        en_passant_markers = self.en_passant_markers.copy()
        castling_ep_target = self.castling_ep_target
        castling_ep_markers = self.castling_ep_markers.copy()
        for turn_side in [Side.WHITE, Side.BLACK]:
            if self.move_history and (
                not self.use_check or (
                    self.move_history[-1] and
                    self.move_history[-1].movement_type == movement.DropMovement and
                    isinstance(self.move_history[-1].promotion, Piece) and
                    isinstance(self.move_history[-1].promotion.movement, movement.RangedAutoCaptureRiderMovement)
                )
            ):
                # we need to check if there's a move in the move history that could be a capture
                royal_capture = False  # of one of the opposing pieces that are treated as royal
                chained_move = self.move_history[-1]  # checking the last move's sufficient here
                while chained_move:  # NB: could be None but if it is the loop is skipped anyway
                    capture = chained_move.captured_piece
                    if capture and capture.side == turn_side:
                        # NB: quasi-royal pieces are treated as royal if only one remains!
                        royal_capture = isinstance(capture, Royal) or isinstance(capture, QuasiRoyal)
                        if self.royal_piece_mode == 0 and royal_capture:
                            # treat as royal capture iff no strictly royal pieces exist
                            royal_capture = not self.royal_pieces[turn_side]
                        elif self.royal_piece_mode == 2 and royal_capture:
                            # treat as royal capture iff no quasi or royal pieces exist
                            royal_capture = not self.royal_pieces[turn_side] and not self.quasi_royal_pieces[turn_side]
                        if royal_capture:
                            break
                    chained_move = chained_move.chained_move
                if royal_capture:
                    check_side = turn_side
                    self.moves[turn_side] = {}
                    self.moves_queried[turn_side] = True
                    self.game_over = True
                    continue
        last_chain_move = self.chain_start
        if last_chain_move:
            chained_move = last_chain_move
            while chained_move.chained_move:
                if not (
                    issubclass(chained_move.movement_type, movement.CastlingMovement)
                    and chained_move.chained_move.pos_from != last_chain_move.pos_to
                    or isinstance(chained_move.piece.movement, movement.RangedAutoCaptureRiderMovement)
                ):
                    last_chain_move = chained_move
                chained_move = chained_move.chained_move
        if moves_for is None:
            moves_for = self.turn_side
        if moves_for == Side.ANY:
            turn_sides = [Side.WHITE, Side.BLACK]
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
                            if isinstance(piece.movement, movement.ProbabilisticMovement):
                                self.roll_history[self.ply_count - 1][pos] = piece.movement.roll()
                    self.probabilistic_piece_history[self.ply_count - 1] = signature
            for piece in movable_pieces[turn_side] if chain_moves is None else [last_chain_move.piece]:
                if self.turn_pieces is not None and type(piece) not in self.turn_pieces:
                    continue
                for move in piece.moves() if chain_moves is None else chain_moves:
                    self.update_move(move)
                    self.update_auto_capture_markers(move)
                    self.update_auto_captures(move, turn_side.opponent())
                    self.move(move)
                    if move.promotion:
                        self.promotion_piece = True
                        self.replace(move.piece, move.promotion)
                        self.update_auto_capture_markers(move)
                        self.update_promotion_auto_captures(move)
                        self.promotion_piece = None
                    move_chain = [move]
                    chained_move = move.chained_move
                    end_early = False
                    if (
                        self.use_check and chained_move
                        and issubclass(type(move.piece), Slow)
                        and move.piece in royal_pieces[turn_side]
                    ):
                        self.load_check(turn_side)
                        if self.check_side == turn_side:
                            if self.use_check:
                                end_early = True
                    while not end_early and chained_move:
                        self.update_move(chained_move)
                        self.move(chained_move)
                        if chained_move.promotion:
                            self.promotion_piece = True
                            self.replace(chained_move.piece, chained_move.promotion)
                            self.update_auto_capture_markers(chained_move)
                            self.update_promotion_auto_captures(chained_move)
                            self.promotion_piece = None
                        else:
                            self.update_auto_capture_markers(chained_move)
                        move_chain.append(chained_move)
                        if (
                            self.use_check and chained_move.chained_move
                            and issubclass(type(chained_move.piece), Slow)
                            and chained_move.piece in royal_pieces[turn_side]
                        ):
                            self.load_check(turn_side)
                            if self.check_side == turn_side:
                                end_early = True
                        if not end_early:
                            chained_move = chained_move.chained_move
                    if not end_early:
                        self.load_check(turn_side)
                    if self.use_check:
                        for chained_move in move_chain:
                            if chained_move.captured_piece in royal_pieces[turn_side]:
                                self.check_side = turn_side
                            if chained_move.captured_piece in royal_pieces[self.turn_side.opponent()]:
                                check_side = self.turn_side.opponent()
                                self.moves[self.turn_side.opponent()] = {}
                                self.moves_queried[self.turn_side.opponent()] = True
                                self.game_over = True
                    if self.check_side != turn_side:
                        pos_from, pos_to = move.pos_from, move.pos_to
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
                            issubclass(chained_move.movement_type, movement.CastlingMovement)
                            and chained_move.chained_move.pos_from != move.pos_to
                            or isinstance(chained_move.piece.movement, movement.RangedAutoCaptureRiderMovement)
                        ):
                            poss.extend((chained_move.pos_from, chained_move.pos_to))
                            chained_move = chained_move.chained_move
                        poss.extend((chained_move.pos_from, chained_move.pos_to))
                        if chained_move.chained_move:
                            self.chain_moves[turn_side].setdefault(tuple(poss), []).append(chained_move.chained_move)
                    for chained_move in move_chain[::-1]:
                        self.undo(chained_move)
                        self.revert_auto_capture_markers(chained_move)
                    self.check_side = check_side
                    self.clear_en_passant()
                    self.clear_castling_ep()
                    if en_passant_target is not None:
                        for marker in en_passant_markers:
                            self.mark_en_passant(en_passant_target.board_pos, marker)
                    if castling_ep_target is not None:
                        for marker in castling_ep_markers:
                            self.mark_castling_ep(castling_ep_target.board_pos, marker)
            self.moves_queried[turn_side] = True
        if theoretical_moves_for is None:
            if self.game_over and self.check_side == self.turn_side.opponent():
                theoretical_moves_for = Side.NONE
            else:
                theoretical_moves_for = self.turn_side.opponent()
        if theoretical_moves_for == Side.ANY:
            turn_sides = [Side.WHITE, Side.BLACK]
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
                    pos_from, pos_to = move.pos_from, move.pos_to
                    self.theoretical_moves[turn_side].setdefault(pos_from, {}).setdefault(pos_to, []).append(move)
            self.theoretical_moves_queried[turn_side] = True
        self.movable_pieces = movable_pieces
        self.royal_pieces = royal_pieces
        self.quasi_royal_pieces = quasi_royal_pieces
        self.probabilistic_pieces = probabilistic_pieces
        self.auto_ranged_pieces = auto_ranged_pieces
        self.auto_capture_markers = auto_capture_markers
        self.check_side = check_side
        if force_reload and not self.edit_mode and not self.moves.get(self.turn_side, {}):
            drop_exists = False
            if self.use_drops and self.turn_side in self.drops:
                side_drops = self.drops[self.turn_side]
                for piece_type in self.captured_pieces[self.turn_side]:
                    if piece_type not in side_drops:
                        continue
                    if self.turn_pieces is not None and piece_type not in self.turn_pieces:
                        continue
                    for pos in side_drops[piece_type]:
                        if self.get_piece(pos).is_empty():
                            drop_exists = True
                            break
                    if drop_exists:
                        break
            if not drop_exists:
                self.game_over = True

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
            for move in sum((sum(v.values(), []) for v in self.moves.get(turn_side, {}).values()), []):
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
                        issubclass(chained_move.movement_type, movement.CastlingMovement)
                        and chained_move.chained_move.pos_from != move.pos_to
                        or isinstance(chained_move.piece.movement, movement.RangedAutoCaptureRiderMovement)
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

    def show_moves(self) -> None:
        self.hide_moves()
        self.update_caption()
        move_sprites = dict()
        pos = self.selected_square or self.hovered_square
        if not pos and self.is_active:
            pos = self.highlight_square
        if self.on_board(pos):
            piece = self.get_piece(pos)
            hide_moves = self.should_hide_moves
            if hide_moves is None:
                hide_moves = piece.is_hidden
            if not piece.is_empty() and not hide_moves:
                if self.display_theoretical_moves.get(piece.side, False):
                    move_dict = self.theoretical_moves.get(piece.side, {})
                elif self.display_moves.get(piece.side, False):
                    move_dict = self.moves.get(piece.side, {})
                else:
                    move_dict = {}
                for pos_to in move_dict.get(pos, {}):
                    if pos_to in move_sprites:
                        continue
                    sprite = Sprite(f"assets/util/{'move' if self.not_a_piece(pos_to) else 'capture'}.png")
                    sprite.color = self.color_scheme['selection_color' if self.selected_square else 'highlight_color']
                    sprite.position = self.get_screen_position(pos_to)
                    sprite.scale = self.square_size / sprite.texture.width
                    self.move_sprite_list.append(sprite)
                    move_sprites[pos_to] = sprite
        if not self.selected_square and self.move_history and not self.edit_mode:
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

    def update_board(self, move: Move) -> None:
        if move.chained_move is not None:
            return
        if self.en_passant_target is not None and move.piece.side == self.en_passant_target.side.opponent():
            self.clear_en_passant()
        if self.castling_ep_target is not None and move.piece.side == self.castling_ep_target.side.opponent():
            self.clear_castling_ep()

    def update_move(self, move: Move) -> None:
        if move.pos_from:
            move.set(piece=self.get_piece(move.pos_from))
        new_piece = move.swapped_piece or move.captured_piece
        new_piece = self.get_piece(new_piece.board_pos if new_piece is not None else move.pos_to)
        if move.piece != new_piece and not new_piece.is_empty():
            if move.swapped_piece is not None:
                move.set(swapped_piece=new_piece)
            else:
                move.set(captured_piece=new_piece)

    def mark_en_passant(self, piece_pos: Position, marker_pos: Position) -> None:
        self.en_passant_target = self.get_piece(piece_pos)
        self.en_passant_markers.add(marker_pos)

    def clear_en_passant(self) -> None:
        self.en_passant_target = None
        self.en_passant_markers = set()

    def mark_castling_ep(self, piece_pos: Position, marker_pos: Position) -> None:
        self.castling_ep_target = self.get_piece(piece_pos)
        self.castling_ep_markers.add(marker_pos)

    def clear_castling_ep(self) -> None:
        self.castling_ep_target = None
        self.castling_ep_markers = set()

    def update_auto_captures(self, move: Move, side: Side) -> None:
        if move.is_edit:
            return
        while move.chained_move and not (issubclass(
            move.chained_move.movement_type,
            movement.AutoRangedAutoCaptureRiderMovement
        ) and move.chained_move.piece.side == side):
            move = move.chained_move
        if move.pos_to in self.auto_capture_markers[side]:
            piece_poss = self.auto_capture_markers[side][move.pos_to]
            piece_pos = sorted(list(piece_poss))[0]
            piece = self.get_piece(piece_pos)
            move_piece = self.get_piece(move.pos_to) if move.piece.is_empty() else move.piece
            if piece.side == side and piece.captures(move_piece):
                chained_move = Move(
                    piece=piece,
                    movement_type=type(piece.movement),
                    pos_from=piece_pos,
                    pos_to=piece_pos,
                    captured_piece=move_piece,
                )
                move.chained_move = chained_move

    def update_promotion_auto_captures(self, move: Move) -> None:
        piece = self.get_piece(move.pos_to)
        move.chained_move = None
        if isinstance(piece.movement, movement.RangedAutoCaptureRiderMovement):
            piece.movement.generate_captures(move, piece)
        self.update_auto_capture_markers(move)
        self.update_auto_captures(move, piece.side.opponent())

    def load_auto_capture_markers(self, side: Side = Side.ANY) -> None:
        for side in self.auto_ranged_pieces if side is Side.ANY else (side,):
            for piece in self.auto_ranged_pieces[side]:
                if isinstance(piece.movement, movement.AutoRangedAutoCaptureRiderMovement):
                    piece.movement.mark(piece.board_pos, piece)

    def clear_auto_capture_markers(self, side: Side = Side.ANY) -> None:
        for side in self.auto_capture_markers if side is Side.ANY else (side,):
            self.auto_capture_markers[side].clear()

    def update_auto_capture_markers(self, move: Move) -> None:
        while move:
            moved_piece = move.piece
            if move.promotion:
                if isinstance(moved_piece.movement, movement.AutoRangedAutoCaptureRiderMovement):
                    moved_piece.movement.unmark(move.pos_to, moved_piece)
                moved_piece = self.get_piece(move.pos_to)
            if isinstance(moved_piece.movement, movement.AutoRangedAutoCaptureRiderMovement):
                if move.pos_to is None or move.is_edit:
                    moved_piece.movement.unmark(move.pos_from, moved_piece)
                if move.pos_from is None or move.is_edit or move.promotion:
                    moved_piece.movement.mark(move.pos_to, moved_piece)
            if move.captured_piece is not None:
                if isinstance(move.captured_piece.movement, movement.AutoRangedAutoCaptureRiderMovement):
                    move.captured_piece.movement.unmark(move.captured_piece.board_pos, move.captured_piece)
            if move.swapped_piece is not None:
                if isinstance(move.swapped_piece.movement, movement.AutoRangedAutoCaptureRiderMovement):
                    move.swapped_piece.movement.unmark(move.pos_to, move.swapped_piece)
                    move.swapped_piece.movement.mark(move.pos_from, move.swapped_piece)
            move = move.chained_move

    def revert_auto_capture_markers(self, move: Move) -> None:
        move_list = []
        while move:
            move_list.append(move)
            move = move.chained_move
        for move in reversed(move_list):
            if move.promotion:
                moved_piece = self.get_piece(move.pos_to)
                if isinstance(moved_piece.movement, movement.AutoRangedAutoCaptureRiderMovement):
                    moved_piece.movement.unmark(move.pos_to, moved_piece)
            moved_piece = move.piece
            if isinstance(moved_piece.movement, movement.AutoRangedAutoCaptureRiderMovement):
                if move.pos_from is None or move.is_edit:
                    moved_piece.movement.unmark(move.pos_to, moved_piece)
                if move.pos_to is None or move.is_edit or move.promotion:
                    moved_piece.movement.mark(move.pos_from, moved_piece)
            if move.captured_piece is not None:
                if isinstance(move.captured_piece.movement, movement.AutoRangedAutoCaptureRiderMovement):
                    move.captured_piece.movement.mark(move.captured_piece.board_pos, move.captured_piece)
            if move.swapped_piece is not None:
                if isinstance(move.swapped_piece.movement, movement.AutoRangedAutoCaptureRiderMovement):
                    move.swapped_piece.movement.unmark(move.pos_from, move.swapped_piece)
                    move.swapped_piece.movement.mark(move.pos_to, move.swapped_piece)

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
                self.move_history.append(None)
                turn_side = self.turn_order[self.ply_count % len(self.turn_order)]
                if isinstance(turn_side, list):
                    turn_pieces = f" ({', '.join(sorted(piece.name for piece in turn_side[1]))})"
                    turn_side = turn_side[0]
                else:
                    turn_pieces = ''
                self.log(f"[Ply {self.ply_count}] Pass: {turn_side} to move{turn_pieces}")
                self.ply_count += 1
                self.clear_en_passant()
                self.clear_castling_ep()
            if next_move.is_edit:
                self.update_move(next_move)
                next_move.piece.move(next_move)
                self.update_auto_capture_markers(next_move)
                self.move_history.append(deepcopy(next_move))
                self.apply_edit_promotion(next_move)
                if next_move.promotion is Unset:
                    finished = True
                    break
                if self.promotion_piece is None:
                    self.log(f"[Ply {self.ply_count}] Edit: {self.move_history[-1]}")
            elif next_move.movement_type == movement.DropMovement:
                pos = next_move.pos_to
                if not self.not_on_board(pos) and self.get_piece(pos).is_empty():
                    if next_move.promotion is Unset:
                        self.try_drop(next_move)
                        if self.promotion_piece:
                            self.move_history.append(next_move)
                    else:
                        if next_move.placed_piece is not None:
                            for i, piece in enumerate(self.captured_pieces[self.turn_side][::-1]):
                                if piece == next_move.placed_piece:
                                    self.captured_pieces[self.turn_side].pop(-(i + 1))
                                    break
                        promotion_piece = self.promotion_piece
                        self.promotion_piece = True
                        self.replace(next_move.piece, next_move.promotion)
                        self.update_promotion_auto_captures(next_move)
                        self.promotion_piece = promotion_piece
                        self.log(f"[Ply {self.ply_count}] Drop: {next_move}")
                        self.move_history.append(next_move)
                        self.ply_count += 1
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
                    issubclass(chained_move.movement_type, movement.CastlingMovement)
                    and chained_move.chained_move.pos_from != move.pos_to
                    or isinstance(chained_move.piece.movement, movement.RangedAutoCaptureRiderMovement)
                ):
                    poss.extend((chained_move.pos_from, chained_move.pos_to))
                    chained_move = chained_move.chained_move
                poss.extend((chained_move.pos_from, chained_move.pos_to))
                if chained_move.chained_move or self.chain_moves.get(self.turn_side, {}).get(tuple(poss)):
                    chained_move.chained_move = Unset  # do not chain moves because we're updating every move separately
                self.update_auto_capture_markers(move)
                self.update_auto_captures(move, self.turn_side.opponent())
                chained_move = move
                while chained_move:
                    chained_move.piece.move(chained_move)
                    self.update_auto_capture_markers(chained_move)
                    chained_move.set(piece=copy(chained_move.piece))
                    if self.promotion_piece is None:
                        self.log(f"[Ply {self.ply_count}] Move: {chained_move}")
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
                if next_move.chained_move is Unset and not self.promotion_piece:
                    self.load_moves()
                    chained = True
                else:
                    self.chain_start = None
                    if self.promotion_piece is None:
                        self.ply_count += 1
            if not chained:
                self.advance_turn()
            if self.promotion_piece:
                finished = True
                break
            if chained:
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
        if move.piece.side in self.drops and not move.is_edit == 1:
            captured_piece = move.piece if move.pos_to is None else move.captured_piece
            if captured_piece is not None and move.piece.side in self.captured_pieces:
                capture_type = captured_piece.promoted_from or type(captured_piece)
                if capture_type in self.drops[move.piece.side]:
                    # droppable piece was captured, add it to the roster of captured pieces
                    self.captured_pieces[move.piece.side].append(capture_type)
        if move.is_edit != 1 and move.movement_type != movement.DropMovement:
            # call movement.update() to update movement state after the move (e.g. pawn double move, castling rights)
            move.piece.movement.update(move, move.piece)
        if move.is_edit != 1:
            if move.piece.is_empty():
                # check if a piece can be dropped
                self.try_drop(move)
            else:
                if (
                    not move.is_edit
                    and not self.use_check
                    and issubclass(type(move.piece), Slow)
                    and move.piece in self.royal_pieces[move.piece.side]
                ):
                    self.mark_castling_ep(move.piece.board_pos, move.pos_to)
                # check if the piece needs to be promoted
                self.try_promotion(move)

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
            if not move.piece.is_empty():
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
            if not self.is_trickster_mode():  # reset_trickster_mode() does not reset removed pieces
                move.captured_piece.angle = 0  # so instead we have to do it manually as a workaround
            self.update_piece(move.captured_piece)  # update the piece sprite to reflect current piece hiding mode
            self.pieces[capture_pos[0]][capture_pos[1]] = move.captured_piece
            self.piece_sprite_list.append(move.captured_piece)
        if move.piece.side in self.drops and move.is_edit != 1:
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
        if move.is_edit != 1 and move.movement_type != movement.DropMovement:
            # call movement.undo() to restore movement state before the move (e.g. pawn double move, castling rights)
            move.piece.movement.undo(move, move.piece)

    def undo_last_move(self) -> None:
        self.deselect_piece()
        if not self.move_history:
            return
        in_promotion = self.promotion_piece is not None
        if in_promotion:
            if self.move_history and self.future_move_history:
                past, future = self.move_history[-1], self.future_move_history[-1]
                if (
                    past and future and past.pos_from == future.pos_from and past.pos_to == future.pos_to
                    and not (past.captured_piece is not None and future.swapped_piece is not None)
                    and not (past.swapped_piece is not None and future.captured_piece is not None)
                    and future.promotion is not None
                ):
                    past.promotion = future.promotion
                    if future.placed_piece is not None:
                        past.placed_piece = future.placed_piece
            self.end_promotion()
        else:
            last_move = self.move_history[-1]
            self.ply_count -= 1 if last_move is None else not last_move.is_edit and self.chain_start is None
        last_move = self.move_history.pop()
        if last_move is not None:
            move_chain = [last_move]
            chained_move = last_move.chained_move
            while chained_move:
                move_chain.append(chained_move)
                chained_move = chained_move.chained_move
            for chained_move in move_chain[::-1]:
                if (
                    chained_move.is_edit == 2
                    and chained_move.pos_from == chained_move.pos_to
                    and chained_move.promotion is None
                ):
                    chained_move.set(piece=self.get_piece(chained_move.pos_to))
                self.undo(chained_move)
                self.revert_auto_capture_markers(chained_move)
                if chained_move.promotion is not None:
                    if chained_move.placed_piece is not None:
                        turn_side = self.turn_order[(self.ply_count - 1) % len(self.turn_order)]
                        if isinstance(turn_side, list):
                            turn_side = turn_side[0]
                        if chained_move.placed_piece in self.drops[turn_side]:
                            self.captured_pieces[turn_side].append(chained_move.placed_piece)
                    if not chained_move.piece.is_empty():
                        self.update_piece(chained_move.piece)
                logged_move = copy(chained_move)
                if in_promotion:
                    logged_move.set(promotion=Unset)
                move_type = (
                    'Edit' if logged_move.is_edit
                    else 'Drop' if logged_move.movement_type == movement.DropMovement
                    else 'Move'
                )
                self.log(f"[Ply {self.ply_count}] Undo: {move_type}: {logged_move}")
                in_promotion = False
        else:
            turn_side = self.turn_order[(self.ply_count - 1) % len(self.turn_order)]
            if isinstance(turn_side, list):
                turn_pieces = f" ({', '.join(sorted(piece.name for piece in turn_side[1]))})"
                turn_side = turn_side[0]
            else:
                turn_pieces = ''
            self.log(f"[Ply {self.ply_count}] Undo: Pass: {turn_side} to move{turn_pieces}")
        if self.move_history:
            move = self.move_history[-1]
            if move is not None and move.is_edit != 1 and move.movement_type != movement.DropMovement:
                move.piece.movement.reload(move, move.piece)
        future_move_history = self.future_move_history.copy()
        if self.chain_start is None:
            self.advance_turn()
        else:
            self.chain_start = None
            self.load_moves()
            self.show_moves()
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
                self.future_move_history.append(last_move)
        else:
            self.future_move_history.append(last_move)

    def redo_last_move(self) -> None:
        self.deselect_piece()
        piece_was_moved = False
        if self.promotion_piece is not None:
            if self.move_history and self.future_move_history:
                past, future = self.move_history[-1], self.future_move_history[-1]
                if (
                    past and future and past.pos_from == future.pos_from and past.pos_to == future.pos_to
                    and not (past.captured_piece is not None and future.swapped_piece is not None)
                    and not (past.swapped_piece is not None and future.captured_piece is not None)
                    and future.promotion
                ):
                    past.promotion = future.promotion
                    if future.placed_piece is not None:
                        past.placed_piece = future.placed_piece
                        for i, piece in enumerate(self.captured_pieces[self.turn_side][::-1]):
                            if piece == future.placed_piece:
                                self.captured_pieces[self.turn_side].pop(-(i + 1))
                                break
                    self.replace(self.promotion_piece, future.promotion)
                    self.update_auto_capture_markers(self.move_history[-1])
                    self.update_promotion_auto_captures(self.move_history[-1])
                    self.end_promotion()
                else:
                    return
            else:
                return
            piece_was_moved = True
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
            turn_side = self.turn_order[self.ply_count % len(self.turn_order)]
            if isinstance(turn_side, list):
                turn_pieces = f" ({', '.join(sorted(piece.name for piece in turn_side[1]))})"
                turn_side = turn_side[0]
            else:
                turn_pieces = ''
            self.log(f"[Ply {self.ply_count}] Redo: Pass: {turn_side} to move{turn_pieces}")
            self.clear_en_passant()
            self.clear_castling_ep()
            self.move_history.append(deepcopy(last_move))
        elif piece_was_moved:
            chained_move = last_move
            while chained_move:
                move_type = (
                    'Edit' if chained_move.is_edit
                    else 'Drop' if chained_move.movement_type == movement.DropMovement
                    else 'Move'
                )
                self.log(f"[Ply {self.ply_count}] Redo: {move_type}: {chained_move}")
                last_chain_move = chained_move
                chained_move = chained_move.chained_move
                if chained_move:
                    chained_move.piece.move(chained_move)
                    self.update_auto_capture_markers(chained_move)
                    chained_move.set(piece=copy(chained_move.piece))
        else:
            if last_move.pos_from is not None:
                self.update_move(last_move)
                self.update_auto_capture_markers(last_move)
                self.update_auto_captures(last_move, self.turn_side.opponent())
            chained_move = last_move
            while chained_move:
                chained_move.piece.move(chained_move)
                self.update_auto_capture_markers(chained_move)
                chained_move.set(piece=copy(chained_move.piece))
                move_type = (
                    'Edit' if chained_move.is_edit
                    else 'Drop' if chained_move.movement_type == movement.DropMovement
                    else 'Move'
                )
                self.log(f"[Ply {self.ply_count}] Redo: {move_type}: {chained_move}")
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
            if self.promotion_piece is None:
                self.ply_count += 1 if last_move is None else not last_move.is_edit
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
            self.load_moves()
            self.select_piece(current_pos)

    def undo_last_finished_move(self) -> None:
        self.undo_last_move()
        while self.move_history and self.move_history[-1] is None:
            self.undo_last_move()

    def redo_last_finished_move(self) -> None:
        while self.future_move_history and self.future_move_history[-1] is None:
            self.redo_last_move()
        self.redo_last_move()

    def advance_turn(self) -> None:
        self.deselect_piece()
        # if we're promoting, we can't advance the turn yet
        if self.promotion_piece:
            return
        self.game_over = False
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
            self.load_pieces()  # loading the new piece positions in order to update the board state
            self.color_pieces()  # reverting the piece colors to normal in case they were changed
            return  # let's not advance the turn while editing the board to hopefully make things easier for everyone
        self.turn_side = self.turn_order[(self.ply_count - 1) % len(self.turn_order)]
        if isinstance(self.turn_side, list):
            self.turn_side, self.turn_pieces = self.turn_side[0], set(self.turn_side[1])
        else:
            self.turn_pieces = None
        self.update_status()

    def update_status(self) -> None:
        self.load_moves()  # this updates the check status as well
        self.show_moves()
        if self.game_over:
            # the game has ended. let's find out who won and show it by changing piece colors
            if self.check_side:
                if self.use_check:
                    # the current player was checkmated, the game ends and the opponent wins
                    self.log(f"[Ply {self.ply_count}] Info: Checkmate! {self.check_side.opponent()} wins.")
                else:
                    # the current player's royal piece was captured, the game ends and the opponent wins
                    self.log(f"[Ply {self.ply_count}] Info: King captured! {self.check_side.opponent()} wins.")
            else:
                # the current player was stalemated, let's consult the rules to see if it's a draw or a win
                if isinstance(self.stalemate_rule, dict):
                    rule = self.stalemate_rule.get(self.turn_side, 0)
                else:
                    rule = self.stalemate_rule
                if rule == 0:  # it's a draw
                    self.log(f"[Ply {self.ply_count}] Info: Stalemate! It's a draw.")
                elif rule == 1:  # stalemating player wins, stalemated player loses
                    self.log(f"[Ply {self.ply_count}] Info: Stalemate! {self.turn_side.opponent()} wins.")
                elif rule == -1:  # stalemating player loses, stalemated player wins
                    self.log(f"[Ply {self.ply_count}] Info: Stalemate! {self.turn_side} wins.")
                else:  # how did we get here?
                    self.log(f"[Ply {self.ply_count}] Info: Stalemate! The result is undefined.")
        else:
            if self.check_side:
                # the game is still going, but the current player is in check
                self.log(f"[Ply {self.ply_count}] Info: {self.check_side} is in check!")
            else:
                # the game is still going and there is no check
                pass
        self.color_all_pieces()

    def update_caption(self) -> None:
        selected_square = self.selected_square
        hovered_square = None
        if self.is_active:
            hovered_square = self.hovered_square or self.highlight_square
        if self.promotion_piece:
            piece = self.promotion_piece
            if piece.is_empty():
                if hovered_square in self.promotion_area:
                    promotion = self.promotion_area[hovered_square]
                    message = f"[Ply {self.ply_count}] {promotion}"
                else:
                    message = f"[Ply {self.ply_count}] "
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
                self.set_caption(message)
                return
            message = f"[Ply {self.ply_count}] {piece} on {toa(piece.board_pos)}"
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
            self.set_caption(message)
            return
        piece = self.get_piece(selected_square)
        if piece.is_empty():
            piece = None
        hide_piece = piece.is_hidden if piece else self.should_hide_pieces
        hide_moves = (
            self.edit_mode or self.should_hide_moves or
            (hide_piece and self.should_hide_moves is not False)
        )
        if selected_square:
            if hide_moves and hovered_square:
                move = Move(
                    pos_from=selected_square,
                    pos_to=hovered_square,
                    piece=piece,
                    is_edit=int(self.edit_mode),
                )
                self.set_caption(f"[Ply {self.ply_count}] {move}")
                return
            move = None
            if not hide_moves and hovered_square:
                move = self.find_move(selected_square, hovered_square)
            if move:
                move = deepcopy(move)
                if move.promotion is not None:
                    move.promotion = Unset
                chained_move = self.chain_start
                poss = []
                while chained_move:
                    poss.extend((chained_move.pos_from, chained_move.pos_to))
                    chained_move = chained_move.chained_move
                chained_move = move
                while chained_move and chained_move.chained_move and (
                    issubclass(chained_move.movement_type, movement.CastlingMovement)
                    and chained_move.chained_move.pos_from != move.pos_to
                    or isinstance(chained_move.piece.movement, movement.RangedAutoCaptureRiderMovement)
                ):
                    # let's also not show all auto-captures because space in the caption is VERY limited
                    if isinstance(chained_move.piece.movement, movement.RangedAutoCaptureRiderMovement):
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
                self.set_caption(f"[Ply {self.ply_count}] {'; '.join(str(move) for move in moves)}")
                return
        if piece or hovered_square:
            if not piece:
                piece = self.get_piece(hovered_square)
            if not piece.is_empty():
                self.set_caption(f"[Ply {self.ply_count}] {piece} on {toa(piece.board_pos)}")
                return
        if self.edit_mode:
            self.set_caption(f"[Ply {self.ply_count}] Editing board")
            return
        if self.game_over:
            if self.check_side:
                if self.use_check:
                    self.set_caption(f"[Ply {self.ply_count}] Checkmate! {self.check_side.opponent()} wins.")
                else:
                    self.set_caption(f"[Ply {self.ply_count}] King captured! {self.check_side.opponent()} wins.")
            else:
                if isinstance(self.stalemate_rule, dict):
                    rule = self.stalemate_rule.get(self.turn_side, 0)
                else:
                    rule = self.stalemate_rule
                if rule == 0:
                    self.set_caption(f"[Ply {self.ply_count}] Stalemate! It's a draw.")
                elif rule == 1:
                    self.set_caption(f"[Ply {self.ply_count}] Stalemate! {self.turn_side.opponent()} wins.")
                elif rule == -1:
                    self.set_caption(f"[Ply {self.ply_count}] Stalemate! {self.turn_side} wins.")
                else:
                    self.set_caption(f"[Ply {self.ply_count}] Stalemate! The result is undefined.")
        else:
            if self.check_side:
                self.set_caption(f"[Ply {self.ply_count}] {self.check_side} is in check!")
            else:
                if self.turn_pieces is not None:
                    turn_pieces = f" ({', '.join(sorted(piece.name for piece in self.turn_pieces))})"
                else:
                    turn_pieces = ''
                self.set_caption(f"[Ply {self.ply_count}] {self.turn_side} to move{turn_pieces}")

    def try_drop(self, move: Move) -> None:
        if self.turn_side not in self.drops:
            return
        if not self.captured_pieces[self.turn_side]:
            return
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
            return
        if not self.use_drops:
            return
        side_drops = self.drops[self.turn_side]
        drop_list = []
        drop_type_list = []
        drop_indexes = {k: i for i, k in enumerate(side_drops)}
        for piece_type in sorted(self.captured_pieces[self.turn_side], key=lambda x: drop_indexes.get(x, 0)):
            if piece_type not in side_drops:
                continue
            if self.turn_pieces is not None and piece_type not in self.turn_pieces:
                continue
            drop_squares = side_drops[piece_type]
            if move.piece.board_pos not in drop_squares:
                continue
            drop = drop_squares[move.piece.board_pos]
            drop_list.append(drop)
            drop_type_list.append(piece_type)
        if not drop_list:
            return
        self.start_promotion(self.get_piece(move.piece.board_pos), drop_list, drop_type_list)

    def try_promotion(self, move: Move) -> None:
        if move.piece.side not in self.promotions:
            return
        side_promotions = self.promotions[move.piece.side]
        if type(move.piece) not in side_promotions:
            return
        promotion_squares = side_promotions[type(move.piece)]
        if move.piece.board_pos not in promotion_squares:
            return
        promotions = promotion_squares[move.piece.board_pos]
        promotion_piece = self.promotion_piece
        if move.promotion:
            self.promotion_piece = True
            move.promotion.promoted_from = move.promotion.promoted_from or move.piece.promoted_from or type(move.piece)
            self.replace(move.piece, move.promotion)
            self.update_promotion_auto_captures(move)
            self.promotion_piece = promotion_piece
            return
        if len(promotions) == 1:
            self.promotion_piece = True
            promotion = promotions[0]
            if isinstance(promotion, Piece):
                promotion = promotion.of(promotion.side or move.piece.side).on(move.pos_to)
            else:
                promotion = promotion(board=self, pos=move.piece.board_pos, side=move.piece.side)
            promotion.promoted_from = promotion.promoted_from or move.piece.promoted_from or type(move.piece)
            move.set(promotion=promotion)
            self.replace(move.piece, move.promotion)
            self.update_promotion_auto_captures(move)
            self.promotion_piece = promotion_piece
            return
        self.start_promotion(move.piece, promotions)

    def start_promotion(
        self, piece: Piece, promotions: list[Piece | Type[Piece]], drops: list[Type[Piece]] | None = None
    ) -> None:
        if drops is None:
            drops = {}
        self.hide_moves()
        self.promotion_piece = piece
        piece_pos = piece.board_pos
        direction = (Side.WHITE if piece_pos[0] < self.board_height / 2 else Side.BLACK).direction
        area = len(promotions)
        area_height = min(len(promotions), max(self.board_height // 2, ceil(sqrt(area))))
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
        side = self.get_promotion_side(piece) if self.edit_mode else (piece.side or self.turn_side)
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
                promotion_piece.promoted_from = promotion_piece.promoted_from or piece.promoted_from or type(piece)
            if self.edit_mode and is_prefix_in(['custom', 'wall'], self.edit_piece_set_id):
                promotion_piece.reload(is_hidden=False, flipped_horizontally=False)
            elif issubclass(promotion, Royal) and promotion not in self.piece_sets[side]:
                if self.edit_mode and self.edit_piece_set_id is not None:
                    promotion_piece.is_hidden = False
                self.update_piece(promotion_piece, asset_folder='other')
            elif not self.edit_mode or self.edit_piece_set_id is None:
                self.update_piece(promotion_piece, penultima_flip=True)
            else:
                promotion_piece.reload(is_hidden=False, flipped_horizontally=False)
            promotion_piece.scale = self.square_size / promotion_piece.texture.width
            if isinstance(promotion_piece, Wall):
                promotion_piece.scale *= 0.8
            if not promotion_piece.is_empty() and not isinstance(promotion_piece, Obstacle):
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

    def apply_edit_promotion(self, move: Move) -> None:
        if move.is_edit and move.promotion is not None:
            if move.promotion is Unset:
                promotion_side = self.get_promotion_side(move.piece)
                if len(self.edit_promotions[promotion_side]):
                    self.start_promotion(move.piece, self.edit_promotions[promotion_side])
                    self.update_caption()
            else:
                self.promotion_piece = True
                self.replace(move.piece, move.promotion)
                self.update_auto_capture_markers(move)
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
        if not new_piece.is_empty() and not isinstance(new_piece, Obstacle):
            new_piece.set_color(
                self.color_scheme.get(
                    f"{new_piece.side.key()}piece_color",
                    self.color_scheme['piece_color']
                ),
                self.color_scheme['colored_pieces']
            )
        new_piece.scale = self.square_size / new_piece.texture.width
        self.piece_sprite_list.append(new_piece)
        if pos in self.en_passant_markers and not self.not_a_piece(pos):
            self.en_passant_markers.remove(pos)

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
            if self.check_side:
                self.color_pieces(
                    self.check_side,
                    self.color_scheme.get(
                        f"{self.check_side.key()}loss_color",
                        self.color_scheme['loss_color']
                    ),
                )
                self.color_pieces(
                    self.check_side.opponent(),
                    self.color_scheme.get(
                        f"{self.check_side.opponent().key()}win_color",
                        self.color_scheme['win_color']
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
                elif not sprite.is_empty():
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
            if piece.is_hidden is False:
                asset_folder = piece.asset_folder
            elif self.should_hide_pieces == 1:
                asset_folder = 'other'
            elif self.should_hide_pieces == 2 and type(piece) in penultima_pieces:
                asset_folder = 'other'
            else:
                asset_folder = piece.asset_folder
        if file_name is None:
            if piece.is_hidden is False:
                file_name = piece.file_name
            elif self.should_hide_pieces == 1:
                file_name = 'ghost'
            elif self.should_hide_pieces == 2 and type(piece) in penultima_pieces:
                file_name = penultima_pieces[type(piece)]
            else:
                file_name = piece.file_name
        if penultima_hide is not None:
            is_hidden = penultima_hide
        elif piece.is_hidden is False:
            is_hidden = False
        else:
            is_hidden = bool(self.should_hide_pieces) or Default
        file_name, flip = (file_name[:-1], penultima_flip) if file_name[-1] == '|' else (file_name, False)
        piece.reload(is_hidden=is_hidden, asset_folder=asset_folder, file_name=file_name, flipped_horizontally=flip)
        piece.scale = self.square_size / piece.texture.width

    def update_pieces(self) -> None:
        for piece in sum(self.movable_pieces.values(), []):
            self.update_piece(piece)
        for piece in self.promotion_piece_sprite_list:
            if isinstance(piece, Piece) and not piece.is_empty():
                if self.edit_mode and is_prefix_in(['custom', 'wall'], self.edit_piece_set_id):
                    piece.reload(is_hidden=False, flipped_horizontally=False)
                # that issubclass call is there because PyCharm doesn't recognize that piece is a Piece
                elif issubclass(type(piece), Royal) and type(piece) not in self.piece_sets[piece.side]:
                    self.update_piece(piece, asset_folder='other')
                elif not self.edit_mode or self.edit_piece_set_id is None:
                    self.update_piece(piece, penultima_flip=True)
                else:
                    piece.reload(is_hidden=False, flipped_horizontally=False)

    def update_sprite(
        self, sprite: Sprite, from_size: float, from_origin: tuple[float, float], from_flip_mode: bool
    ) -> None:
        old_position = sprite.position
        sprite.scale = self.square_size / sprite.texture.width
        sprite.position = self.get_screen_position(self.get_board_position(
            old_position, from_size, from_origin, from_flip_mode
        ))

    def update_sprites(self, flip_mode: bool) -> None:
        old_size = self.square_size
        self.square_size = min(self.width / (self.board_width + 2), self.height / (self.board_height + 2))
        old_origin = self.origin
        self.origin = self.width / 2, self.height / 2
        old_flip_mode = self.flip_mode
        self.flip_mode = flip_mode
        old_selected_square = self.selected_square
        self.update_sprite(self.highlight, old_size, old_origin, old_flip_mode)
        self.update_sprite(self.selection, old_size, old_origin, old_flip_mode)
        if self.active_piece is not None:
            self.update_sprite(self.active_piece, old_size, old_origin, old_flip_mode)
        for sprite_list in (
            self.board_sprite_list,
            self.move_sprite_list,
            self.piece_sprite_list,
            self.promotion_area_sprite_list,
            self.promotion_piece_sprite_list,
        ):
            for sprite in sprite_list:
                self.update_sprite(sprite, old_size, old_origin, old_flip_mode)
        for label in self.label_list:
            old_position = label.position
            label.font_size = self.square_size / 2
            label.x, label.y = self.get_screen_position(
                self.get_board_position(old_position, old_size, old_origin, old_flip_mode)
            )
        self.deselect_piece()
        self.select_piece(old_selected_square)
        if self.highlight_square:
            self.update_highlight(self.highlight_square)
            self.hovered_square = None
        else:
            self.update_highlight(self.get_board_position(self.highlight.position, old_size, old_origin, old_flip_mode))
        if self.skip_mouse_move == 2:
            self.skip_mouse_move = 1

    def flip_board(self) -> None:
        self.update_sprites(not self.flip_mode)

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
                    isinstance(sprite, Piece) and not sprite.is_empty()
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
                if isinstance(sprite, Piece) and not sprite.is_empty():
                    sprite.angle = 0

    def resize_board(self, width: int = 0, height: int = 0) -> None:
        width, height = width or self.board_width, height or self.board_height
        if self.game_loaded and self.board_width == width and self.board_height == height:
            return

        old_highlight = self.get_board_position(self.highlight.position) if self.highlight_square else None
        old_width, old_height = self.board_width, self.board_height
        self.board_width, self.board_height = width, height

        self.board_sprite_list.clear()
        self.label_list.clear()

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
            self.label_list.extend([
                Text(text, *self.get_screen_position((row, -1)), width=width, **label_kwargs),
                Text(text, *self.get_screen_position((row, self.board_width)), width=width, **label_kwargs)
            ])

        for col in range(self.board_width):
            text = b26(col + 1)
            width = round(self.square_size / 2 * len(text))
            self.label_list.extend([
                Text(text, *self.get_screen_position((-1, col)), width=width, **label_kwargs),
                Text(text, *self.get_screen_position((self.board_height, col)), width=width, **label_kwargs),
            ])

        for row, col in product(range(self.board_height), range(self.board_width)):
            sprite = Sprite("assets/util/square.png")
            sprite.color = self.color_scheme[f"{'light' if self.is_light_square((row, col)) else 'dark'}_square_color"]
            sprite.position = self.get_screen_position((row, col))
            sprite.scale = self.square_size / sprite.texture.width
            self.board_sprite_list.append(sprite)

        self.reset_drops()
        self.reset_promotions()

        for row in range(len(self.pieces), self.board_height):
            self.pieces += [[]]
        for row in range(self.board_height):
            for col in range(len(self.pieces[row]), self.board_width):
                self.pieces[row].append(NoPiece(self, pos=(row, col)))
            self.pieces[row] = self.pieces[row][:self.board_width]
        self.pieces = self.pieces[:self.board_height]

        if self.game_loaded or self.board_width != board_width or self.board_height != board_height:
            self.log(f"[Ply {self.ply_count}] Info: Changed board size to {self.board_width}x{self.board_height}")
            self.resize(
                self.width + self.square_size * (self.board_width - old_width),
                self.height + self.square_size * (self.board_height - old_height)
            )
            self.update_highlight(old_highlight)

    def resize(self, width: float, height: float) -> None:
        if self.fullscreen:
            return
        if width == self.width and height == self.height:
            return
        self.skip_mouse_move = 2
        old_width, old_height = self.width, self.height
        x, y = self.get_location()
        min_width, min_height = (self.board_width + 2) * min_size, (self.board_height + 2) * min_size
        self.set_visible(False)
        self.set_size(round(max(width, min_width)), round(max(height, min_height)))
        self.log(f"[Ply {self.ply_count}] Info: Resized to {self.width}x{self.height}", False)
        self.set_location(x - (self.width - old_width) // 2, y - (self.height - old_height) // 2)
        if not self.fullscreen:
            self.windowed_size = self.width, self.height
            self.windowed_square_size = min(self.width / (self.board_width + 2), self.height / (self.board_height + 2))
        self.set_visible(True)

    def toggle_fullscreen(self) -> None:
        if self.fullscreen:
            self.log(f"[Ply {self.ply_count}] Info: Fullscreen disabled", False)
            self.set_fullscreen(False)
            return
        screens = get_screens()
        if len(screens) == 1:
            self.log(f"[Ply {self.ply_count}] Info: Fullscreen enabled", False)
            self.set_fullscreen()
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
        self.log(f"[Ply {self.ply_count}] Info: Fullscreen enabled on screen {screen + 1}", False)
        self.set_fullscreen(screen=screens[screen])

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
        if self.active_piece:
            self.active_piece.draw()
        self.promotion_area_sprite_list.draw()
        self.promotion_piece_sprite_list.draw()
        if self.promotion_area:
            self.highlight.draw()

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
        self.update_sprites(self.flip_mode)

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
                    if pos in self.promotion_area_drops and (drop := self.promotion_area_drops[pos]) is not None:
                        self.move_history[-1].set(placed_piece=drop)
                        for i, piece in enumerate(self.captured_pieces[self.turn_side][::-1]):
                            if piece == drop:
                                self.captured_pieces[self.turn_side].pop(-(i + 1))
                                break
                    self.move_history[-1].set(promotion=self.promotion_area[pos])
                    self.replace(self.promotion_piece, self.promotion_area[pos])
                    self.update_auto_capture_markers(self.move_history[-1])
                    self.update_promotion_auto_captures(self.move_history[-1])
                    self.end_promotion()
                    chained_move = self.move_history[-1]
                    while chained_move:
                        move_type = (
                            'Edit' if chained_move.is_edit
                            else 'Drop' if chained_move.movement_type == movement.DropMovement
                            else 'Move'
                        )
                        self.log(f"[Ply {self.ply_count}] {move_type}: {chained_move}")
                        chained_move = chained_move.chained_move
                        if chained_move:
                            chained_move.piece.move(chained_move)
                            self.update_auto_capture_markers(chained_move)
                            chained_move.set(piece=copy(chained_move.piece))
                    self.ply_count += not self.move_history[-1].is_edit
                    self.compare_history()
                    self.advance_turn()
                return
            if pos == self.selected_square:
                if self.find_move(pos, pos) is None:
                    self.deselect_piece()
                    return
            if self.selected_square is not None:
                if self.edit_mode:
                    self.square_was_clicked = True
                    self.clicked_square = pos
                    return
                if pos not in self.moves.get(self.turn_side, {}).get(self.selected_square, {}):
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
            self.deselect_piece()
            if self.promotion_piece and (self.edit_mode or not self.promotion_piece.is_empty()):
                self.undo_last_finished_move()
                self.update_caption()
                return
            if self.edit_mode:
                pos = self.get_board_position((x, y))
                if self.not_on_board(pos):
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
            if self.promotion_piece:
                return
            pos = self.get_board_position((x, y))
            if self.not_on_board(pos):
                return
            next_selected_square = None
            move = Move(is_edit=1)
            if held_buttons & MOUSE_BUTTON_LEFT:
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
                if self.clicked_square != pos:
                    self.deselect_piece()
                    return
                if modifiers & key.MOD_ALT:
                    move.set(pos_from=pos, pos_to=pos, piece=self.get_piece(pos), is_edit=2)
                    if move.piece.is_empty():
                        move.set(pos_from=None, movement_type=movement.DropMovement, promotion=Unset)
                    else:
                        side = self.get_promotion_side(move.piece)
                        if len(self.edit_promotions[side]) == 1:
                            piece = self.edit_promotions[side][0]
                            if isinstance(piece, Piece):
                                piece = piece.of(piece.side or side).on(pos)
                            else:
                                p = piece(board=self, pos=move.pos_to, side=side)
                                p.promoted_from = p.promoted_from or ((mp := move.piece).promoted_from or type(mp))
                                piece = p
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
                    if move.piece.is_empty():
                        move.set(pos_from=None)
                    side = self.get_promotion_side(move.piece)
                    if len(self.edit_promotions[side]) == 1:
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
            move.piece.move(move)
            self.update_auto_capture_markers(move)
            self.move_history.append(deepcopy(move))
            self.apply_edit_promotion(move)
            if not self.promotion_piece:
                self.log(f"[Ply {self.ply_count}] Edit: {self.move_history[-1]}")
                self.compare_history()
            self.advance_turn()
            if next_selected_square:
                self.select_piece(next_selected_square)
            return
        if held_buttons & MOUSE_BUTTON_RIGHT:
            if not self.drops:
                self.deselect_piece()
                return
            if self.game_over:
                self.deselect_piece()
                return
            if self.promotion_piece:
                if not self.edit_mode and self.promotion_piece.is_empty():
                    self.undo_last_finished_move()
                    self.update_caption()
                if not modifiers & key.MOD_SHIFT:
                    return
            pos = self.get_board_position((x, y))
            if not self.not_on_board(pos) and (piece := self.get_piece(pos)).is_empty():
                move = Move(pos_from=pos, pos_to=pos, movement_type=movement.DropMovement, piece=piece, promotion=Unset)
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
                    issubclass(chained_move.movement_type, movement.CastlingMovement)
                    and chained_move.chained_move.pos_from != move.pos_to
                    or isinstance(chained_move.piece.movement, movement.RangedAutoCaptureRiderMovement)
                ):
                    poss.extend((chained_move.pos_from, chained_move.pos_to))
                    chained_move = chained_move.chained_move
                poss.extend((chained_move.pos_from, chained_move.pos_to))
                if chained_move.chained_move or self.chain_moves.get(self.turn_side, {}).get(tuple(poss)):
                    chained_move.chained_move = Unset  # do not chain moves since we are selecting chained move manually
                    is_final = False
                else:
                    is_final = True
                self.update_auto_capture_markers(move)
                self.update_auto_captures(move, self.turn_side.opponent())
                chained_move = move
                while chained_move:
                    chained_move.piece.move(chained_move)
                    self.update_auto_capture_markers(chained_move)
                    chained_move.set(piece=copy(chained_move.piece))
                    if self.promotion_piece is None:
                        self.log(f"[Ply {self.ply_count}] Move: {chained_move}")
                    chained_move = chained_move.chained_move
                if self.chain_start is None:
                    self.chain_start = deepcopy(move)
                    self.move_history.append(self.chain_start)
                else:
                    last_move = self.chain_start
                    while last_move.chained_move:
                        last_move = last_move.chained_move
                    last_move.chained_move = deepcopy(move)
                if not is_final and not self.promotion_piece:
                    self.load_moves()
                    self.select_piece(move.pos_to)
                else:
                    self.chain_start = None
                    if self.promotion_piece is None:
                        self.ply_count += 1
                        self.compare_history()
                    self.advance_turn()
            else:
                self.reset_position(self.get_piece(self.selected_square))
                if not self.square_was_clicked:
                    self.deselect_piece()

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if not self.is_active:
            return
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
                self.log(f"[Ply {self.ply_count}] Info: Custom layout saved")
            elif modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:  # Save
                save_path = get_filename('save', 'json')
                self.save(save_path)
            elif modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Save as
                self.deactivate()
                self.draw(0)
                self.log(f"[Ply {self.ply_count}] Info: Selecting a file to save to", False)
                save_path = select_save_name()
                if save_path:
                    self.save(save_path)
                else:
                    self.log(f"[Ply {self.ply_count}] Info: Save cancelled", False)
                self.activate()
        if symbol == key.R:  # Restart
            if modifiers & key.MOD_ALT:  # Reload save data
                data = self.save_data if modifiers & key.MOD_SHIFT else self.load_data
                if data is not None:
                    whence = 'saved to' if modifiers & key.MOD_SHIFT else 'loaded from'
                    path = self.save_path if modifiers & key.MOD_SHIFT else self.load_path
                    state = '' if isfile(path) else '(deleted) '
                    self.log(f"[Ply {self.ply_count}] Info: Reloading data {whence} {state}{path}")
                    self.load_board(data)
            elif modifiers & key.MOD_SHIFT:  # Randomize piece sets
                blocked_ids = set(self.board_config['block_ids'])
                set_id_list = list(i for i in range(len(piece_groups)) if i not in blocked_ids)
                if modifiers & key.MOD_ACCEL:  # Randomize piece sets (same for both sides)
                    self.log(
                        f"[Ply {self.ply_count}] Info: Starting new game (with a random piece set)",
                        bool(self.should_hide_pieces)
                    )
                    chosen_id = self.set_rng.sample(set_id_list, k=1)[0]
                    self.piece_set_ids = {side: chosen_id for side in self.piece_set_ids}
                else:  # Randomize piece sets (different for each side)
                    self.log(
                        f"[Ply {self.ply_count}] Info: Starting new game (with random piece sets)",
                        bool(self.should_hide_pieces)
                    )
                    chosen_ids = self.set_rng.sample(set_id_list, k=len(self.piece_set_ids))
                    self.piece_set_ids = {side: set_id for side, set_id in zip(self.piece_set_ids, chosen_ids)}
                self.chaos_mode = 0
                self.reset_custom_data()
                self.reset_board()
            elif modifiers & key.MOD_ACCEL:  # Restart with the same piece sets
                self.log(f"[Ply {self.ply_count}] Info: Starting new game", bool(self.should_hide_pieces))
                self.reset_board(update=None)  # Clear redoing if and only if no moves were made yet, i.e. double Ctrl+R
        if symbol == key.C:
            if modifiers & (key.MOD_SHIFT | key.MOD_ALT):  # Chaos mode
                self.load_chaos_sets(1 + bool(modifiers & key.MOD_ALT), modifiers & key.MOD_ACCEL)
            elif modifiers & key.MOD_ACCEL:  # Config
                self.save_config()
                self.log(f"[Ply {self.ply_count}] Info: Configuration saved", False)
        if symbol == key.X:
            if modifiers & (key.MOD_SHIFT | key.MOD_ALT):  # Extreme chaos mode
                self.load_chaos_sets(3 + bool(modifiers & key.MOD_ALT), modifiers & key.MOD_ACCEL)
            elif modifiers & key.MOD_ACCEL:  # Extra roll (update probabilistic pieces)
                if self.selected_square:  # Only update selected piece (if it is probabilistic)
                    piece = self.get_piece(self.selected_square)
                    if isinstance(piece.movement, movement.ProbabilisticMovement):
                        del self.roll_history[self.ply_count - 1][piece.board_pos]
                        self.probabilistic_piece_history[self.ply_count - 1].discard((piece.board_pos, type(piece)))
                        self.log(f"[Ply {self.ply_count}] Info: Probabilistic piece on {toa(piece.board_pos)} updated")
                        self.advance_turn()
                else:  # Update all probabilistic pieces
                    self.clear_future_history(self.ply_count - 1)
                    self.log(f"[Ply {self.ply_count}] Info: Probabilistic pieces updated")
                    self.advance_turn()
        if symbol == key.F11:  # Full screen (toggle)
            self.toggle_fullscreen()
        if symbol == key.MINUS and not self.fullscreen:  # (-) Decrease window size
            if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:
                self.resize((self.board_width + 2) * min_size, (self.board_height + 2) * min_size)
            elif modifiers & key.MOD_ACCEL:
                width, height = self.get_size()
                self.resize(
                    width - (self.board_width + 2) * size_step,
                    height - (self.board_height + 2) * size_step
                )
            elif modifiers & key.MOD_SHIFT:
                width, height = self.get_size()
                size = min(round(width / (self.board_width + 2)), round(height / (self.board_height + 2)))
                self.resize((self.board_width + 2) * size, (self.board_height + 2) * size)
        if symbol == key.EQUAL and not self.fullscreen:  # (+) Increase window size
            if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:
                self.resize((self.board_width + 2) * max_size, (self.board_height + 2) * max_size)
            elif modifiers & key.MOD_ACCEL:
                width, height = self.get_size()
                self.resize(
                    width + (self.board_width + 2) * size_step,
                    height + (self.board_height + 2) * size_step
                )
            elif modifiers & key.MOD_SHIFT:
                width, height = self.get_size()
                size = max(round(width / (self.board_width + 2)), round(height / (self.board_height + 2)))
                self.resize((self.board_width + 2) * size, (self.board_height + 2) * size)
        if symbol == key.KEY_0 and modifiers & key.MOD_ACCEL:  # Reset window size
            self.set_fullscreen(False)
            self.resize((self.board_width + 2) * default_size, (self.board_height + 2) * default_size)
        if symbol == key.E:
            if modifiers & key.MOD_SHIFT:  # Empty board
                self.empty_board()
            if modifiers & key.MOD_ACCEL:  # Edit mode (toggle)
                self.edit_mode = not self.edit_mode
                self.log(f"[Ply {self.ply_count}] Mode: {'EDIT' if self.edit_mode else 'PLAY'}", False)
                self.deselect_piece()
                self.hide_moves()
                self.advance_turn()
                if self.edit_mode:
                    self.moves = {side: {} for side in self.moves}
                    self.chain_moves = {side: {} for side in self.chain_moves}
                    self.theoretical_moves = {side: {} for side in self.theoretical_moves}
                    self.show_moves()
        if symbol == key.W:  # White
            if modifiers & key.MOD_ALT:  # Reset white set to default
                self.piece_set_ids[Side.WHITE] = 0
                set_name_suffix = ''
                if not self.should_hide_pieces:
                    set_name = piece_groups[self.piece_set_ids[Side.WHITE]].get('name')
                    set_name_suffix = f" ({set_name})"
                self.log(
                    f"[Ply {self.ply_count}] Info: Using default piece set for White{set_name_suffix}",
                    bool(self.should_hide_pieces)
                )
                self.reset_custom_data()
                self.reset_board()
            elif modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:  # White is in control
                while self.turn_side != Side.WHITE and not self.chain_start:
                    self.move_history.append(None)
                    turn_side = self.turn_order[self.ply_count % len(self.turn_order)]
                    if isinstance(turn_side, list):
                        turn_pieces = f" ({', '.join(sorted(piece.name for piece in turn_side[1]))})"
                        turn_side = turn_side[0]
                    else:
                        turn_pieces = ''
                    self.log(f"[Ply {self.ply_count}] Pass: {turn_side} to move{turn_pieces}")
                    self.ply_count += 1
                    self.clear_en_passant()
                    self.clear_castling_ep()
                    self.compare_history()
                    self.advance_turn()
            elif modifiers & key.MOD_SHIFT:  # Shift white piece set
                d = -1 if modifiers & key.MOD_ACCEL else 1
                self.piece_set_ids[Side.WHITE] = (
                    (self.piece_set_ids[Side.WHITE] + len(self.chaos_sets) + d)
                    % (len(piece_groups) + len(self.chaos_sets))
                    - len(self.chaos_sets)
                ) if self.piece_set_ids[Side.WHITE] is not None else 0
                which = {-1: 'previous', 1: 'next'}[d]
                set_name_suffix = ''
                if not self.should_hide_pieces:
                    if self.piece_set_ids[Side.WHITE] < 0:
                        set_name = get_set_name(self.chaos_sets[-self.piece_set_ids[Side.WHITE]])
                    else:
                        set_name = piece_groups[self.piece_set_ids[Side.WHITE]].get('name')
                    set_name_suffix = f" ({set_name})"
                self.log(
                    f"[Ply {self.ply_count}] Info: Using {which} piece set for White{set_name_suffix}",
                    bool(self.should_hide_pieces)
                )
                self.reset_custom_data()
                self.reset_board()
        if symbol == key.B:  # Black
            if modifiers & key.MOD_ALT:  # Reset black set to default
                self.piece_set_ids[Side.BLACK] = 0
                set_name_suffix = ''
                if not self.should_hide_pieces:
                    set_name = piece_groups[self.piece_set_ids[Side.BLACK]].get('name')
                    set_name_suffix = f" ({set_name})"
                self.log(
                    f"[Ply {self.ply_count}] Info: Using default piece set for Black{set_name_suffix}",
                    bool(self.should_hide_pieces)
                )
                self.reset_custom_data()
                self.reset_board()
            elif modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:  # Black is in control
                while self.turn_side != Side.BLACK and not self.chain_start:
                    self.move_history.append(None)
                    turn_side = self.turn_order[self.ply_count % len(self.turn_order)]
                    if isinstance(turn_side, list):
                        turn_pieces = f" ({', '.join(sorted(piece.name for piece in turn_side[1]))})"
                        turn_side = turn_side[0]
                    else:
                        turn_pieces = ''
                    self.log(f"[Ply {self.ply_count}] Pass: {turn_side} to move{turn_pieces}")
                    self.ply_count += 1
                    self.clear_en_passant()
                    self.clear_castling_ep()
                    self.compare_history()
                    self.advance_turn()
            elif modifiers & key.MOD_SHIFT:  # Shift black piece set
                d = -1 if modifiers & key.MOD_ACCEL else 1
                self.piece_set_ids[Side.BLACK] = (
                    (self.piece_set_ids[Side.BLACK] + len(self.chaos_sets) + d)
                    % (len(piece_groups) + len(self.chaos_sets))
                    - len(self.chaos_sets)
                ) if self.piece_set_ids[Side.BLACK] is not None else 0
                which = {-1: 'previous', 1: 'next'}[d]
                set_name_suffix = ''
                if not self.should_hide_pieces:
                    if self.piece_set_ids[Side.BLACK] < 0:
                        set_name = get_set_name(self.chaos_sets[-self.piece_set_ids[Side.BLACK]])
                    else:
                        set_name = piece_groups[self.piece_set_ids[Side.BLACK]].get('name')
                    set_name_suffix = f" ({set_name})"
                self.log(
                    f"[Ply {self.ply_count}] Info: Using {which} piece set for Black{set_name_suffix}",
                    bool(self.should_hide_pieces)
                )
                self.reset_custom_data()
                self.reset_board()
        if symbol == key.N:  # Next
            if modifiers & key.MOD_ALT:  # Reset white and black sets to default
                self.chaos_mode = 0
                self.piece_set_ids = {side: 0 for side in self.piece_set_ids}
                set_name_suffix = ''
                if not self.should_hide_pieces:
                    set_name = piece_groups[self.piece_set_ids[Side.WHITE]].get('name')
                    set_name_suffix = f" ({set_name})"
                self.log(
                    f"[Ply {self.ply_count}] Info: Using default piece set{set_name_suffix}",
                    bool(self.should_hide_pieces)
                )
                self.reset_custom_data()
                self.reset_board()
            elif modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT and not self.chain_start:  # Next player
                self.move_history.append(None)
                turn_side = self.turn_order[self.ply_count % len(self.turn_order)]
                if isinstance(turn_side, list):
                    turn_pieces = f" ({', '.join(sorted(piece.name for piece in turn_side[1]))})"
                    turn_side = turn_side[0]
                else:
                    turn_pieces = ''
                self.log(f"[Ply {self.ply_count}] Pass: {turn_side} to move{turn_pieces}")
                self.ply_count += 1
                self.clear_en_passant()
                self.clear_castling_ep()
                self.compare_history()
                self.advance_turn()
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
                    if not self.should_hide_pieces:
                        if self.piece_set_ids[Side.WHITE] < 0:
                            set_name = get_set_name(self.chaos_sets[-self.piece_set_ids[Side.WHITE]])
                        else:
                            set_name = piece_groups[self.piece_set_ids[Side.WHITE]].get('name')
                        set_name_suffix = f" ({set_name})"
                    self.log(
                        f"[Ply {self.ply_count}] Info: Using {which} piece set{set_name_suffix}",
                        bool(self.should_hide_pieces)
                    )
                else:  # Next player goes first
                    for data in (self.piece_sets, self.piece_set_ids, self.piece_set_names):
                        data[Side.WHITE], data[Side.BLACK] = data[Side.BLACK], data[Side.WHITE]
                    set_name_suffix = ''
                    if not self.should_hide_pieces:
                        set_names = [self.piece_set_names[side] for side in (Side.WHITE, Side.BLACK)]
                        set_name_suffix = f" ({' vs. '.join(set_names)})"
                    self.log(
                        f"[Ply {self.ply_count}] Info: Swapping piece sets{set_name_suffix}",
                        bool(self.should_hide_pieces)
                    )
                self.reset_custom_data()
                self.reset_board()
        if symbol == key.P:  # Promotion
            if self.edit_mode:
                old_id = self.edit_piece_set_id
                if modifiers & key.MOD_ALT:  # Promote to custom pieces
                    self.edit_piece_set_id = 'wall' if modifiers & key.MOD_SHIFT else 'custom'
                    which = {'custom': 'custom', 'wall': 'obstacle'}[self.edit_piece_set_id]
                    self.log(f"[Ply {self.ply_count}] Info: Placing {which} pieces", False)
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
                    self.log(f"[Ply {self.ply_count}] Info: Placing from {which} piece set{set_name_suffix}", False)
                elif modifiers & key.MOD_ACCEL:  # Reset promotion piece set
                    self.edit_piece_set_id = None
                    set_names = [self.piece_set_names[side] for side in (Side.WHITE, Side.BLACK)]
                    set_names = list(dict.fromkeys(set_names))
                    set_name_suffix = f"{'s' * (len(set_names) > 1)}"
                    if not self.should_hide_pieces:
                        set_name_suffix += f" ({' vs. '.join(set_names)})"
                    self.log(f"[Ply {self.ply_count}] Info: Placing from current piece set{set_name_suffix}", False)
                if old_id != self.edit_piece_set_id:
                    self.reset_edit_promotions()
                    if self.promotion_piece:
                        promotion_piece = self.promotion_piece
                        promotion_side = self.get_promotion_side(promotion_piece)
                        self.end_promotion()
                        if len(self.edit_promotions[promotion_side]):
                            self.start_promotion(promotion_piece, self.edit_promotions[promotion_side])
                            self.update_caption()
        if symbol == key.O:  # Royal pieces
            old_mode = self.royal_piece_mode
            old_check = self.use_check
            if modifiers & key.MOD_ALT:  # Toggle checks
                self.use_check = not self.use_check
            elif modifiers & key.MOD_SHIFT:  # Force royal mode (Shift: all quasi-royal, Ctrl+Shift: all royal)
                self.royal_piece_mode = 1 if modifiers & key.MOD_ACCEL else 2
            elif modifiers & key.MOD_ACCEL:  # Default royal mode (depends on piece superclass)
                self.royal_piece_mode = 0
            if old_mode != self.royal_piece_mode:
                if self.royal_piece_mode == 0:
                    self.log(f"[Ply {self.ply_count}] Info: Using default check rule (piece-dependent)")
                elif self.royal_piece_mode == 1:
                    self.log(f"[Ply {self.ply_count}] Info: Using royal check rule (threaten any royal piece)")
                elif self.royal_piece_mode == 2:
                    self.log(f"[Ply {self.ply_count}] Info: Using quasi-royal check rule (threaten last royal piece)")
                else:
                    self.royal_piece_mode = old_mode
            if old_check != self.use_check:
                if self.use_check:
                    self.log(f"[Ply {self.ply_count}] Info: Checks enabled (checkmate the royal piece to win)")
                else:
                    self.log(f"[Ply {self.ply_count}] Info: Checks disabled (capture the royal piece to win)")
            if old_mode != self.royal_piece_mode or old_check != self.use_check:
                self.future_move_history = []  # we don't know if we can redo the future moves anymore, so we clear them
                self.advance_turn()
        if symbol == key.F:
            if modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:  # Flip board
                self.flip_board()
                self.log(f"[Ply {self.ply_count}] Info: Board flipped", False)
            if not modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Fast-forward
                if self.future_move_history:
                    self.log(f"[Ply {self.ply_count}] Info: Fast-forwarding", False)
                while self.future_move_history:
                    self.redo_last_move()
            if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Fast-forward, but slowly. (Reload history)
                self.log(f"[Ply {self.ply_count}] Info: Reloading history", False)
                self.log(f"[Ply {self.ply_count}] Info: Starting new game", bool(self.should_hide_pieces))
                self.reload_history()
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
                self.log(f"[Ply {self.ply_count}] Info: Using {which} color scheme (ID {self.color_index})", False)
                self.color_scheme = colors[self.color_index]
                self.update_colors()
        if symbol == key.H:
            old_should_hide_pieces = self.should_hide_pieces
            old_drops = self.use_drops
            if modifiers & key.MOD_ALT:  # Toggle drops (Crazyhouse mode)
                self.use_drops = not self.use_drops
            elif modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Show
                self.should_hide_pieces = 0
            elif modifiers & key.MOD_SHIFT:  # Hide
                self.should_hide_pieces = 1
            elif modifiers & key.MOD_ACCEL:  # Penultima mode
                self.should_hide_pieces = 2
            if old_should_hide_pieces != self.should_hide_pieces:
                if self.should_hide_pieces == 0:
                    self.log(
                        f"[Ply {self.ply_count}] Info: Pieces revealed: "
                        f"{self.piece_set_names[Side.WHITE]} vs. "
                        f"{self.piece_set_names[Side.BLACK]}"
                    )
                elif self.should_hide_pieces == 1:
                    self.log(f"[Ply {self.ply_count}] Info: Pieces hidden")
                elif self.should_hide_pieces == 2:
                    self.log(f"[Ply {self.ply_count}] Info: Penultima mode activated!")
                else:
                    self.should_hide_pieces = old_should_hide_pieces
                self.update_pieces()
                self.show_moves()
            if old_drops != self.use_drops:
                if self.use_drops:
                    self.log(f"[Ply {self.ply_count}] Info: Drops enabled")
                else:
                    self.log(f"[Ply {self.ply_count}] Info: Drops disabled")
                if old_drops and not self.edit_mode and self.promotion_piece and self.promotion_piece.is_empty():
                    self.undo_last_finished_move()
                    self.update_caption()
        if symbol == key.M:  # Moves
            if modifiers & key.MOD_ALT:  # Clear future move history
                self.log(f"[Ply {self.ply_count}] Info: Future move history cleared", False)
                if self.future_move_history:
                    self.future_move_history = []
                else:
                    self.clear_future_history(self.ply_count - 1)
                    self.log(f"[Ply {self.ply_count}] Info: Probabilistic pieces updated")
                    self.advance_turn()
            else:
                old_should_hide_moves = self.should_hide_moves
                if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Default
                    self.should_hide_moves = None
                elif modifiers & key.MOD_SHIFT:  # Hide
                    self.should_hide_moves = True
                elif modifiers & key.MOD_ACCEL:  # Show
                    self.should_hide_moves = False
                if old_should_hide_moves != self.should_hide_moves:
                    if self.should_hide_moves is None:
                        self.log(f"[Ply {self.ply_count}] Info: Move markers default to piece visibility", False)
                    elif self.should_hide_moves is False:
                        self.log(f"[Ply {self.ply_count}] Info: Move markers default to shown", False)
                    elif self.should_hide_moves is True:
                        self.log(f"[Ply {self.ply_count}] Info: Move markers default to hidden", False)
                    else:
                        self.should_hide_moves = old_should_hide_moves
                    self.update_pieces()
                    self.show_moves()
        if symbol == key.K and not self.should_hide_moves:  # Move markers
            selected_square = self.selected_square
            if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Default
                self.log(f"[Ply {self.ply_count}] Info: Showing legal moves for moving player", False)
                self.load_moves(False)
            elif modifiers & key.MOD_ACCEL:  # Valid moves
                self.log(f"[Ply {self.ply_count}] Info: Showing legal moves for both players", False)
                self.load_moves(False, Side.ANY, Side.NONE)
            elif modifiers & key.MOD_SHIFT:  # Theoretical moves
                self.log(f"[Ply {self.ply_count}] Info: Showing all possible moves for both players", False)
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
        if symbol == key.Y and modifiers & key.MOD_ACCEL:  # Redo
            self.redo_last_finished_move()
        if symbol == key.L:
            if modifiers & key.MOD_ALT:  # Load save data
                self.deactivate()
                self.draw(0)
                self.log(f"[Ply {self.ply_count}] Info: Selecting a file to load from", False)
                load_path = select_save_data()
                if load_path:
                    self.load(load_path, with_history=modifiers & key.MOD_SHIFT)
                else:
                    self.log(f"[Ply {self.ply_count}] Info: Load cancelled", False)
                self.activate()
            else:  # Log
                if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Toggle verbose
                    self.verbose = not self.verbose
                    self.log(f"[Ply {self.ply_count}] Info: Verbose output: {'ON' if self.verbose else 'OFF'}", False)
                elif modifiers & key.MOD_ACCEL:  # Save log
                    self.save_log()
                    self.log(f"[Ply {self.ply_count}] Info: Log file saved", False)
                elif modifiers & key.MOD_SHIFT:  # Save verbose log
                    self.save_log(self.verbose_data, 'verbose')
                    self.log(f"[Ply {self.ply_count}] Info: Verbose log file saved", False)
        if symbol == key.D:  # Debug
            if modifiers & key.MOD_ACCEL:  # Save debug log
                self.log(f"[Ply {self.ply_count}] Info: Saving debug information", False)
                debug_log_data = self.debug_info()
                self.save_log(debug_log_data, 'debug')
                self.log(f"[Ply {self.ply_count}] Info: Debug information saved", False)
            if modifiers & key.MOD_SHIFT:  # Print debug log
                self.log(f"[Ply {self.ply_count}] Info: Printing debug information", False)
                debug_log_data = self.debug_info()
                for string in debug_log_data:
                    print(f"[Debug] {string}")
                self.log(f"[Ply {self.ply_count}] Info: Debug information printed", False)
            if modifiers & key.MOD_ALT:  # Save debug listings
                self.log(f"[Ply {self.ply_count}] Info: Saving debug listings", False)
                save_piece_data(self)
                save_piece_sets()
                save_piece_types()
                self.log(f"[Ply {self.ply_count}] Info: Debug listings saved", False)
        if symbol == key.SLASH:  # (?) Random
            if self.edit_mode:
                return
            moves = self.unique_moves()[self.turn_side]
            if modifiers & key.MOD_SHIFT:  # Random piece
                self.deselect_piece()
                if moves:
                    self.log(f"[Ply {self.ply_count}] Info: Selecting a random piece", False)
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
                    self.log(f"[Ply {self.ply_count}] Info: Making a random move{suffix}", False)
                    move = base_rng.choice(choices)
                    self.update_auto_capture_markers(move)
                    self.update_auto_captures(move, self.turn_side.opponent())
                    chained_move = move
                    while chained_move:
                        chained_move.piece.move(chained_move)
                        self.update_auto_capture_markers(chained_move)
                        chained_move.set(piece=copy(chained_move.piece))
                        if self.promotion_piece is None:
                            self.log(f"[Ply {self.ply_count}] Move: {chained_move}")
                        chained_move = chained_move.chained_move
                    if self.chain_start is None:
                        self.chain_start = move
                        self.move_history.append(deepcopy(self.chain_start))
                    else:
                        last_move = self.chain_start
                        while last_move.chained_move:
                            last_move = last_move.chained_move
                        last_move.chained_move = move
                    if move.chained_move is Unset and not self.promotion_piece:
                        self.load_moves()
                        self.select_piece(move.pos_to)
                    else:
                        self.chain_start = None
                        if self.promotion_piece is None:
                            self.ply_count += 1
                            self.compare_history()
                        self.advance_turn()

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
            self.log(f"[Ply {self.ply_count}] Info: Loading from {path}")
            with open(save_path, mode='r', encoding='utf-8') as file:
                save_data = file.read()
            self.load_board(save_data, with_history=update_mode & 1 if should_update else with_history)
            if self.load_data == save_data:
                self.load_path = save_path
                if should_update:
                    self.save(save_path)
        except Exception:
            self.log(f"[Ply {self.ply_count}] Error: Failed to load from {path}")
            print_exc()

    def save(self, path: str | None, auto: bool = False) -> None:
        if not path:
            return
        data = self.dump_board(self.board_config[f"partial_{'auto' * auto}save"])  # completely unnecessary but whatever
        if auto and data == self.save_data:
            return
        makedirs(dirname(path), exist_ok=True)
        with open(path, mode='w', encoding='utf-8') as file:
            file.write(data)
        self.save_data = data
        self.save_path = path
        saved = 'Auto-saved' if auto else 'Saved'
        self.log(f"[Ply {self.ply_count}] Info: {saved} to {path}", False)

    def auto_save(self) -> None:
        self.save(get_filename('autosave', 'json', in_dir=join(base_dir, 'auto')), auto=True)

    def log(self, string: str, important: bool = True) -> None:
        self.verbose_data.append(string)
        if important:
            self.log_data.append(string)
        if important or self.verbose:
            print(string)

    def log_armies(self):
        if self.custom_layout:
            self.log(f"[Ply {self.ply_count}] Game: Custom")
            return
        self.log(
            f"[Ply {self.ply_count}] Game: "
            f"{self.piece_set_names[Side.WHITE] if not self.should_hide_pieces else '???'} vs. "
            f"{self.piece_set_names[Side.BLACK] if not self.should_hide_pieces else '???'}"
        )

    def log_special_modes(self):
        if self.should_hide_pieces == 1:
            self.log(f"[Ply {self.ply_count}] Info: Pieces hidden")
        if self.should_hide_pieces == 2:
            self.log(f"[Ply {self.ply_count}] Info: Penultima mode activated!")
        if self.royal_piece_mode == 1:
            self.log(f"[Ply {self.ply_count}] Info: Using royal check rule (threaten any royal piece)")
        if self.royal_piece_mode == 2:
            self.log(f"[Ply {self.ply_count}] Info: Using quasi-royal check rule (threaten last royal piece)")
        if not self.use_check:
            self.log(f"[Ply {self.ply_count}] Info: Checks disabled (capture the royal piece to win)")

    def save_log(self, log_data: list[str] | None = None, log_name: str = 'log') -> None:
        if not log_data:
            log_data = self.log_data
        if log_data:
            with open(get_filename(log_name, 'txt'), mode='w', encoding='utf-8') as log_file:
                log_file.write('\n'.join(log_data))

    def clear_log(self, console: bool = True, log: bool = True, verbose: bool = True) -> None:
        self.log(f"[Ply {self.ply_count}] Info: Log cleared", False)
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
        config['hide_pieces'] = self.should_hide_pieces
        config['hide_moves'] = self.should_hide_moves
        config['use_drops'] = self.use_drops
        config['use_check'] = self.use_check
        config['stalemate'] = (
            {side.value - 1: value % 3 for side, value in self.stalemate_rule.items()}
            if isinstance(self.stalemate_rule, dict) else self.stalemate_rule
        )
        config['royal_mode'] = self.royal_piece_mode
        config['chaos_mode'] = self.chaos_mode
        config['chaos_seed'] = self.chaos_seed
        config['set_seed'] = self.set_seed
        config['roll_seed'] = self.roll_seed
        config['verbose'] = self.verbose
        config.save(get_filename('config', 'ini'))

    def debug_info(self) -> list[str]:
        debug_log_data = []  # noqa
        debug_log_data.append(f"Board size: {self.board_width}x{self.board_height}")
        debug_log_data.append(f"Window size: {self.width}x{self.height}")
        debug_log_data.append(f"Square size: {self.square_size}")
        debug_log_data.append(f"Color scheme ID: {'-' if self.color_index is None else self.color_index}")
        debug_log_data.append("Color scheme:")
        color_scheme = deepcopy(self.color_scheme)  # just in case trickster mode messes with the color scheme RIGHT NOW
        for k, v in color_scheme.items():
            debug_log_data.append(f"  {k} = {v}")
        debug_log_data.append(f"Piece sets ({len(piece_groups)}):")
        digits = len(str(len(piece_groups)))
        for i, group in enumerate(piece_groups):
            debug_log_data.append(f"  ID {i:0{digits}d}: {group['name']}")
        for i in sorted(self.chaos_sets):
            debug_log_data.append(f"  ID {-i:0{digits}d}: {self.chaos_sets[i][1]}")
        debug_log_data.append(
            f"ID blocklist ({len(self.board_config['block_ids'])}): "
            f"{', '.join(str(i) for i in self.board_config['block_ids']) or 'None'}"
        )
        debug_log_data.append(
            f"Chaos ID blocklist ({len(self.board_config['block_ids_chaos'])}): "
            f"{', '.join(str(i) for i in self.board_config['block_ids_chaos']) or 'None'}"
        )
        side_id_strings = {
            side: '-' if set_id is None else f"{set_id:0{digits}d}"
            for side, set_id in self.piece_set_ids.items()
        }
        debug_log_data.append(
            f"Game: "
            f"(ID {side_id_strings[Side.WHITE]}) {self.piece_set_names[Side.WHITE]} vs. "
            f"(ID {side_id_strings[Side.BLACK]}) {self.piece_set_names[Side.BLACK]}"
        )
        for side in self.piece_set_ids:
            debug_log_data.append(f"{side} setup: {', '.join(piece.name for piece in self.piece_sets[side])}")
            debug_log_data.append(f"{side} pieces ({len(self.movable_pieces[side])}):")
            for piece in self.movable_pieces[side]:
                debug_log_data.append(f'  {toa(piece.board_pos)} {piece.board_pos}: {piece.name}')
            if not self.movable_pieces[side]:
                debug_log_data[-1] += " None"
            debug_log_data.append(f"{side} royal pieces ({len(self.royal_pieces[side])}):")
            for piece in self.royal_pieces[side]:
                debug_log_data.append(f'  {toa(piece.board_pos)} {piece.board_pos}: {piece.name}')
            if not self.royal_pieces[side]:
                debug_log_data[-1] += " None"
            debug_log_data.append(f"{side} quasi-royal pieces ({len(self.quasi_royal_pieces[side])}):")
            for piece in self.quasi_royal_pieces[side]:
                debug_log_data.append(f'  {toa(piece.board_pos)} {piece.board_pos}: {piece.name}')
            if not self.quasi_royal_pieces[side]:
                debug_log_data[-1] += " None"
            debug_log_data.append(f"{side} probabilistic pieces ({len(self.probabilistic_pieces[side])}):")
            for piece in self.probabilistic_pieces[side]:
                debug_log_data.append(f'  {toa(piece.board_pos)} {piece.board_pos}: {piece.name}')
            if not self.probabilistic_pieces[side]:
                debug_log_data[-1] += " None"
            debug_log_data.append(f"{side} auto-ranged pieces ({len(self.auto_ranged_pieces[side])}):")
            for piece in self.auto_ranged_pieces[side]:
                debug_log_data.append(f'  {toa(piece.board_pos)} {piece.board_pos}: {piece.name}')
            if not self.auto_ranged_pieces[side]:
                debug_log_data[-1] += " None"
            debug_log_data.append(f"{side} auto-capture squares ({len(self.auto_capture_markers[side])}):")
            for pos in sorted(self.auto_capture_markers[side]):
                piece_poss = self.auto_capture_markers[side][pos]
                debug_log_data.append(f"""  {toa(pos)} {pos}: (From {len(piece_poss)}) {
                    ', '.join(f'{toa(xy)} {xy}' for xy in sorted(piece_poss))
                }""")
            if not self.auto_capture_markers[side]:
                debug_log_data[-1] += " None"
            piece_list = ', '.join(piece.name for piece in self.edit_promotions[side])
            debug_log_data.append(
                f"{side} replacements ({len(self.edit_promotions[side])}): {piece_list if piece_list else 'None'}"
            )
        debug_log_data.append(f"Edit piece set: {self.edit_piece_set_id}")
        debug_log_data.append(f"Custom pieces ({len(self.custom_pieces)}):")
        for piece, data in self.custom_pieces.items():
            debug_log_data.append(f"  '{piece}': {save_custom_type(data)}")
        if not self.custom_pieces:
            debug_log_data[-1] += " None"
        debug_log_data.append(f"Custom layout ({len(self.custom_layout)}):")
        for pos, piece in self.custom_layout.items():
            suffixes = []
            if piece.movement and piece.movement.total_moves:
                suffixes.append(f"Moves: {piece.movement.total_moves}")
            if piece.promoted_from:
                suffixes.append(f"Promoted from: {piece.promoted_from.name}")
            if piece.is_hidden is False:
                suffixes.append('Never hide')
            suffix = f" ({', '.join(suffixes)})" if suffixes else ''
            debug_log_data.append(f"  {toa(pos)} {pos}: {piece}{suffix}")
        if not self.custom_layout:
            debug_log_data[-1] += " None"
        data = (self.load_dict or {}).get('promotions', {})
        for side in self.piece_set_ids:
            promotions = self.custom_promotions.get(side, {})
            debug_log_data.append(f"Custom promotions for {side} ({len(promotions)}):")
            for piece in promotions:
                debug_log_data.append(f"  {piece.name} ({len(promotions[piece])}):")
                compressed = data.get(str(side.value), {}).get(save_piece_type(piece), {})
                from_mapping = frm(list(compressed), self.width, self.height)
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
        data = (self.load_dict or {}).get('drops', {})
        for side in self.piece_set_ids:
            drops = self.custom_drops.get(side, {})
            debug_log_data.append(f"Drop rules for {side} ({len(drops)}):")
            for piece in drops:
                debug_log_data.append(f"  {piece.name} ({len(drops[piece])}):")
                compressed = data.get(str(side.value), {}).get(save_piece_type(piece), {})
                from_mapping = frm(list(compressed), self.width, self.height)
                mapping = {}
                for pos, value in from_mapping.items():
                    if value not in mapping:
                        mapping[value] = pos
                for value, pos in mapping.items():
                    to_piece = drops[piece][pos]
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
                    debug_log_data.append(f"    {value} {fra(value)}: {to_piece.name}{suffix}")
                if not drops[piece]:
                    debug_log_data[-1] += " None"
            if not drops:
                debug_log_data[-1] += " None"
        for side in self.custom_extra_drops:
            debug_log_data.append(
                f"Starting drops of {side} ({len(self.custom_extra_drops[side])}): "
                f"{', '.join(piece.name for piece in self.custom_extra_drops[side]) or 'None'}"
            )
        for side in self.captured_pieces:
            debug_log_data.append(
                f"Drops of {side} ({len(self.captured_pieces[side])}): "
                f"{', '.join(piece.name for piece in self.captured_pieces[side]) or 'None'}"
            )
        en_passant_pos = toa(self.en_passant_target.board_pos) if self.en_passant_target else 'None'
        debug_log_data.append(f"En passant target: {en_passant_pos}")
        en_passant_squares = ', '.join(toa(xy) for xy in sorted(self.en_passant_markers)) or 'None'
        debug_log_data.append(f"En passant squares ({len(self.en_passant_markers)}): {en_passant_squares}")
        castling_ep_pos = toa(self.castling_ep_target.board_pos) if self.castling_ep_target else 'None'
        debug_log_data.append(f"Castling EP target: {castling_ep_pos}")
        castling_ep_squares = ', '.join(toa(xy) for xy in sorted(self.castling_ep_markers)) or 'None'
        debug_log_data.append(f"Castling EP squares ({len(self.castling_ep_markers)}): {castling_ep_squares}")
        piece_modes = {0: "Shown", 1: "Hidden", 2: "Penultima"}
        debug_log_data.append(f"Hide pieces: {self.should_hide_pieces} - {piece_modes[self.should_hide_pieces]}")
        move_modes = {None: "Default", False: "Shown", True: "Hidden"}
        debug_log_data.append(f"Hide moves: {self.should_hide_moves} - {move_modes[self.should_hide_moves]}")
        drop_modes = {k: f"Pieces {v} be dropped on the board" for k, v in {False: "cannot", True: "can"}.items()}
        debug_log_data.append(f"Use drops: {self.use_drops} - {drop_modes[self.use_drops]}")
        check_modes = {False: "Capture the royal piece to win", True: "Checkmate the royal piece to win"}
        debug_log_data.append(f"Use check: {self.use_check} - {check_modes[self.use_check]}")
        stalemate_modes = {0: "draws", 1: "loses", -1: "wins"}
        if isinstance(self.stalemate_rule, dict):
            debug_log_data.append(f"Stalemate rules")
            for side, mode in self.stalemate_rule.items():
                debug_log_data.append(f"  {side} {stalemate_modes[mode]} when stalemated")
        else:
            debug_log_data.append(f"Stalemate rule: Player {stalemate_modes[self.stalemate_rule]} when stalemated")
        royal_modes = {0: "Default", 1: "Force royal (Threaten Any)", 2: "Force quasi-royal (Threaten Last)"}
        debug_log_data.append(f"Royal mode: {self.royal_piece_mode} - {royal_modes[self.royal_piece_mode]}")
        chaos_modes = {
            0: "Off",
            1: "Chaos (Matching Pieces)",
            2: "Chaos (Matching Pieces), Asymmetrical",
            3: "Extreme Chaos (Any Pieces)",
            4: "Extreme Chaos (Any Pieces), Asymmetrical"
        }
        debug_log_data.append(f"Chaos mode: {self.chaos_mode} - {chaos_modes[self.chaos_mode]}")
        debug_log_data.append(f"Board mode: {'Edit' if self.edit_mode else 'Play'}")
        debug_log_data.append(f"Current ply: {self.ply_count}")
        if self.turn_pieces:
            turn_pieces = f" ({', '.join(sorted(piece.name for piece in self.turn_pieces))})"
        else:
            turn_pieces = ''
        self.log(f"Turn side: {self.turn_side if self.turn_side else 'None'}{turn_pieces}")
        debug_log_data.append(f"Turn order ({len(self.turn_order)}):")
        for i, data in enumerate(self.turn_order):
            if isinstance(data, list):
                turn_side = data[0]
                turn_pieces = f" ({', '.join(sorted(piece.name for piece in data[1]))})"
            else:
                turn_side = data
                turn_pieces = ''
            self.log(f"  {i + 1}: {turn_side if turn_side else 'None'}{turn_pieces}")
        possible_moves = sum((sum(v.values(), []) for v in self.moves.get(self.turn_side, {}).values()), [])
        debug_log_data.append(f"Moves possible: {len(possible_moves)}")
        debug_log_data.append(f"Unique moves: {sum(len(i) for i in self.unique_moves()[self.turn_side].values())}")
        debug_log_data.append(f"Check side: {self.check_side if self.check_side else 'None'}")
        debug_log_data.append(f"Game over: {self.game_over}")
        debug_log_data.append(f"Action history ({len(self.move_history)}):")
        for i, move in enumerate(self.move_history):
            if not move:
                debug_log_data.append(f"  {i + 1}: (Pass) None")
            else:
                move_type = (
                    'Edit' if move.is_edit else 'Drop' if move.movement_type == movement.DropMovement else 'Move'
                )
                debug_log_data.append(f"  {i + 1}: ({move_type}) {move}")
                j = 0
                while move.chained_move:
                    move = move.chained_move
                    move_type = (
                        'Edit' if move.is_edit else 'Drop' if move.movement_type == movement.DropMovement else 'Move'
                    )
                    debug_log_data.append(f"  {i + 1}.{j + 1}: ({move_type}) {move}")
                    j += 1
        if not self.move_history:
            debug_log_data[-1] += " None"
        debug_log_data.append(f"Future action history ({len(self.future_move_history)}):")
        for i, move in enumerate(self.future_move_history[::-1], len(self.move_history)):
            if not move:
                debug_log_data.append(f"  {i + 1}: (Pass) None")
            else:
                move_type = (
                    'Edit' if move.is_edit else 'Drop' if move.movement_type == movement.DropMovement else 'Move'
                )
                debug_log_data.append(f"  {i + 1}: ({move_type}) {move}")
                j = 0
                while move.chained_move:
                    move = move.chained_move
                    move_type = (
                        'Edit' if move.is_edit else 'Drop' if move.movement_type == movement.DropMovement else 'Move'
                    )
                    debug_log_data.append(f"  {i + 1}.{j + 1}: ({move_type}) {move}")
                    j += 1
        if not self.future_move_history:
            debug_log_data[-1] += " None"
        empty = True
        debug_log_data.append(f"Roll history ({len(self.roll_history)}):")
        for i, roll in enumerate(self.roll_history):
            if roll:
                empty = False
                debug_log_data.append(f"  Roll {i + 1}:")
                for pos, value in roll.items():
                    debug_log_data.append(f"    {toa(pos)} {pos}: {value}")
        if empty:
            debug_log_data[-1] += " None"
        empty = True
        debug_log_data.append(f"Probabilistic piece history ({len(self.probabilistic_piece_history)}):")
        for i, pieces in enumerate(self.probabilistic_piece_history):
            if pieces:
                empty = False
                debug_log_data.append(f"  Ply {i + 1}:")
                for pos, piece in sorted(pieces, key=lambda x: x[0]):
                    debug_log_data.append(f"    {toa(pos)} {pos}: {piece.name}")
        if empty:
            debug_log_data[-1] += " None"
        debug_log_data.append(f"Roll seed: {self.roll_seed} (update: {self.board_config['update_roll_seed']})")
        debug_log_data.append(f"Piece set seed: {self.set_seed}")
        debug_log_data.append(f"Chaos set seed: {self.chaos_seed}")
        return debug_log_data

    def run(self):
        if self.board_config['save_update_mode'] < 0 and self.load_data is not None:
            self.close()
        else:
            self.set_visible()
            super().run()
