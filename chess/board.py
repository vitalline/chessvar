from copy import copy, deepcopy
from datetime import datetime
from itertools import product, zip_longest
from json import dump, load
from math import ceil, sqrt
from os import name as os_name, system
from os.path import isfile, join
from random import Random
from sys import argv
from traceback import print_exc
from typing import Type

from PIL.ImageColor import getrgb
from arcade import key, MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT, Text
from arcade import Sprite, SpriteList, Window
from arcade import start_render

from chess.color import colors, trickster_colors
from chess.color import average, darken, desaturate, lighten, saturate
from chess.config import Config
from chess.movement import movement
from chess.movement.move import Move
from chess.movement.util import Position, add, to_alpha as toa, from_alpha as fra
from chess.pieces import pieces as abc
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
from chess.pieces.groups.util import NoPiece
from chess.pieces.pieces import Side
from chess.save import load_move, load_piece, load_rng, load_type, save_move, save_piece, save_rng, save_type
from chess.util import Default, Unset, base_dir

piece_groups: list[dict[str, str | list[Type[abc.Piece]]]] = [
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

pawn_row: list[Type[abc.Piece]] = [fide.Pawn] * board_width
empty_row: list[Type[abc.Piece]] = [NoPiece] * board_width

white_row = [Side.WHITE] * board_width
black_row = [Side.BLACK] * board_width
neutral_row = [Side.NONE] * board_width

types = [white_row, pawn_row] + [empty_row] * (board_height - 4) + [pawn_row, black_row]
sides = [white_row, white_row] + [neutral_row] * (board_height - 4) + [black_row, black_row]

white_promotion_squares = {(board_height - 1, i) for i in range(board_width)}
black_promotion_squares = {(0, i) for i in range(board_width)}
promotion_squares = {Side.WHITE: white_promotion_squares, Side.BLACK: black_promotion_squares}

default_size = 50
min_size = 25
max_size = 100
size_step = 5

base_rng = Random()
max_seed = 2 ** 32 - 1

movements = []

config_path = join(base_dir, 'config.ini')

invalid_chars = ':<>|"?*'
invalid_chars_trans_table = str.maketrans(invalid_chars, '_' * len(invalid_chars))


def get_filename(name: str, ext: str, in_dir: str = base_dir, ts_format: str = "%Y-%m-%d_%H-%M-%S") -> str:
    name_args = [name, datetime.now().strftime(ts_format)]
    full_name = '_'.join(s for s in name_args if s).translate(invalid_chars_trans_table)
    return join(in_dir, f"{full_name}.{ext}")


def get_set(side: Side, set_id: int) -> list[Type[abc.Piece]]:
    piece_group = piece_groups[set_id]
    return piece_group.get(f"set_{side.key()[0]}", piece_group.get('set', empty_row))


def get_set_name(piece_set: list[Type[abc.Piece]]) -> str:
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


class Board(Window):

    def __init__(self):
        # super boring initialization stuff (bluh bluh)
        self.board_config = Config(config_path)
        if not isfile(config_path):
            self.board_config.save(config_path)

        self.board_width, self.board_height = board_width, board_height
        self.square_size = default_size

        super().__init__(
            width=(self.board_width + 2) * self.square_size,
            height=(self.board_height + 2) * self.square_size,
            title='Chess',
            resizable=True,
            vsync=True,
            center_window=True,
        )

        self.origin = self.width / 2, self.height / 2
        self.set_minimum_size((self.board_width + 2) * min_size, (self.board_height + 2) * min_size)

        if self.board_config['color_id'] < 0 or self.board_config['color_id'] >= len(colors):
            self.board_config['color_id'] %= len(colors)
            self.board_config.save(config_path)

        self.color_index = self.board_config['color_id'] or 0  # index of the current color scheme
        self.color_scheme = colors[self.color_index]  # current color scheme
        self.background_color = self.color_scheme["background_color"]  # background color
        self.log_data = []  # list of presently logged strings
        self.skip_mouse_move = False  # setting this to True skips one mouse movement offset
        self.hovered_square = None  # square we are currently hovering over
        self.clicked_square = None  # square we clicked on
        self.selected_square = None  # square selected for moving
        self.square_was_clicked = False  # used to discern two-click moving from dragging
        self.piece_was_selected = False  # used to discern between selecting a piece and moving it
        self.held_buttons = 0  # mouse button that was pressed
        self.en_passant_target = None  # piece that can be captured en passant
        self.en_passant_markers = set()  # squares where it can be captured
        self.promotion_piece = None  # piece that is currently being promoted
        self.promotion_area = {}  # squares to draw possible promotions on
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
        self.turn_side = Side.WHITE  # side whose turn it is
        self.check_side = Side.NONE  # side that is currently in check
        self.castling_threats = set()  # squares that are attacked in a way that prevents castling
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
        self.promotions = {Side.WHITE: [], Side.BLACK: []}  # types of pieces each side promotes to
        self.promotion_squares = promotion_squares  # squares where pawns can promote for each side
        self.edit_promotions = {Side.WHITE: [], Side.BLACK: []}  # types of pieces each side can promote to in edit mode
        self.movable_pieces = {Side.WHITE: [], Side.BLACK: []}  # pieces that can be moved by each side
        self.royal_pieces = {Side.WHITE: [], Side.BLACK: []}  # these have to stay on the board and should be protected
        self.quasi_royal_pieces = {Side.WHITE: [], Side.BLACK: []}  # at least one of these has to stay on the board
        self.auto_ranged_pieces = {Side.WHITE: [], Side.BLACK: []}  # pieces that auto-capture anywhere they can move to
        self.auto_capture_markers = {Side.WHITE: {}, Side.BLACK: {}}  # squares where the side's pieces can auto-capture
        self.probabilistic_pieces = {Side.WHITE: [], Side.BLACK: []}  # pieces that can move probabilistically
        self.probabilistic_piece_history = []  # list of probabilistic piece positions for every ply
        self.penultima_pieces = {Side.WHITE: {}, Side.BLACK: {}}  # piece textures that are used for penultima mode
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
        self.highlight.color = self.color_scheme["highlight_color"]  # color it according to the color scheme
        self.highlight.scale = self.square_size / self.highlight.texture.width  # scale it to the size of a square
        self.selection = Sprite("assets/util/selection.png")  # sprite for the selection marker
        self.selection.color = self.color_scheme["selection_color"]  # color it according to the color scheme
        self.selection.scale = self.square_size / self.selection.texture.width  # scale it to the size of a square
        self.active_piece = None  # piece that is currently being moved
        self.label_list = []  # labels for the rows and columns
        self.board_sprite_list = SpriteList()  # sprites for the board squares
        self.move_sprite_list = SpriteList()  # sprites for the move markers
        self.piece_sprite_list = SpriteList()  # sprites for the pieces
        self.promotion_area_sprite_list = SpriteList()  # sprites for the promotion area background tiles
        self.promotion_piece_sprite_list = SpriteList()  # sprites for the possible promotion pieces

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

        # initialize row/column labels
        label_kwargs = {
            'anchor_x': 'center',
            'anchor_y': 'center',
            'font_name': 'Courier New',
            'font_size': self.square_size / 2,
            'width': self.square_size / 2,
            'bold': True,
            'align': 'center',
            'color': self.color_scheme["text_color"],
        }

        for row in range(self.board_height):
            self.label_list.extend([
                Text(str(row + 1), *self.get_screen_position((row, -1)), **label_kwargs),
                Text(str(row + 1), *self.get_screen_position((row, board_width)), **label_kwargs)
            ])

        for col in range(self.board_width):
            self.label_list.extend([
                Text(chr(col + ord('a')), *self.get_screen_position((-1, col)), **label_kwargs),
                Text(chr(col + ord('a')), *self.get_screen_position((board_height, col)), **label_kwargs),
            ])

        # initialize board sprites
        for row, col in product(range(self.board_height), range(self.board_width)):
            sprite = Sprite("assets/util/square.png")
            sprite.color = self.color_scheme[f"{'light' if self.is_light_square((row, col)) else 'dark'}_square_color"]
            sprite.position = self.get_screen_position((row, col))
            sprite.scale = self.square_size / sprite.texture.width
            self.board_sprite_list.append(sprite)

        # set up pieces on the board
        loaded = False
        if len(argv) > 1:
            # noinspection PyBroadException
            try:
                save_path = join(base_dir, argv[1])
                if isfile(save_path):
                    self.load_board(save_path)
                    loaded = True
            except Exception:
                print_exc()
        if not loaded:
            if self.should_hide_pieces == 1:
                self.log(f"[Ply {self.ply_count}] Info: Pieces hidden")
            if self.should_hide_pieces == 2:
                self.log(f"[Ply {self.ply_count}] Info: Penultima mode activated!")
            if self.royal_piece_mode == 1:
                self.log(f"[Ply {self.ply_count}] Info: Using royal check rule (threaten any royal piece)")
            if self.royal_piece_mode == 2:
                self.log(f"[Ply {self.ply_count}] Info: Using quasi-royal check rule (threaten last royal piece)")
            self.reset_board(update=True)

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

    def get_piece(self, pos: Position | None) -> abc.Piece:
        return NoPiece(self, pos) if self.not_on_board(pos) else self.pieces[pos[0]][pos[1]]

    def get_side(self, pos: Position | None) -> Side:
        return self.get_piece(pos).side

    def get_promotion_side(self, piece: abc.Piece | None):
        return piece.side or (Side.WHITE if piece.board_pos[0] < self.board_height / 2 else Side.BLACK)

    def set_position(self, piece: abc.Piece, pos: Position) -> None:
        piece.board_pos = pos
        piece.position = self.get_screen_position(pos)

    def reset_position(self, piece: abc.Piece) -> None:
        self.set_position(piece, piece.board_pos)

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
        self.selection.color = self.color_scheme["selection_color"]
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

    def reset_board(self, update: bool = False) -> None:
        self.deselect_piece()
        self.clear_en_passant()
        self.clear_auto_capture_markers()

        self.turn_side = Side.WHITE
        self.game_over = False
        self.edit_mode = False
        self.chain_start = None
        self.promotion_piece = None
        self.ply_count = 0

        for sprite_list in self.piece_sprite_list, self.promotion_piece_sprite_list, self.promotion_area_sprite_list:
            sprite_list.clear()
            for sprite in sprite_list:
                sprite_list.remove(sprite)

        self.piece_sets, self.piece_set_names = self.get_piece_sets()

        if self.chaos_mode:
            no_chaos = True
            for i in self.piece_set_ids:
                if self.piece_set_ids[i] < 0:
                    no_chaos = False
                    break
            if no_chaos:
                self.chaos_mode = 0

        self.log(
            f"[Ply {self.ply_count}] Game: "
            f"{self.piece_set_names[Side.WHITE] if not self.should_hide_pieces else '???'} vs. "
            f"{self.piece_set_names[Side.BLACK] if not self.should_hide_pieces else '???'}"
        )
        self.ply_count += 1

        if update:
            self.edit_piece_set_id = self.board_config['edit_id']
            self.roll_history = []
            self.future_move_history = []
            self.probabilistic_piece_history = []
            self.reset_promotions()
            self.reset_edit_promotions()
            self.reset_penultima_pieces()
        else:
            self.future_move_history += self.move_history[::-1]

        if not self.board_config['update_roll_seed']:
            self.roll_history = []

        update_seed = not self.move_history and self.roll_history

        if update_seed:
            self.roll_history = []
            self.future_move_history = []
            self.probabilistic_piece_history = []

        if self.roll_rng is not None:
            if update or update_seed:
                if self.board_config['update_roll_seed']:
                    self.roll_seed = self.roll_rng.randint(0, 2 ** 32 - 1)

        self.roll_rng = Random(self.roll_seed)

        self.move_history = []

        self.pieces = []

        for row in range(self.board_height):
            self.pieces += [[]]

        for row, col in product(range(self.board_height), range(self.board_width)):
            piece_type = types[row][col]
            piece_side = sides[row][col]
            if isinstance(piece_type, abc.Side):
                piece_type = self.piece_sets[piece_side][col]
            self.pieces[row].append(
                piece_type(
                    board=self,
                    board_pos=(row, col),
                    side=piece_side,
                    promotions=self.promotions.get(piece_side),
                    promotion_squares=self.promotion_squares.get(piece_side),
                )
            )
            if not self.pieces[row][col].is_empty():
                self.update_piece(self.pieces[row][col])
                self.pieces[row][col].set_color(
                    self.color_scheme.get(
                        f"{self.pieces[row][col].side.key()}piece_color",
                        self.color_scheme["piece_color"]
                    ),
                    self.color_scheme["colored_pieces"]
                )
            self.pieces[row][col].scale = self.square_size / self.pieces[row][col].texture.width
            self.piece_sprite_list.append(self.pieces[row][col])

        self.load_moves()
        self.show_moves()

    def save_board(self, indent: int = None) -> None:
        data = {
            'board_size': [self.board_width, self.board_height],
            'window_size': [self.width, self.height],
            'square_size': self.square_size,
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
            'sets': {side.value: [save_type(t) for t in piece_set] for side, piece_set in self.piece_sets.items()},
            'pieces': {toa(p.board_pos): save_piece(p) for pieces in self.movable_pieces.values() for p in pieces},
            'moves': [save_move(m) for m in self.move_history],
            'future': [save_move(m) for m in self.future_move_history[::-1]],
            'rolls': {n: {toa(pos): d[pos] for pos in sorted(d)} for n, d in enumerate(self.roll_history) if d},
            'roll_piece_history': {
                n: {toa(pos): save_type(t) for pos, t in sorted(d, key=lambda x: x[0])}
                for n, d in enumerate(self.probabilistic_piece_history) if d
            },
            'auto_captures': {
                side.value: {toa(on): [toa(of) for of in sorted(ofs)] for on, ofs in d.items()}
                for side, d in self.auto_capture_markers.items() if d
            },
            'promotion': save_piece(self.promotion_piece),
            'chain_start': save_move(self.chain_start),
            'chain_moves': [
                save_move(m) for m in self.moves[self.chain_start.piece.side][self.chain_start.piece.board_pos]
            ] if self.chain_start else [],
            'ply': self.ply_count,
            'side': self.turn_side.value,
            'edit': self.edit_mode,
            'edit_promotion': self.edit_piece_set_id,
            'hide_pieces': self.should_hide_pieces,
            'hide_moves': self.should_hide_moves,
            'royal_mode': self.royal_piece_mode,
            'chaos_mode': self.chaos_mode,
            'set_seed': self.set_seed,
            'set_state': save_rng(self.set_rng),
            'roll_seed': self.roll_seed,
            'roll_state': save_rng(self.roll_rng),
            'roll_update': self.board_config['update_roll_seed'],
            'chaos_seed': self.chaos_seed,
            'chaos_state': save_rng(self.chaos_rng),
        }
        with open(get_filename('save', 'json'), 'w') as file:
            if indent is None:
                dump(data, file, separators=(',', ':'))
            else:
                dump(data, file, indent=indent)

    def load_board(self, path: str) -> None:
        self.deselect_piece()
        self.clear_en_passant()
        self.clear_auto_capture_markers()

        for sprite_list in self.piece_sprite_list, self.promotion_piece_sprite_list, self.promotion_area_sprite_list:
            sprite_list.clear()
            for sprite in sprite_list:
                sprite_list.remove(sprite)

        with open(path) as file:
            data = load(file)

        # might have to add more error checking to saving/loading, even if at the cost of slight redundancy.
        # who knows when someone decides to introduce a breaking change and absolutely destroy all the saves
        if (self.board_width, self.board_height) != tuple(data['board_size']):
            print(
                f"Warning: Board size does not match (was {tuple(data['board_size'])}, "
                f"but is {(self.board_width, self.board_height)})"
            )

        self.resize(*data['window_size'])
        self.update_sprites(data['flip_mode'])
        if self.square_size != data['square_size']:
            print(f"Warning: Square size does not match (was {data['square_size']}, but is {self.square_size})")

        self.color_index = data['color_index']
        if self.color_index is not None:  # None here means we're using a custom color scheme as defined in the savefile
            self.color_scheme = colors[self.color_index]
        for k, v in self.color_scheme.items():
            old = (tuple(data['color_scheme'][k]) if isinstance(v, tuple) else data['color_scheme'][k])
            if v != old:
                self.color_scheme[k] = old  # first time when we might have enough information to fully restore old data
                # in all cases before we had to pick one or the other, but here we can try to reload the save faithfully
                if self.color_index is not None:  # warning if there's an explicitly defined color scheme and it doesn't
                    print(f"Warning: Color scheme does not match ({k} was {old}, but is {v})")  # match the saved scheme

        self.board_config['block_ids'] = data['set_blocklist']
        self.board_config['block_ids_chaos'] = data['chaos_blocklist']

        self.should_hide_pieces = data['hide_pieces']
        self.should_hide_moves = data['hide_moves']
        self.royal_piece_mode = data['royal_mode']
        self.chaos_mode = data['chaos_mode']
        self.edit_mode = data['edit']
        self.edit_piece_set_id = data['edit_promotion']

        self.set_seed = data['set_seed']
        self.set_rng = Random(self.set_seed)
        self.roll_seed = data['roll_seed']
        self.roll_rng = Random(self.roll_seed)
        self.chaos_seed = data['chaos_seed']
        self.chaos_rng = Random(self.chaos_seed)
        self.board_config['update_roll_seed'] = data['roll_update']

        self.piece_set_ids = {Side(int(k)): v for k, v in data['set_ids'].items()}
        self.piece_sets, self.piece_set_names = self.get_piece_sets()
        save_piece_sets = {Side(int(v)): [load_type(t) for t in d] for v, d in data['sets'].items()}
        update_sets = False
        for side in self.piece_sets:
            if self.piece_sets[side] is None:
                self.piece_sets[side] = save_piece_sets[side]
                self.piece_set_names[side] = get_set_name(self.piece_sets[side])
                continue
            for i, pair in enumerate(zip(save_piece_sets[side], self.piece_sets[side])):
                if pair[0] != pair[1]:
                    # this can mean a few things, namely the RNG implementation changing or new sets/pieces being added.
                    # either way, we should at least try to load the old pieces defined in the save to recreate the game
                    print(
                        f"Warning: Piece set does not match ({side}: {toa(((0 if side == Side.WHITE else 7), i))} "
                        f"was {pair[0].name}, but is {pair[1].name})"
                    )
                    update_sets = True
        if update_sets:
            self.piece_sets = {side: save_piece_sets[side] for side in self.piece_sets}
            self.piece_set_names = {side: get_set_name(self.piece_sets[side]) for side in self.piece_sets}

        self.reset_promotions()
        self.reset_edit_promotions()
        self.reset_penultima_pieces()

        self.ply_count = data['ply']
        self.turn_side = Side(data['side'])
        self.move_history = [load_move(d, self) for d in data['moves']]
        self.future_move_history = [load_move(d, self) for d in data['future'][::-1]]

        rolls = data['rolls']
        self.roll_history = [
            ({fra(s): v for s, v in rolls[str(n)].items()} if str(n) in rolls else {}) for n in range(self.ply_count)
        ]
        rph = data['roll_piece_history']
        self.probabilistic_piece_history = [
            ({(fra(k), load_type(v)) for k, v in rph[str(n)].items()} if str(n) in rph else set())
            for n in range(self.ply_count)
        ]
        ac = data['auto_captures']
        self.auto_capture_markers = {
            side: {fra(on): {fra(of) for of in ofs} for on, ofs in ac[str(side.value)].items()}
            if str(side.value) in ac else {} for side in self.auto_capture_markers
        }

        self.chain_start = load_move(data['chain_start'], self)
        if self.move_history and self.move_history[-1] and self.move_history[-1].matches(self.chain_start):
            self.chain_start = self.move_history[-1]
        cm = data['chain_moves']
        self.chain_moves = {
            self.chain_start.piece.side: {
                (self.chain_start.pos_from, self.chain_start.pos_to): [load_move(m, self) for m in cm]
            }, self.chain_start.piece.side.opponent(): {}
        } if self.chain_start else {}

        self.set_rng = load_rng(data['set_state'])
        self.roll_rng = load_rng(data['roll_state'])
        self.chaos_rng = load_rng(data['chaos_state'])

        self.pieces = []

        for row in range(self.board_height):
            self.pieces += [[]]

        for row, col in product(range(self.board_height), range(self.board_width)):
            piece_data = data['pieces'].get(toa((row, col)))
            self.pieces[row].append(
                NoPiece(self, (row, col)) if piece_data is None else load_piece(piece_data, self)
            )
            self.pieces[row][col].scale = self.square_size / self.pieces[row][col].texture.width
            self.piece_sprite_list.append(self.pieces[row][col])

        self.promotion_piece = load_piece(data['promotion'], self)

        if self.move_history:
            last_move = self.move_history[-1]
            if last_move and not last_move.is_edit:
                last_move.piece.movement.reload(last_move, last_move.piece)

        self.load_pieces()
        self.update_colors()

        self.log(f"[Ply {self.ply_count}] Info: Game loaded from {path}")
        if self.should_hide_pieces == 1:
            self.log(f"[Ply {self.ply_count}] Info: Pieces hidden")
        if self.should_hide_pieces == 2:
            self.log(f"[Ply {self.ply_count}] Info: Penultima mode activated!")
        if self.royal_piece_mode == 1:
            self.log(f"[Ply {self.ply_count}] Info: Using royal check rule (threaten any royal piece)")
        if self.royal_piece_mode == 2:
            self.log(f"[Ply {self.ply_count}] Info: Using quasi-royal check rule (threaten last royal piece)")
        if None in self.piece_set_ids.values():
            self.log(f"[Ply {self.ply_count}] Info: Resuming saved game (with custom piece sets)")
        else:
            some = 'regular' if not self.chaos_mode else 'chaotic'
            same = self.piece_set_ids[Side.WHITE] == self.piece_set_ids[Side.BLACK]
            if self.chaos_mode in {3, 4}:
                some = f"extremely {some}"
            if self.chaos_mode in {2, 4}:
                some = f"asymmetrical {some}"
            if same:
                some = f"a{'' if self.chaos_mode in {0, 1} else 'n'} {some}"
            sets = "set" if same else "sets"
            self.log(f"[Ply {self.ply_count}] Info: Resuming saved game (with {some} piece {sets})")
        self.log(
            f"[Ply {self.ply_count}] Game: "
            f"{self.piece_set_names[Side.WHITE] if not self.should_hide_pieces else '???'} vs. "
            f"{self.piece_set_names[Side.BLACK] if not self.should_hide_pieces else '???'}"
        )
        self.log(f"[Ply {self.ply_count}] Mode: {'EDIT' if self.edit_mode else 'PLAY'}")
        self.log(f"[Ply {self.ply_count}] Info: {self.turn_side}'s turn")

        if self.promotion_piece:
            self.start_promotion(
                self.promotion_piece,
                (self.edit_promotions if self.edit_mode else self.promotions)[
                    self.get_promotion_side(self.promotion_piece)
                ]
            )
        else:
            if not self.edit_mode:
                self.update_status()
            if data['selection']:
                self.select_piece(fra(data['selection']))

    def empty_board(self) -> None:
        self.deselect_piece()
        self.clear_en_passant()
        self.clear_auto_capture_markers()

        self.turn_side = Side.WHITE
        self.game_over = False
        self.chain_start = None
        self.promotion_piece = None
        self.ply_count = 0

        for sprite_list in self.piece_sprite_list, self.promotion_piece_sprite_list, self.promotion_area_sprite_list:
            sprite_list.clear()
            for sprite in sprite_list:
                sprite_list.remove(sprite)

        self.log(f"[Ply {self.ply_count}] Info: Board cleared")
        if not self.edit_mode:
            self.log(f"[Ply {self.ply_count}] Mode: EDIT")
        self.edit_mode = True
        self.ply_count += 1

        self.edit_piece_set_id = self.board_config['edit_id']
        self.roll_history = []
        self.future_move_history = []
        self.probabilistic_piece_history = []
        self.reset_promotions()
        self.reset_edit_promotions()
        self.reset_penultima_pieces()

        if self.board_config['update_roll_seed']:
            self.roll_seed = self.roll_rng.randint(0, 2 ** 32 - 1)

        self.roll_rng = Random(self.roll_seed)

        self.move_history = []

        self.pieces = []

        for row in range(self.board_height):
            self.pieces += [[]]

        for row, col in product(range(self.board_height), range(self.board_width)):
            self.pieces[row].append(NoPiece(self, (row, col)))
            self.pieces[row][col].scale = self.square_size / self.pieces[row][col].texture.width
            self.piece_sprite_list.append(self.pieces[row][col])

        self.load_moves()
        self.show_moves()

    def reset_promotions(self, piece_sets: dict[Side, list[Type[abc.Piece]]] | None = None) -> None:
        if piece_sets is None:
            piece_sets = self.piece_sets
        self.promotions = {side: [] for side in self.promotions}
        for side in self.promotions:
            used_piece_set = set()
            for pieces in (
                    piece_sets[side][3::-1], piece_sets[side.opponent()][3::-1],
                    piece_sets[side][5:], piece_sets[side.opponent()][5:],
            ):
                promotion_types = []
                for piece in pieces:
                    if piece not in used_piece_set and not issubclass(piece, abc.RoyalPiece):
                        used_piece_set.add(piece)
                        promotion_types.append(piece)
                self.promotions[side].extend(promotion_types[::-1])

    def reset_edit_promotions(self, piece_sets: dict[Side, list[Type[abc.Piece]]] | None = None) -> None:
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

    def reset_penultima_pieces(self, piece_sets: dict[Side, list[Type[abc.Piece]]] | None = None) -> None:
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
    ) -> tuple[dict[Side, list[Type[abc.Piece]]], dict[Side, str]]:
        if piece_set_ids is None:
            piece_set_ids = self.piece_set_ids
        elif isinstance(piece_set_ids, int):
            piece_set_ids = {side: piece_set_ids for side in self.piece_set_ids}  # type: ignore
        piece_sets = {Side.WHITE: [], Side.BLACK: []}
        piece_names = {Side.WHITE: [], Side.BLACK: []}
        for side in piece_set_ids:
            if piece_set_ids[side] is None:
                piece_sets[side] = self.piece_sets[side].copy()
                piece_names[side] = self.piece_set_names[side]
            elif piece_set_ids[side] < 0:
                for i in range(-piece_set_ids[side]):
                    if i + 1 not in self.chaos_sets:
                        self.chaos_sets[i + 1] = self.get_chaos_set(side)
                chaos_set = self.chaos_sets.get(-piece_set_ids[side], [[], '-'])
                piece_sets[side] = chaos_set[0].copy()
                piece_names[side] = chaos_set[1]
            else:
                piece_group = piece_groups[piece_set_ids[side]]
                piece_sets[side] = get_set(side, piece_set_ids[side])
                piece_names[side] = piece_group.get('name', '-')
        return piece_sets, piece_names

    def get_random_set(self, side: Side, asymmetrical: bool = False) -> tuple[list[Type[abc.Piece]], str]:
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

    def get_extremely_random_set(self, side: Side, asymmetrical: bool = False) -> tuple[list[Type[abc.Piece]], str]:
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

    def get_chaos_set(self, side: Side) -> tuple[list[Type[abc.Piece]], str]:
        asymmetrical = self.chaos_mode in {2, 4}
        if self.chaos_mode in {1, 2}:
            return self.get_random_set(side, asymmetrical)
        if self.chaos_mode in {3, 4}:
            return self.get_extremely_random_set(side, asymmetrical)

    def load_chaos_sets(self, mode: int, same: bool) -> None:
        chaotic = "chaotic"
        if mode in {3, 4}:
            chaotic = f"extremely {chaotic}"
        if mode in {2, 4}:
            chaotic = f"asymmetrical {chaotic}"
        if same:
            chaotic = f"a{'' if mode == 1 else 'n'} {chaotic}"
        sets = "set" if same else "sets"
        self.log(f"[Ply {self.ply_count}] Info: Starting new game (with {chaotic} piece {sets})")
        self.chaos_mode = mode
        self.chaos_sets = {}
        self.chaos_seed = self.chaos_rng.randrange(2 ** 32)
        self.chaos_rng = Random(self.chaos_seed)
        self.piece_set_ids = {Side.WHITE: -1, Side.BLACK: -1 if same else -2}
        self.reset_board(update=True)

    def load_pieces(self):
        self.movable_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.royal_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.quasi_royal_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.probabilistic_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.auto_ranged_pieces = {Side.WHITE: [], Side.BLACK: []}
        for row, col in product(range(self.board_height), range(self.board_width)):
            piece = self.get_piece((row, col))
            if piece.side and not piece.is_empty():
                self.movable_pieces[piece.side].append(piece)
                if isinstance(piece, abc.RoyalPiece):
                    self.royal_pieces[piece.side].append(piece)
                elif isinstance(piece, abc.QuasiRoyalPiece):
                    self.quasi_royal_pieces[piece.side].append(piece)
                if isinstance(piece.movement, movement.ProbabilisticMovement):
                    self.probabilistic_pieces[piece.side].append(piece)
                if isinstance(piece.movement, movement.AutoRangedAutoCaptureRiderMovement):
                    self.auto_ranged_pieces[piece.side].append(piece)
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

    def load_check(self):
        self.load_pieces()
        self.check_side = Side.NONE
        self.castling_threats = set()
        for royal in self.royal_pieces[self.turn_side]:
            movement_list = (
                royal.movement.movements if isinstance(royal.movement, movement.BaseMultiMovement) else [royal.movement]
            )
            castle_movements = set(m for m in movement_list if isinstance(m, movement.CastlingMovement))
            castle_squares = set(
                add(royal.board_pos, offset)
                for castling in castle_movements
                for offset in castling.gap + [castling.direction]
            )
            self.ply_simulation += 1
            for piece in self.movable_pieces[self.turn_side.opponent()]:
                if isinstance(piece.movement, movement.ProbabilisticMovement):
                    continue
                for move in piece.moves():
                    last_move = copy(move)
                    self.update_move(last_move)
                    if last_move.promotion and not last_move.is_edit:
                        new_piece = last_move.promotion
                        last_move.piece = new_piece
                        self.update_promotion_auto_captures(last_move)
                    self.update_auto_captures(last_move, self.turn_side)
                    while last_move:
                        if last_move.pos_to == royal.board_pos or last_move.captured_piece == royal:
                            self.check_side = self.turn_side
                            self.castling_threats = castle_squares
                        if last_move.pos_to in castle_squares:
                            self.castling_threats.add(last_move.pos_to)
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
        castling_threats = self.castling_threats.copy()
        en_passant_target = self.en_passant_target
        en_passant_markers = self.en_passant_markers.copy()
        last_chain_move = self.chain_start
        if last_chain_move:
            while last_chain_move.chained_move:
                last_chain_move = last_chain_move.chained_move
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
            chain_moves = (
                self.chain_moves.get(turn_side, {}).get((last_chain_move.pos_from, last_chain_move.pos_to))
                if last_chain_move is not None else None
            )
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
                    self.roll_history = self.roll_history[:self.ply_count]
                    self.probabilistic_piece_history = self.probabilistic_piece_history[:self.ply_count]
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
                for move in list(piece.moves()) if chain_moves is None else chain_moves:
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
                    while chained_move:
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
                        chained_move = chained_move.chained_move
                    self.ply_simulation += 1
                    self.load_check()
                    self.ply_simulation -= 1
                    for chained_move in move_chain:
                        if chained_move.captured_piece in royal_pieces[turn_side]:
                            self.check_side = turn_side
                        if chained_move.captured_piece in royal_pieces[turn_side.opponent()]:
                            check_side = self.turn_side.opponent()
                            self.game_over = True
                    if self.check_side != turn_side:
                        self.moves[turn_side].setdefault(move.pos_from, []).append(move)
                        if move.chained_move:
                            (
                                self.chain_moves[turn_side]
                                .setdefault((move.pos_from, move.pos_to), [])
                                .append(move.chained_move)
                            )
                    for chained_move in move_chain[::-1]:
                        self.undo(chained_move)
                        self.revert_auto_capture_markers(chained_move)
                    self.check_side = check_side
                    self.castling_threats = castling_threats.copy()
                    if en_passant_target is not None:
                        self.en_passant_target = en_passant_target
                        self.en_passant_markers = en_passant_markers.copy()
                        for marker in self.en_passant_markers:
                            self.mark_en_passant(self.en_passant_target.board_pos, marker)
            self.moves_queried[turn_side] = True
        if theoretical_moves_for is None:
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
                    self.theoretical_moves[turn_side].setdefault(move.pos_from, []).append(move)
            self.theoretical_moves_queried[turn_side] = True
        self.movable_pieces = movable_pieces
        self.royal_pieces = royal_pieces
        self.quasi_royal_pieces = quasi_royal_pieces
        self.probabilistic_pieces = probabilistic_pieces
        self.auto_ranged_pieces = auto_ranged_pieces
        self.auto_capture_markers = auto_capture_markers
        self.check_side = check_side
        self.castling_threats = castling_threats

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
            for move in sum(self.moves.get(turn_side, {}).values(), []):
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
                    if (
                        (move.chained_move or self.chain_moves.get(turn_side, {}).get((move.pos_from, move.pos_to)))
                        and not issubclass(
                            move.movement_type,
                            movement.CastlingMovement |
                            movement.RangedAutoCaptureRiderMovement
                        )
                    ):
                        move.chained_move = Unset  # do not chain moves because we are only counting one-move sequences
                    moves[turn_side].setdefault(move.pos_from, []).append(move)
        return moves

    def find_move(self, pos_from: Position, pos_to: Position) -> Move | None:
        for move in self.moves.get(self.turn_side, {}).get(pos_from, ()):
            if move.pos_from == move.pos_to:
                if move.captured_piece is None and pos_to == move.pos_to:
                    return copy(move)
                if move.captured_piece is not None and pos_to == move.captured_piece.board_pos:
                    return copy(move)
            elif pos_to == move.pos_to:
                return copy(move)
        return None

    def show_moves(self) -> None:
        self.hide_moves()
        move_sprites = dict()
        pos = self.selected_square or self.hovered_square or self.get_board_position(self.highlight.position)
        if not self.not_on_board(pos):
            piece = self.get_piece(pos)
            if not piece.is_empty() and not piece.is_hidden:
                if self.display_theoretical_moves[piece.side]:
                    move_dict = self.theoretical_moves.get(piece.side, {})
                elif self.display_moves[piece.side]:
                    move_dict = self.moves.get(piece.side, {})
                else:
                    move_dict = {}
                for move in move_dict.get(pos, ()):
                    capture = move.captured_piece
                    pos_to = capture.board_pos if move.pos_from == move.pos_to and capture is not None else move.pos_to
                    if pos_to in move_sprites:
                        continue
                    sprite = Sprite(f"assets/util/{'move' if self.not_a_piece(pos_to) else 'capture'}.png")
                    sprite.color = self.color_scheme["selection_color" if self.selected_square else "highlight_color"]
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
                if not issubclass(move.movement_type, movement.CastlingMovement):
                    while last_move.chained_move:
                        if last_move.captured_piece:
                            captures.append(last_move.captured_piece.board_pos)
                        last_move = last_move.chained_move
                    pos_to = last_move.pos_to
                if last_move.captured_piece:
                    captures.append(last_move.captured_piece.board_pos)
                if pos_from is not None and pos_from != pos_to:
                    if pos_from in move_sprites and not self.not_a_piece(pos_from):
                        move_sprites[pos_from].color = self.color_scheme["selection_color"]
                    else:
                        sprite = Sprite(f"assets/util/{'capture' if self.not_a_piece(pos_from) else 'selection'}.png")
                        sprite.color = self.color_scheme["selection_color"]
                        sprite.position = self.get_screen_position(pos_from)
                        sprite.scale = self.square_size / sprite.texture.width
                        self.move_sprite_list.append(sprite)
                if pos_to is not None:
                    if pos_to in move_sprites:
                        move_sprites[pos_to].color = self.color_scheme["selection_color"]
                    else:
                        sprite = Sprite(f"assets/util/{'capture' if self.not_a_piece(pos_to) else 'selection'}.png")
                        sprite.color = self.color_scheme["selection_color"]
                        sprite.position = self.get_screen_position(pos_to)
                        sprite.scale = self.square_size / sprite.texture.width
                        self.move_sprite_list.append(sprite)
                for capture in captures:
                    if capture == pos_to:
                        continue
                    if capture in move_sprites:
                        move_sprites[capture].color = self.color_scheme["selection_color"]
                    else:
                        sprite = Sprite(f"assets/util/{'capture' if self.not_a_piece(capture) else 'selection'}.png")
                        sprite.color = self.color_scheme["highlight_color"]
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
        if self.not_on_board(pos):
            self.highlight.color = (0, 0, 0, 0)
            self.hovered_square = None
            if (self.selected_square is None and not self.move_history) or self.promotion_piece:
                self.hide_moves()
            else:
                self.show_moves()
        else:
            self.highlight.color = self.color_scheme["highlight_color"]
            if self.hovered_square != pos:
                self.hovered_square = pos
                if self.selected_square is None and not self.promotion_piece:
                    self.show_moves()
                elif self.promotion_piece:
                    self.hide_moves()

    def update_board(self, move: Move) -> None:
        if self.en_passant_target is not None and move.piece.side == self.en_passant_target.side.opponent():
            self.clear_en_passant()

    def update_move(self, move: Move) -> None:
        move.set(piece=self.get_piece(move.pos_from))
        new_piece = move.swapped_piece or move.captured_piece
        new_piece = self.get_piece(new_piece.board_pos if new_piece is not None else move.pos_to)
        if move.piece != new_piece and not new_piece.is_empty():
            if move.swapped_piece is not None:
                move.set(swapped_piece=new_piece)
            else:
                move.set(captured_piece=new_piece)

    def mark_en_passant(self, piece_pos: Position, marker_pos: Position) -> None:
        if self.en_passant_target is not None and self.en_passant_target.board_pos != piece_pos:
            return
        self.en_passant_target = self.get_piece(piece_pos)
        self.en_passant_markers.add(marker_pos)

    def clear_en_passant(self) -> None:
        self.en_passant_target = None
        self.en_passant_markers = set()

    def update_auto_captures(self, move: Move, side: Side) -> None:
        if move.is_edit:
            return
        first_move = move
        while move.chained_move and not issubclass(
            move.chained_move.movement_type,
            movement.AutoRangedAutoCaptureRiderMovement
        ):
            move = move.chained_move
        if move.pos_to in self.auto_capture_markers[side]:
            piece_poss = self.auto_capture_markers[side][move.pos_to]
            piece_pos = sorted(list(piece_poss))[0]
            piece = self.get_piece(piece_pos)
            if piece.side == side and move.piece.side == side.opponent():
                chained_move = Move(
                    piece=piece,
                    movement_type=type(piece.movement),
                    pos_from=piece_pos,
                    pos_to=piece_pos,
                    captured_piece=move.piece,
                )
                move.chained_move = chained_move
                if first_move.promotion is not None:
                    first_move.promotion = None

    def update_promotion_auto_captures(self, move: Move) -> None:
        piece = self.get_piece(move.pos_to)
        if isinstance(piece.movement, movement.RangedAutoCaptureRiderMovement):
            piece.movement.generate_captures(move, piece)

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

    def compare_history(self) -> None:
        # check if the last move matches the first future move
        if self.future_move_history and self.move_history:  # if there are any moves to compare that is
            if (
                (self.move_history[-1] is None) == (self.future_move_history[-1] is None)
                and (self.move_history[-1] is None or self.move_history[-1].matches(self.future_move_history[-1]))
            ):
                self.future_move_history.pop()  # if it does, the other future moves are still makeable, so we keep them
            else:
                self.future_move_history = []  # otherwise, we can't redo the future moves anymore, so we clear them
                self.roll_history = self.roll_history[:self.ply_count - 1]  # and we also clear the roll history
                self.probabilistic_piece_history = self.probabilistic_piece_history[:self.ply_count - 1]

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
                NoPiece(self, move.pos_from) if move.swapped_piece is None else move.swapped_piece
            )
            self.piece_sprite_list.append(self.pieces[move.pos_from[0]][move.pos_from[1]])
        if move.captured_piece is not None and (capture_pos := move.captured_piece.board_pos) != move.pos_to:
            # piece was captured on a different square than the one the capturing piece moved to (e.g. en passant)
            # create a blank piece on the square it was captured on
            self.pieces[capture_pos[0]][capture_pos[1]] = NoPiece(self, capture_pos)
            self.piece_sprite_list.append(self.pieces[capture_pos[0]][capture_pos[1]])
        if move.piece is not None and move.pos_from is None:
            # piece was added to the board, add it to the sprite list
            self.piece_sprite_list.append(move.piece)
        if not move.is_edit or (move.pos_from == move.pos_to and move.promotion is None):
            # call movement.update() to update movement state after the move (e.g. pawn double move, castling rights)
            move.piece.movement.update(move, move.piece)

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
                    move.piece.angle = 0           # so instead we have to do it manually as a workaround
                # removed pieces don't get updated by update_hide_mode() either so we also do it manually
                if not move.piece.is_empty():
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
            # removed pieces don't get updated by update_hide_mode() either so we also do it manually
            self.update_piece(move.captured_piece)
            self.pieces[capture_pos[0]][capture_pos[1]] = move.captured_piece
            self.piece_sprite_list.append(move.captured_piece)
        if move.pos_to is not None and move.pos_from != move.pos_to:
            # piece was added on or moved to a different square, restore the piece that was there before
            if move.captured_piece is None or move.captured_piece.board_pos != move.pos_to:
                # no piece was on the square that was moved to (e.g. non-capturing move, en passant)
                # create a blank piece on that square
                self.pieces[move.pos_to[0]][move.pos_to[1]] = NoPiece(self, move.pos_to)
                self.piece_sprite_list.append(self.pieces[move.pos_to[0]][move.pos_to[1]])
            if move.swapped_piece is not None:
                # piece was swapped with another piece, move the swapped piece to the square that was moved to
                self.set_position(move.swapped_piece, move.pos_to)
                self.piece_sprite_list.append(move.swapped_piece)
                self.pieces[move.pos_to[0]][move.pos_to[1]] = move.swapped_piece
        if not move.is_edit or (move.pos_from == move.pos_to and move.promotion is None):
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
                    past.pos_from == future.pos_from and past.pos_to == future.pos_to
                    and not (past.captured_piece is not None and future.swapped_piece is not None)
                    and not (past.swapped_piece is not None and future.captured_piece is not None)
                    and future.promotion is not None
                ):
                    past.promotion = future.promotion
            if self.promotion_piece.board_pos in self.en_passant_markers:
                self.mark_en_passant(self.en_passant_target, self.promotion_piece.board_pos)
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
                self.undo(chained_move)
                self.revert_auto_capture_markers(chained_move)
                if chained_move.promotion is not None:
                    if not chained_move.piece.is_empty():
                        self.update_piece(chained_move.piece)
                logged_move = copy(chained_move)
                if in_promotion:
                    logged_move.set(promotion=Unset)
                self.log(f'''[Ply {self.ply_count}] Undo: {
                    f"{'Edit' if logged_move.is_edit else 'Move'}: " + str(logged_move)
                }''')
                in_promotion = False
        else:
            self.log(f"[Ply {self.ply_count}] Undo: Pass: {self.turn_side}'s turn")
        if self.move_history:
            move = self.move_history[-1]
            if move is not None and (not move.is_edit or (move.pos_from == move.pos_to and move.promotion is None)):
                move.piece.movement.reload(move, move.piece)
        future_move_history = self.future_move_history.copy()
        if self.chain_start is None:
            self.advance_turn()
        else:
            self.chain_start = None
            self.load_moves()
        self.chain_start = None
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
                    past.pos_from == future.pos_from and past.pos_to == future.pos_to
                    and not (past.captured_piece is not None and future.swapped_piece is not None)
                    and not (past.swapped_piece is not None and future.captured_piece is not None)
                    and future.promotion
                ):
                    past.promotion = future.promotion
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
            self.log(f"[Ply {self.ply_count}] Redo: Pass: {self.turn_side.opponent()}'s turn")
            self.clear_en_passant()
            self.move_history.append(deepcopy(last_move))
        elif piece_was_moved:
            chained_move = last_move
            while chained_move:
                self.log(f'''[Ply {self.ply_count}] Redo: {
                    f"{'Edit' if chained_move.is_edit else 'Move'}: " + str(chained_move)
                }''')
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
                self.log(f'''[Ply {self.ply_count}] Redo: {
                    f"{'Edit' if chained_move.is_edit else 'Move'}: " + str(chained_move)
                }''')
                if chained_move.is_edit and chained_move.promotion is not None:
                    if chained_move.promotion is Unset:
                        promotion_side = self.get_promotion_side(chained_move.piece)
                        self.start_promotion(chained_move.piece, self.edit_promotions[promotion_side])
                    else:
                        self.promotion_piece = True
                        self.replace(chained_move.piece, chained_move.promotion)
                        self.update_auto_capture_markers(chained_move)
                        self.update_promotion_auto_captures(chained_move)
                        self.promotion_piece = None
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
        if (
            last_chain_move is None or last_chain_move.chained_move is None
            or not self.chain_moves.get(self.turn_side, {}).get((last_chain_move.pos_from, last_chain_move.pos_to))
        ):
            self.chain_start = None
            if self.promotion_piece is None:
                self.ply_count += 1 if last_move is None else not last_move.is_edit
                self.compare_history()
            self.advance_turn()
        elif last_chain_move.chained_move is Unset:
            self.load_moves()
            self.select_piece(last_chain_move.pos_to)
            self.show_moves()

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
        if self.edit_mode:
            self.load_pieces()  # loading the new piece positions in order to update the board state
            self.color_pieces()  # reverting the piece colors to normal in case they were changed
            return  # let's not advance the turn while editing the board to hopefully make things easier for everyone
        self.turn_side = Side.WHITE if self.ply_count % 2 == 1 else Side.BLACK
        self.update_status()

    def update_status(self) -> None:
        self.load_moves()  # this updates the check status as well
        self.show_moves()
        if not sum(self.moves.get(self.turn_side, {}).values(), []):
            self.game_over = True
        if self.game_over:
            # the game has ended. let's find out who won and show it by changing piece colors
            if self.check_side:
                # the current player was checkmated, the game ends and the opponent wins
                self.log(f"[Ply {self.ply_count}] Info: Checkmate! {self.check_side.opponent()} wins.")
            else:
                # the current player was stalemated, the game ends in a draw
                self.log(f"[Ply {self.ply_count}] Info: Stalemate! It's a draw.")
        else:
            if self.check_side:
                # the game is still going, but the current player is in check
                self.log(f"[Ply {self.ply_count}] Info: {self.check_side} is in check!")
            else:
                # the game is still going and there is no check
                pass
        self.color_all_pieces()

    def start_promotion(self, piece: abc.Piece, promotions: list[Type[abc.Piece]]) -> None:
        self.hide_moves()
        self.promotion_piece = piece
        piece_pos = piece.board_pos
        side = self.get_promotion_side(piece)
        area = len(promotions)
        area_height = max(4, ceil(sqrt(area)))
        area_width = ceil(area / area_height)
        area_origin = piece_pos
        while self.not_on_board((area_origin[0] + side.direction(area_height - 1), area_origin[1])):
            area_origin = add(area_origin, side.direction((-1, 0)))
        area_origin = add(area_origin, side.direction((area_height - 1, 0)))
        area_squares = []
        col_increment = 0
        aim_left = area_origin[1] >= board_width / 2
        for col, row in product(range(area_width), range(area_height)):
            current_row = area_origin[0] + side.direction(-row)
            new_col = col + col_increment
            current_col = area_origin[1] + ((new_col + 1) // 2 * ((aim_left + new_col) % 2 * 2 - 1))
            while self.not_on_board((current_row, current_col)):
                col_increment += 1
                new_col = col + col_increment
                current_col = area_origin[1] + ((new_col + 1) // 2 * ((aim_left + new_col) % 2 * 2 - 1))
            area_squares.append((current_row, current_col))
        for promotion, pos in zip_longest(promotions, area_squares):
            background_sprite = Sprite("assets/util/square.png")
            background_sprite.color = self.color_scheme["promotion_area_color"]
            background_sprite.position = self.get_screen_position(pos)
            background_sprite.scale = self.square_size / background_sprite.texture.width
            self.promotion_area_sprite_list.append(background_sprite)
            if promotion is None:
                continue
            promotion_piece = promotion(self, pos, side)
            if issubclass(promotion, abc.RoyalPiece) and promotion not in self.piece_sets[side]:
                if self.edit_mode and self.edit_piece_set_id is not None:
                    promotion_piece.is_hidden = False
                self.update_piece(promotion_piece, asset_folder='other')
            elif not self.edit_mode or self.edit_piece_set_id is None:
                self.update_piece(promotion_piece, penultima_flip=True)
            else:
                promotion_piece.reload(is_hidden=False, flipped_horizontally=False)
            promotion_piece.scale = self.square_size / promotion_piece.texture.width
            promotion_piece.set_color(
                self.color_scheme.get(
                    f"{promotion_piece.side.key()}piece_color",
                    self.color_scheme["piece_color"]
                ),
                self.color_scheme["colored_pieces"]
            )
            self.promotion_piece_sprite_list.append(promotion_piece)
            self.promotion_area[pos] = promotion_piece

    def end_promotion(self) -> None:
        self.promotion_piece = None
        self.promotion_area = {}
        self.promotion_area_sprite_list.clear()
        self.promotion_piece_sprite_list.clear()

    def replace(
        self,
        piece: abc.Piece,
        new_piece: abc.Piece
    ) -> None:
        new_piece.board_pos = None
        new_piece = copy(new_piece)
        pos = piece.board_pos
        self.piece_sprite_list.remove(self.pieces[pos[0]][pos[1]])
        self.pieces[pos[0]][pos[1]] = new_piece
        self.set_position(new_piece, pos)
        self.update_piece(new_piece)
        new_piece.set_color(
            self.color_scheme.get(
                f"{new_piece.side.key()}piece_color",
                self.color_scheme["piece_color"]
            ),
            self.color_scheme["colored_pieces"]
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
                    self.color_scheme["piece_color"]
                ),
                self.color_scheme["colored_pieces"]
            )

    def color_all_pieces(self) -> None:
        if self.game_over:
            if self.check_side:
                self.color_pieces(
                    self.check_side,
                    self.color_scheme.get(
                        f"{self.check_side.key()}loss_color",
                        self.color_scheme["loss_color"]
                    ),
                )
                self.color_pieces(
                    self.check_side.opponent(),
                    self.color_scheme.get(
                        f"{self.check_side.opponent().key()}win_color",
                        self.color_scheme["win_color"]
                    ),
                )
            else:
                self.color_pieces(
                    Side.WHITE,
                    self.color_scheme.get(
                        f"{Side.WHITE.key()}draw_color",
                        self.color_scheme["draw_color"]
                    ),
                )
                self.color_pieces(
                    Side.BLACK,
                    self.color_scheme.get(
                        f"{Side.BLACK.key()}draw_color",
                        self.color_scheme["draw_color"]
                    ),
                )
        else:
            if self.check_side:
                self.color_pieces(
                    self.check_side,
                    self.color_scheme.get(
                        f"{self.check_side.key()}check_color",
                        self.color_scheme["check_color"]
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
            self.color_scheme["light_square_color"] = lighten(desaturate(new_colors[0], 0.11), 0.011)
            self.color_scheme["dark_square_color"] = lighten(desaturate(new_colors[1], 0.11), 0.011)
            self.color_scheme["background_color"] = darken(average(
                self.color_scheme["light_square_color"],
                self.color_scheme["dark_square_color"]
            ), 0.11 / 2)
            self.color_scheme["promotion_area_color"] = darken(self.color_scheme["background_color"], 0.11)
            self.color_scheme["highlight_color"] = saturate(self.color_scheme["promotion_area_color"], 0.11 * 2) + (80,)
            self.color_scheme["selection_color"] = self.color_scheme["highlight_color"][:3] + (120,)
            self.color_scheme["text_color"] = darken(self.color_scheme["background_color"], 0.11 * 3)
            self.color_scheme["white_piece_color"] = saturate(darken(new_colors[0], 0.11), 0.11)
            self.color_scheme["black_piece_color"] = desaturate(darken(new_colors[1], 0.11), 0.11)
            self.color_scheme["white_check_color"] = desaturate(self.color_scheme["white_piece_color"], 0.11)
            self.color_scheme["black_check_color"] = desaturate(self.color_scheme["black_piece_color"], 0.11)
            self.color_scheme["white_win_color"] = darken(self.color_scheme["white_piece_color"], 0.11)
            self.color_scheme["black_win_color"] = darken(self.color_scheme["black_piece_color"], 0.11)
            self.color_scheme["white_draw_color"] = desaturate(self.color_scheme["white_piece_color"], 0.11 * 5)
            self.color_scheme["black_draw_color"] = desaturate(self.color_scheme["black_piece_color"], 0.11 * 5)
            self.color_scheme["loss_color"] = getrgb("#bbbbbb")
        self.background_color = self.color_scheme["background_color"]
        for sprite in self.label_list:
            sprite.color = self.color_scheme["text_color"]
        for sprite in self.board_sprite_list:
            position = self.get_board_position(sprite.position)
            sprite.color = self.color_scheme[f"{'light' if self.is_light_square(position) else 'dark'}_square_color"]
        for sprite in self.promotion_area_sprite_list:
            sprite.color = self.color_scheme["promotion_area_color"]
        for sprite in self.promotion_piece_sprite_list:
            if isinstance(sprite, abc.Piece):
                sprite.set_color(
                    self.color_scheme.get(
                        f"{sprite.side.key()}piece_color",
                        self.color_scheme["piece_color"]
                    ),
                    self.color_scheme["colored_pieces"]
                )
        self.color_all_pieces()
        self.selection.color = self.color_scheme["selection_color"] if self.selection.alpha else (0, 0, 0, 0)
        self.highlight.color = self.color_scheme["highlight_color"] if self.highlight.alpha else (0, 0, 0, 0)
        self.show_moves()

    def update_piece(
        self,
        piece: abc.Piece,
        asset_folder: str | None = None,
        file_name: str | None = None,
        penultima_flip: bool = None,
        penultima_hide: bool = None,
    ) -> None:
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
        elif self.should_hide_moves is not None:
            is_hidden = self.should_hide_moves or Default
        else:
            is_hidden = bool(self.should_hide_pieces) or Default
        file_name, flip = (file_name[:-1], penultima_flip) if file_name[-1] == '|' else (file_name, False)
        piece.reload(is_hidden=is_hidden, asset_folder=asset_folder, file_name=file_name, flipped_horizontally=flip)

    def update_pieces(self) -> None:
        for piece in sum(self.movable_pieces.values(), []):
            self.update_piece(piece)
        for piece in self.promotion_piece_sprite_list:
            if isinstance(piece, abc.Piece) and not piece.is_empty():
                if isinstance(piece, abc.RoyalPiece) and type(piece) not in self.piece_sets[piece.side]:
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
        if self.hovered_square:
            self.update_highlight(self.get_board_position(self.highlight.position, old_size, old_origin, old_flip_mode))
        else:
            self.update_highlight(self.get_board_position(self.highlight.position, old_size, old_origin))
            self.hovered_square = None
        self.skip_mouse_move = True

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
                    isinstance(sprite, abc.Piece) and not sprite.is_empty()
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
            while colors[self.color_index]["scheme_type"] != "cherub":
                self.color_index += 1
                if self.color_index >= len(colors):
                    self.color_index = 0
                    break
        self.color_scheme = colors[self.color_index]
        self.update_colors()
        for sprite_list in (self.piece_sprite_list, self.promotion_piece_sprite_list, [self.active_piece]):
            for sprite in sprite_list:
                if isinstance(sprite, abc.Piece) and not sprite.is_empty():
                    sprite.angle = 0

    def resize(self, width: int, height: int):
        min_width, min_height = (self.board_width + 2) * min_size, (self.board_height + 2) * min_size
        self.set_size(max(width, min_width), max(height, min_height))

    def on_draw(self):
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

    def on_update(self, delta_time: float):
        if self.is_trickster_mode():
            self.trickster_color_delta += delta_time
            self.trickster_angle_delta += delta_time

    def on_resize(self, width: float, height: float):
        super().on_resize(width, height)
        self.update_sprites(self.flip_mode)

    def on_deactivate(self):
        self.hovered_square = None
        self.clicked_square = None
        self.held_buttons = 0
        self.highlight.alpha = 0
        self.show_moves()

    def on_mouse_press(self, x, y, buttons, modifiers) -> None:
        self.piece_was_selected = False
        if buttons & MOUSE_BUTTON_LEFT:
            self.held_buttons = MOUSE_BUTTON_LEFT
            if self.game_over and not self.edit_mode:
                return
            pos = self.get_board_position((x, y))
            if self.promotion_piece:
                if pos in self.promotion_area:
                    self.move_history[-1].set(promotion=self.promotion_area[pos])
                    self.replace(self.promotion_piece, self.promotion_area[pos])
                    self.update_auto_capture_markers(self.move_history[-1])
                    self.update_promotion_auto_captures(self.move_history[-1])
                    self.end_promotion()
                    chained_move = self.move_history[-1]
                    while chained_move:
                        self.log(
                            f"[Ply {self.ply_count}] "
                            f"{'Edit' if chained_move.is_edit else 'Move'}: "
                            f"{chained_move}"
                        )
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
                if pos not in {
                    move.pos_to for move in self.moves.get(self.turn_side, {}).get(self.selected_square, ())
                }:
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
            if self.promotion_piece:
                self.undo_last_finished_move()
                return
            if self.edit_mode:
                pos = self.get_board_position((x, y))
                if self.not_on_board(pos):
                    return
                self.square_was_clicked = True
                self.clicked_square = pos

    def on_mouse_motion(self, x, y, dx, dy) -> None:
        if not self.held_buttons:
            if self.skip_mouse_move:
                dx, dy = 0, 0
            pos = self.get_board_position((x + dx, y + dy))
            self.update_highlight(pos)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers) -> None:
        pos = self.get_board_position((x + dx, y + dy))
        self.update_highlight(pos)
        if buttons & self.held_buttons & MOUSE_BUTTON_LEFT and self.selected_square is not None:
            if self.edit_mode and modifiers & key.MOD_ACCEL:
                self.reset_position(self.get_piece(self.selected_square))
            else:
                sprite = self.get_piece(self.selected_square)
                sprite.position = x, y

    def on_mouse_release(self, x, y, buttons, modifiers) -> None:
        held_buttons = buttons & self.held_buttons
        self.held_buttons = 0
        if self.edit_mode:
            if self.promotion_piece:
                return
            pos = self.get_board_position((x, y))
            if self.not_on_board(pos):
                return
            next_selected_square = None
            move = Move(is_edit=True)
            if held_buttons & MOUSE_BUTTON_LEFT:
                if not self.selected_square:
                    return
                if pos == self.selected_square:
                    if not self.square_was_clicked:
                        self.deselect_piece()
                    self.reset_position(self.get_piece(pos))
                    return
                if modifiers & key.MOD_ACCEL:
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
                if modifiers & key.MOD_ACCEL:
                    if self.not_a_piece(pos):
                        self.deselect_piece()
                        return
                    move.set(pos_from=pos, pos_to=pos, piece=self.get_piece(pos))
                elif modifiers & key.MOD_SHIFT:
                    move.set(pos_from=pos, pos_to=pos, piece=self.get_piece(pos))
                    side = self.get_promotion_side(move.piece)
                    if len(self.edit_promotions[side]) == 1:
                        move.set(promotion=self.edit_promotions[side][0](
                            board=self,
                            board_pos=move.pos_to,
                            side=side,
                            promotions=self.promotions.get(side),
                            promotion_squares=self.promotion_squares.get(side),
                        ))
                    elif len(self.edit_promotions[side]) > 1:
                        move.set(promotion=Unset)
                        move.piece.move(move)
                        self.update_auto_capture_markers(move)
                        self.move_history.append(deepcopy(move))
                        self.start_promotion(move.piece, self.edit_promotions[side])
                        return
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
            if not self.promotion_piece:
                self.log(f"[Ply {self.ply_count}] Edit: {self.move_history[-1]}")
                self.compare_history()
            self.advance_turn()
            if next_selected_square:
                self.select_piece(next_selected_square)
            return
        if held_buttons & MOUSE_BUTTON_RIGHT:
            self.deselect_piece()
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
                    self.deselect_piece()
                    return
                self.update_move(move)
                if move.promotion is not None:
                    move.promotion = Unset  # do not auto-promote because we are selecting promotion type manually
                if (
                    (move.chained_move or self.chain_moves.get(self.turn_side, {}).get((move.pos_from, move.pos_to)))
                    and not issubclass(
                        move.movement_type,
                        movement.CastlingMovement |
                        movement.RangedAutoCaptureRiderMovement
                    )
                ):
                    move.chained_move = Unset  # do not chain moves because we are selecting chained move manually
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
                if move.chained_move is Unset and not self.promotion_piece:
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

    def on_key_press(self, symbol, modifiers):
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
            self.hovered_square = None
        if symbol == key.TAB:  # Next piece
            start_row, start_col = self.get_board_position(self.highlight.position)
            side = self.turn_side.opponent() if modifiers & key.MOD_ACCEL else self.turn_side
            direction = -1 if (modifiers & key.MOD_SHIFT) == (side == Side.WHITE) else 1
            if not self.selected_square:
                positions = {piece.board_pos for piece in self.movable_pieces[side]}
            elif not self.edit_mode:
                positions = {move.pos_to for move in self.moves.get(self.turn_side, {}).get(self.selected_square, {})}
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
                        self.hovered_square = None
                        return
        if self.held_buttons:
            return
        if symbol == key.S and modifiers & key.MOD_ACCEL:  # Save
            self.save_board(2 if modifiers & key.MOD_SHIFT else None)
        if symbol == key.R:  # Restart
            if modifiers & key.MOD_SHIFT:  # Randomize piece sets
                blocked_ids = set(self.board_config['block_ids'])
                piece_set_ids = list(i for i in range(len(piece_groups)) if i not in blocked_ids)
                if modifiers & key.MOD_ACCEL:  # Randomize piece sets (same for both sides)
                    self.log(f"[Ply {self.ply_count}] Info: Starting new game (with a random piece set)")
                    piece_set_ids = self.set_rng.sample(piece_set_ids, k=1)
                    self.piece_set_ids = {side: piece_set_ids[0] for side in self.piece_set_ids}
                else:  # Randomize piece sets (different for each side)
                    self.log(f"[Ply {self.ply_count}] Info: Starting new game (with random piece sets)")
                    piece_set_ids = self.set_rng.sample(piece_set_ids, k=len(self.piece_set_ids))
                    self.piece_set_ids = {side: set_id for side, set_id in zip(self.piece_set_ids, piece_set_ids)}
                self.chaos_mode = 0
                self.reset_board(update=True)
            elif modifiers & key.MOD_ACCEL:  # Restart with the same piece sets
                self.log(f"[Ply {self.ply_count}] Info: Starting new game")
                self.reset_board()
        if symbol == key.C:
            if modifiers & (key.MOD_SHIFT | key.MOD_ALT):  # Chaos mode
                self.load_chaos_sets(1 + bool(modifiers & key.MOD_ALT), modifiers & key.MOD_ACCEL)
            elif modifiers & key.MOD_ACCEL:  # Config
                self.save_config()
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
                    self.roll_history = self.roll_history[:self.ply_count - 1]
                    self.probabilistic_piece_history = self.probabilistic_piece_history[:self.ply_count - 1]
                    self.log(f"[Ply {self.ply_count}] Info: Probabilistic pieces updated")
                    self.advance_turn()
        if symbol == key.F11:  # Full screen (toggle)
            self.set_fullscreen(not self.fullscreen)
        if symbol == key.MINUS:  # (-) Decrease window size
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
        if symbol == key.EQUAL:  # (+) Increase window size
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
            self.resize((self.board_width + 2) * default_size, (self.board_height + 2) * default_size)
        if symbol == key.E:
            if modifiers & key.MOD_SHIFT:  # Empty board
                self.empty_board()
            if modifiers & key.MOD_ACCEL:  # Edit mode (toggle)
                self.edit_mode = not self.edit_mode
                self.log(f"[Ply {self.ply_count}] Mode: {'EDIT' if self.edit_mode else 'PLAY'}")
                self.deselect_piece()
                self.hide_moves()
                self.advance_turn()
                if self.edit_mode:
                    self.moves = {side: {} for side in self.moves}
                    self.chain_moves = {side: {} for side in self.chain_moves}
                    self.theoretical_moves = {side: {} for side in self.theoretical_moves}
                    self.show_moves()
        if symbol == key.W:  # White
            if modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:  # White is in control
                if self.turn_side != Side.WHITE and not self.chain_start:
                    self.move_history.append(None)
                    self.log(f"[Ply {self.ply_count}] Pass: {Side.WHITE}'s turn")
                    self.ply_count += 1
                    self.clear_en_passant()
                    self.compare_history()
                    self.advance_turn()
            elif modifiers & key.MOD_SHIFT:  # Shift white piece set
                d = -1 if modifiers & key.MOD_ACCEL else 1
                self.piece_set_ids[Side.WHITE] = (
                    (self.piece_set_ids[Side.WHITE] + len(self.chaos_sets) + d)
                    % (len(piece_groups) + len(self.chaos_sets))
                    - len(self.chaos_sets)
                ) if self.piece_set_ids[Side.WHITE] is not None else 0
                self.reset_board(update=True)
        if symbol == key.B:  # Black
            if modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:  # Black is in control
                if self.turn_side != Side.BLACK and not self.chain_start:
                    self.move_history.append(None)
                    self.log(f"[Ply {self.ply_count}] Pass: {Side.BLACK}'s turn")
                    self.ply_count += 1
                    self.clear_en_passant()
                    self.compare_history()
                    self.advance_turn()
            elif modifiers & key.MOD_SHIFT:  # Shift black piece set
                d = -1 if modifiers & key.MOD_ACCEL else 1
                self.piece_set_ids[Side.BLACK] = (
                    (self.piece_set_ids[Side.BLACK] + len(self.chaos_sets) + d)
                    % (len(piece_groups) + len(self.chaos_sets))
                    - len(self.chaos_sets)
                ) if self.piece_set_ids[Side.BLACK] is not None else 0
                self.reset_board(update=True)
        if symbol == key.N:  # Next
            if modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT and not self.chain_start:  # Next player
                self.move_history.append(None)
                self.log(f"[Ply {self.ply_count}] Pass: {self.turn_side.opponent()}'s turn")
                self.ply_count += 1
                self.clear_en_passant()
                self.compare_history()
                self.advance_turn()
            elif modifiers & key.MOD_SHIFT:
                if self.piece_set_ids[Side.WHITE] == self.piece_set_ids[Side.BLACK]:  # Next piece set
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
                else:  # Next player goes first
                    for data in (self.piece_sets, self.piece_set_ids, self.piece_set_names):
                        data[Side.WHITE], data[Side.BLACK] = data[Side.BLACK], data[Side.WHITE]
                self.reset_board(update=True)
        if symbol == key.P:  # Promotion
            if self.edit_mode:
                old_id = self.edit_piece_set_id
                if modifiers & key.MOD_SHIFT:  # Shift promotion piece set
                    if self.edit_piece_set_id is not None:
                        d = -1 if modifiers & key.MOD_ACCEL else 1
                        self.edit_piece_set_id = (self.edit_piece_set_id + d) % len(piece_groups)
                    else:
                        self.edit_piece_set_id = 0
                elif modifiers & key.MOD_ACCEL:  # Reset promotion piece set
                    self.edit_piece_set_id = None
                if old_id != self.edit_piece_set_id:
                    self.reset_edit_promotions()
                    if self.promotion_piece:
                        promotion_piece = self.promotion_piece
                        promotion_side = self.get_promotion_side(promotion_piece)
                        self.end_promotion()
                        self.start_promotion(promotion_piece, self.edit_promotions[promotion_side])
        if symbol == key.O:  # Royal pieces
            old_mode = self.royal_piece_mode
            if modifiers & key.MOD_SHIFT:  # Force royal mode (Shift: all quasi-royal, Ctrl+Shift: all royal)
                self.royal_piece_mode = 1 if modifiers & key.MOD_ACCEL else 2
            elif modifiers & key.MOD_ACCEL:  # Default
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
                self.future_move_history = []  # we don't know if we can redo the future moves anymore, so we clear them
                self.advance_turn()
        if symbol == key.F:
            if modifiers & key.MOD_ACCEL:  # Flip
                self.flip_board()
            elif modifiers & key.MOD_SHIFT:  # Fast-forward
                while self.future_move_history:
                    self.redo_last_move()
        if symbol == key.G and not self.is_trickster_mode():  # Graphics
            old_color_index = self.color_index
            if modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:  # Graphics reset
                self.color_index = 0
            elif modifiers & key.MOD_SHIFT:  # Graphics shift
                if self.color_index is None:
                    self.color_index = 0
                else:
                    self.color_index = (self.color_index + (-1 if modifiers & key.MOD_ACCEL else 1)) % len(colors)
            if old_color_index != self.color_index:
                self.color_scheme = colors[self.color_index]
                self.update_colors()
        if symbol == key.H:  # Hide
            old_should_hide_pieces = self.should_hide_pieces
            if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Show
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
        if symbol == key.M:  # Moves
            old_should_hide_moves = self.should_hide_moves
            if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Default
                self.should_hide_moves = None
            elif modifiers & key.MOD_SHIFT:  # Hide
                self.should_hide_moves = True
            elif modifiers & key.MOD_ACCEL:  # Show
                self.should_hide_moves = False
            if old_should_hide_moves != self.should_hide_moves:
                if self.should_hide_moves is None:
                    self.log(f"[Ply {self.ply_count}] Info: Move markers default to piece visibility")
                elif self.should_hide_moves is False:
                    self.log(f"[Ply {self.ply_count}] Info: Move markers default to shown")
                elif self.should_hide_moves is True:
                    self.log(f"[Ply {self.ply_count}] Info: Move markers default to hidden")
                else:
                    self.should_hide_moves = old_should_hide_moves
                self.update_pieces()
                self.show_moves()
        if symbol == key.K:  # Move markers
            selected_square = self.selected_square
            if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Default
                self.load_moves(False)
            elif modifiers & key.MOD_ACCEL:  # Valid moves
                self.load_moves(False, Side.ANY, Side.NONE)
            elif modifiers & key.MOD_SHIFT:  # Theoretical moves
                self.load_moves(False, Side.NONE, Side.ANY)
            if selected_square:
                self.select_piece(selected_square)
            self.show_moves()
        if symbol == key.T and modifiers & key.MOD_ACCEL:  # Trickster mode
            if self.color_scheme["scheme_type"] == "cherub":
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
        if symbol == key.L:  # Log
            if modifiers & key.MOD_ACCEL:  # Save log
                self.save_log()
            if modifiers & key.MOD_SHIFT:  # Clear log
                self.clear_log()
        if symbol == key.D:  # Debug
            debug_log_data = self.debug_info()
            if modifiers & key.MOD_ACCEL:  # Save debug info
                self.save_log(debug_log_data, "debug")
            if modifiers & key.MOD_SHIFT:  # Print debug info
                for string in debug_log_data:
                    print(f"[Debug] {string}")
        if symbol == key.SLASH:  # (?) Random
            if self.edit_mode:
                return
            moves = self.unique_moves()[self.turn_side]
            if modifiers & key.MOD_SHIFT:  # Random piece
                self.deselect_piece()
                if moves:
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

    def on_key_release(self, symbol: int, modifiers: int):
        if symbol == key.ENTER:  # Simulate LMB
            self.on_mouse_release(
                round(self.highlight.center_x), round(self.highlight.center_y),  MOUSE_BUTTON_LEFT, modifiers
            )
        if symbol == key.BACKSPACE:  # Simulate RMB
            self.on_mouse_release(
                round(self.highlight.center_x), round(self.highlight.center_y),  MOUSE_BUTTON_RIGHT, modifiers
            )

    def log(self, string: str) -> None:
        self.log_data.append(string)
        print(string)

    def save_log(
            self,
            log_data: list[str] | None = None,
            log_name: str = "log"
    ) -> None:
        if not log_data:
            log_data = self.log_data
        if log_data:
            with open(get_filename(log_name, 'txt'), "w") as log_file:
                log_file.write("\n".join(log_data))

    def clear_log(self, console: bool = True, file: bool = False) -> None:
        self.log(f"[Ply {self.ply_count}] Info: Log cleared")
        if file:
            self.log_data.clear()
        if console:
            system("cls" if os_name == "nt" else "clear")

    def save_config(self) -> None:
        config = Config(config_path)
        config['color_id'] = self.color_index
        config['white_id'] = self.piece_set_ids[Side.WHITE]
        config['black_id'] = self.piece_set_ids[Side.BLACK]
        config['edit_id'] = self.edit_piece_set_id
        config['hide_pieces'] = self.should_hide_pieces
        config['hide_moves'] = self.should_hide_moves
        config['royal_mode'] = self.royal_piece_mode
        config['set_seed'] = self.set_seed
        config['roll_seed'] = self.roll_seed
        config['chaos_seed'] = self.chaos_seed
        config['chaos_mode'] = self.chaos_mode
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
            side: '-' * digits if set_id is None else f"{set_id:0{digits}d}"
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
            debug_log_data.append(f"{side} quasiroyal pieces ({len(self.quasi_royal_pieces[side])}):")
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
            piece_list = ', '.join(piece.name for piece in self.promotions[side])
            debug_log_data.append(
                f"{side} promotions ({len(self.promotions[side])}): {piece_list if piece_list else 'None'}"
            )
            piece_list = ', '.join(piece.name for piece in self.edit_promotions[side])
            debug_log_data.append(
                f"{side} replacements ({len(self.edit_promotions[side])}): {piece_list if piece_list else 'None'}"
            )
        piece_modes = {0: 'Shown', 1: 'Hidden', 2: 'Penultima'}
        debug_log_data.append(f"Hide pieces: {self.should_hide_pieces} - {piece_modes[self.should_hide_pieces]}")
        move_modes = {None: 'Default', False: 'Shown', True: 'Hidden'}
        debug_log_data.append(f"Hide moves: {self.should_hide_moves} - {move_modes[self.should_hide_moves]}")
        royal_modes = {0: 'Default', 1: 'Force royal (Threaten Any)', 2: 'Force quasi-royal (Threaten Last)'}
        debug_log_data.append(f"Royal mode: {self.royal_piece_mode} - {royal_modes[self.royal_piece_mode]}")
        chaos_modes = {
            0: 'Off',
            1: 'Chaos (Matching Pieces)',
            2: 'Chaos (Matching Pieces), Asymmetrical',
            3: 'Extreme Chaos (Any Pieces)',
            4: 'Extreme Chaos (Any Pieces), Asymmetrical'
        }
        debug_log_data.append(f"Chaos mode: {self.chaos_mode} - {chaos_modes[self.chaos_mode]}")
        debug_log_data.append(f"Board mode: {'Edit' if self.edit_mode else 'Play'}")
        debug_log_data.append(f"Turn side: {self.turn_side if self.turn_side else 'None'}")
        debug_log_data.append(f"Current ply: {self.ply_count}")
        debug_log_data.append(f"Moves possible: {len(sum(self.moves[self.turn_side].values(), []))}")
        debug_log_data.append(f"Unique moves: {sum(len(i) for i in self.unique_moves()[self.turn_side].values())}")
        debug_log_data.append(f"Check side: {self.check_side if self.check_side else 'None'}")
        debug_log_data.append(f"Game over: {self.game_over}")
        debug_log_data.append(f"Action history ({len(self.move_history)}):")
        for i, move in enumerate(self.move_history):
            if not move:
                debug_log_data.append(f"  {i}: (Pass) None")
            else:
                debug_log_data.append(f"  {i}: ({'Edit' if move.is_edit else 'Move'}) {move}")
                j = 0
                while move.chained_move:
                    move = move.chained_move
                    j += 1
                    debug_log_data.append(f"  {i}.{j}: ({'Edit' if move.is_edit else 'Move'}) {move}")
        if not self.move_history:
            debug_log_data[-1] += " None"
        debug_log_data.append(f"Future action history ({len(self.future_move_history)}):")
        for i, move in enumerate(self.future_move_history[::-1], len(self.move_history)):
            if not move:
                debug_log_data.append(f"  {i}: (Pass) None")
            else:
                debug_log_data.append(f"  {i}: ({'Edit' if move.is_edit else 'Move'}) {move}")
                j = 0
                while move.chained_move:
                    move = move.chained_move
                    j += 1
                    debug_log_data.append(f"  {i}.{j}: ({'Edit' if move.is_edit else 'Move'}) {move}")
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
        pass
