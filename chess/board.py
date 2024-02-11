from copy import copy, deepcopy
from datetime import datetime
from itertools import product, zip_longest
from math import ceil, sqrt
from os import curdir, name as os_name, system
from os.path import abspath, join
from random import choice, randrange
from typing import Type

from PIL.ImageColor import getrgb
from arcade import key, MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT, Text
from arcade import Sprite, SpriteList, Window
from arcade import start_render

from chess.color import colors, trickster_colors
from chess.color import average, darken, desaturate, lighten, saturate
from chess.movement import movement
from chess.movement.move import Move
from chess.movement.util import Position, add
from chess.pieces import pieces as abc
from chess.pieces.groups import classic as fide
from chess.pieces.groups import amazon as am, amontillado as ao, avian as av
from chess.pieces.groups import backward as bw, beast as bs, breakfast as bk, burn as br, buzz as bz
from chess.pieces.groups import camel as ca, cannon as cn, color as co, colorbound as cb
from chess.pieces.groups import crash as cs, crook as cr, cylindrical as cy
from chess.pieces.groups import demirifle as de, drip as dr
from chess.pieces.groups import fairy as fa, fizz as fi, fly as fl, forward as fw
from chess.pieces.groups import horse as hs
from chess.pieces.groups import inadjacent as ia, iron as ir
from chess.pieces.groups import knight as kn
from chess.pieces.groups import mash as ms
from chess.pieces.groups import narrow as na, nocturnal as no
from chess.pieces.groups import pawn as pa, perimeter as pe, pizza as pz, probable as pr
from chess.pieces.groups import rookie as rk
from chess.pieces.groups import starbound as st, stone as so, switch as sw
from chess.pieces.groups import thrash as th
from chess.pieces.groups import wide as wd
from chess.pieces.groups import zebra as zb
from chess.pieces.groups.util import NoPiece
from chess.pieces.pieces import Side

piece_groups = [
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
        'name': "Amazing Armada",
        'set': [am.Cannon, am.Camel, am.NightRdr, am.Amazon, fide.King, am.NightRdr, am.Camel, am.Cannon],
    },
    {
        'name': "Amontillado Arbiters",
        'set': [ao.Hasdrubal, ao.Barcfil, ao.Bed, ao.Hamilcar, fide.King, ao.Bed, ao.Barcfil, ao.Hasdrubal],
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
        'name': "Inadjacent Intimidators",
        'set': [ia.Bireme, ia.Tigon, ia.Bicycle, ia.Biplane, fide.King, ia.Bicycle, ia.Tigon, ia.Bireme],
    },
    {
        'name': "Irritant Irons",
        'set': [ir.Musth, ir.Officer, ir.SilverRdr, ir.GoldRdr, fide.King, ir.SilverRdr, ir.Officer, ir.Musth],
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

pawn_row = [fide.Pawn] * board_width
empty_row = [NoPiece] * board_width

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

movements = []

base_dir = abspath(curdir)

invalid_chars = ':<>|"?*'
invalid_chars_trans_table = str.maketrans(invalid_chars, '_' * len(invalid_chars))


class Board(Window):

    def __init__(self):
        # super boring initialization stuff (bluh bluh)
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

        self.log_data = []  # list of presently logged strings
        self.color_index = 0  # index of the current color scheme
        self.color_scheme = colors[self.color_index]  # current color scheme
        self.background_color = self.color_scheme["background_color"]  # background color
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
        self.turn_side = Side.WHITE  # side whose turn it is
        self.check_side = Side.NONE  # side that is currently in check
        self.castling_threats = set()  # squares that are attacked in a way that prevents castling
        self.should_hide_pieces = 0  # 0: don't hide, 1: hide all pieces, 2: penultima mode
        self.should_hide_moves = None  # whether to hide the move markers; None defaults to should_hide_pieces
        self.flip_mode = False  # whether the board is flipped
        self.edit_mode = False  # allows to edit the board position if set to True
        self.game_over = False  # act 6 act 6 intermission 3 (game over)
        self.trickster_color_index = 0  # hey wouldn't it be funny if there was an easter egg here
        self.trickster_color_delta = 0  # but it's not like that's ever going to happen right
        self.trickster_angle_delta = 0  # this is just a normal chess game after all
        self.pieces = []  # list of pieces on the board
        self.piece_sets = {Side.WHITE: 0, Side.BLACK: 0}  # piece sets to use for each side
        self.promotions = {Side.WHITE: [], Side.BLACK: []}  # types of pieces each side promote to
        self.edit_promotions = {Side.WHITE: [], Side.BLACK: []}  # types of pieces each side can promote to in edit mode
        self.movable_pieces = {Side.WHITE: [], Side.BLACK: []}  # pieces that can be moved by each side
        self.royal_pieces = {Side.WHITE: [], Side.BLACK: []}  # these have to stay on the board and should be protected
        self.quasi_royal_pieces = {Side.WHITE: [], Side.BLACK: []}  # at least one of these has to stay on the board
        self.probabilistic_pieces = {Side.WHITE: [], Side.BLACK: []}  # pieces that can move probabilistically
        self.penultima_pieces = {}  # piece textures that are used for penultima mode
        self.moves = {}  # dictionary of valid moves from any square that has a movable piece on it
        self.chain_moves = {}  # dictionary of valid moves that can be chained from a specific move (marked as from/to)
        self.chain_start = None  # move that started the current chain (if any)
        self.theoretical_moves = {}  # dictionary of theoretical moves from any square that has an opposing piece on it
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
        self.reset_board(update=True)

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

    def reset_board(self, update: bool = False) -> None:
        self.deselect_piece()  # you know, just in case
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

        self.log(
            f"[Ply {self.ply_count}] Game: "
            f"{piece_groups[self.piece_sets[Side.WHITE]]['name'] if not self.should_hide_pieces else '???'} vs. "
            f"{piece_groups[self.piece_sets[Side.BLACK]]['name'] if not self.should_hide_pieces else '???'}"
        )
        self.ply_count += 1

        piece_sets = {}
        for side in self.piece_sets:
            piece_group = piece_groups[self.piece_sets[side]]
            piece_sets[side] = piece_group.get(f"set_{side.key_name()[0]}", piece_group.get('set', [])).copy()

        if update:
            self.roll_history = []
            self.future_move_history = []
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
            self.penultima_pieces = {}
            for side in self.piece_sets:
                for i, piece in enumerate(piece_sets[side]):
                    if penultima_textures[i]:
                        self.penultima_pieces[piece] = penultima_textures[i]
        else:
            self.future_move_history += self.move_history[::-1]

        if not self.move_history and self.roll_history:
            self.roll_history = []
            self.future_move_history = []

        self.move_history = []

        self.pieces = []

        for row in range(self.board_height):
            self.pieces += [[]]

        for row, col in product(range(self.board_height), range(self.board_width)):
            piece_type = types[row][col]
            piece_side = sides[row][col]
            if isinstance(piece_type, abc.Side):
                piece_type = piece_sets[piece_side][col]
            self.pieces[row].append(
                piece_type(
                    self, (row, col), piece_side,
                    promotions=self.promotions[piece_side],
                    promotion_squares=promotion_squares[piece_side],
                )
                if issubclass(piece_type, abc.PromotablePiece) else
                piece_type(
                    self, (row, col), piece_side
                )
            )
            self.update_piece(self.pieces[row][col])
            self.pieces[row][col].set_color(
                self.color_scheme.get(
                    f"{self.pieces[row][col].side.key_name()}piece_color",
                    self.color_scheme["piece_color"]
                ),
                self.color_scheme["colored_pieces"]
            )
            self.pieces[row][col].scale = self.square_size / self.pieces[row][col].texture.width
            self.piece_sprite_list.append(self.pieces[row][col])

        self.load_all_moves()
        self.show_moves()

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
        return NoPiece(self, pos, Side.NONE) if self.not_on_board(pos) else self.pieces[pos[0]][pos[1]]

    def get_side(self, pos: Position | None) -> Side:
        return self.get_piece(pos).side

    def not_on_board(self, pos: Position | None) -> bool:
        return pos is None or pos[0] < 0 or pos[0] >= self.board_height or pos[1] < 0 or pos[1] >= self.board_width

    def not_a_piece(self, pos: Position | None) -> bool:
        return self.get_piece(pos).is_empty()

    def nothing_selected(self) -> bool:
        return self.not_a_piece(self.selected_square)

    def find_move(self, pos_from: Position, pos_to: Position) -> Move | None:
        for move in self.moves.get(pos_from, ()):
            if move.pos_from == move.pos_to:
                if move.captured_piece is None and pos_to == move.pos_to:
                    return copy(move)
                if move.captured_piece is not None and pos_to == move.captured_piece.board_pos:
                    return copy(move)
            elif pos_to == move.pos_to:
                return copy(move)
        return None

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

    def show_moves(self) -> None:
        self.hide_moves()
        move_sprites = dict()
        pos = self.selected_square or self.hovered_square or self.get_board_position(self.highlight.position)
        if not self.not_on_board(pos):
            piece = self.get_piece(pos)
            if not piece.is_empty() and not piece.is_hidden:
                theoretical = piece.side == self.turn_side.opponent()
                move_dict = self.theoretical_moves if theoretical else self.moves
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
                pos_from = move.pos_from
                if not isinstance(move.movement, movement.CastlingMovement):
                    while move.chained_move:
                        move = move.chained_move
                capture = move.captured_piece
                pos_to = capture.board_pos if move.pos_from == move.pos_to and capture is not None else move.pos_to
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
                    self.end_promotion()
                    self.log(
                        f"[Ply {self.ply_count}] "
                        f"{'Edit' if self.move_history[-1].is_edit else 'Move'}: "
                        f"{self.move_history[-1]}"
                    )
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
                if pos not in {move.pos_to for move in self.moves.get(self.selected_square, ())}:
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
                    side = self.get_side(pos)
                    if not side:
                        side = Side.WHITE if pos[0] < self.board_height / 2 else Side.BLACK
                        move.piece.side = side
                    if len(self.edit_promotions[side]) == 1:
                        move.set(promotion=self.edit_promotions[side][0])
                    elif len(self.edit_promotions[side]) > 1:
                        move.set(promotion=True)
                        move.piece.move(move)
                        self.move_history.append(move)
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
            self.move_history.append(move)
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
                    move.promotion = True  # do not auto-promote because we are selecting promotion type manually
                if (
                    (move.chained_move or self.chain_moves.get((move.pos_from, move.pos_to)))
                    and not isinstance(move.movement, movement.CastlingMovement)
                ):
                    move.chained_move = None  # do not chain moves because we are selecting chained move manually
                chained_move = move
                while chained_move:
                    chained_move.piece.move(chained_move)
                    if self.promotion_piece is None:
                        self.log(f"[Ply {self.ply_count}] Move: {chained_move}")
                    chained_move = chained_move.chained_move
                if self.chain_start is None:
                    self.chain_start = move
                    self.move_history.append(self.chain_start)
                else:
                    last_move = self.chain_start
                    while last_move.chained_move:
                        last_move = last_move.chained_move
                    last_move.chained_move = move
                if move.chained_move is None:
                    self.load_all_moves()
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

    def update_move(self, move: Move) -> None:
        move.set(piece=self.get_piece(move.pos_from))
        new_piece = move.swapped_piece or move.captured_piece
        new_piece = self.get_piece(new_piece.board_pos if new_piece is not None else move.pos_to)
        if move.piece != new_piece and not new_piece.is_empty():
            if move.swapped_piece is not None:
                move.set(swapped_piece=new_piece)
            else:
                move.set(captured_piece=new_piece)

    def set_position(self, piece: abc.Piece, pos: Position) -> None:
        piece.board_pos = pos
        piece.position = self.get_screen_position(pos)

    def reset_position(self, piece: abc.Piece) -> None:
        self.set_position(piece, piece.board_pos)

    def move(self, move: Move) -> None:
        self.deselect_piece()
        if move.piece is not None and move.pos_to is not None:
            self.set_position(move.piece, move.pos_to)
        if move.swapped_piece is not None:
            self.set_position(move.swapped_piece, move.pos_from)
        if move.piece is not None and move.pos_to is None:
            self.piece_sprite_list.remove(move.piece)
        if move.pos_to is not None and move.pos_from != move.pos_to:
            self.piece_sprite_list.remove(self.pieces[move.pos_to[0]][move.pos_to[1]])
            self.pieces[move.pos_to[0]][move.pos_to[1]] = move.piece
        if move.captured_piece is not None and move.captured_piece.board_pos != move.pos_to:
            self.piece_sprite_list.remove(move.captured_piece)
        if move.pos_from is not None and move.pos_from != move.pos_to:
            self.pieces[move.pos_from[0]][move.pos_from[1]] = (
                NoPiece(self, move.pos_from) if move.swapped_piece is None else move.swapped_piece
            )
            self.piece_sprite_list.append(self.pieces[move.pos_from[0]][move.pos_from[1]])
        if move.captured_piece is not None and (capture_pos := move.captured_piece.board_pos) != move.pos_to:
            self.pieces[capture_pos[0]][capture_pos[1]] = NoPiece(self, capture_pos)
            self.piece_sprite_list.append(self.pieces[capture_pos[0]][capture_pos[1]])
        if move.piece is not None and move.pos_from is None:
            self.piece_sprite_list.append(move.piece)
        if not move.is_edit or (move.pos_from == move.pos_to and move.promotion is None):
            (move.piece or move).movement.update(move, move.piece)

    def update_board(self, move: Move) -> None:
        if self.en_passant_target is not None and move.piece.side == self.en_passant_target.side.opponent():
            self.clear_en_passant()

    def undo(self, move: Move) -> None:
        if move.pos_from != move.pos_to or move.promotion is not None:
            # piece was added, moved, removed, or promoted
            if move.pos_from is not None:
                # existing piece was moved, empty the square it moved from and restore its position
                self.set_position(move.piece, move.pos_from)
                self.piece_sprite_list.remove(self.pieces[move.pos_from[0]][move.pos_from[1]])
            if move.pos_to is not None and move.pos_from != move.pos_to:
                # piece was placed on a different square, empty that square
                self.piece_sprite_list.remove(self.pieces[move.pos_to[0]][move.pos_to[1]])
            if move.pos_to is None or move.promotion is not None:
                # existing piece was removed from the board (possibly promoted to a different piece type)
                if self.is_trickster_mode(False):  # reset_trickster_mode() does not reset removed pieces
                    move.piece.angle = 0           # so instead we have to do it manually as a workaround
            if move.pos_from is not None:
                # existing piece was moved, restore it on the square it moved from
                self.pieces[move.pos_from[0]][move.pos_from[1]] = move.piece
                self.piece_sprite_list.append(move.piece)
        if move.captured_piece is not None:
            # piece was captured, restore it on the square it was captured from
            capture_pos = move.captured_piece.board_pos
            if capture_pos != move.pos_to:
                # piece was captured from a different square than the one the capturing piece moved to (e.g. en passant)
                # empty the square it was captured from (it was not emptied earlier because it was not the one moved to)
                self.piece_sprite_list.remove(self.pieces[capture_pos[0]][capture_pos[1]])
            self.reset_position(move.captured_piece)
            if self.is_trickster_mode(False):  # reset_trickster_mode() does not reset removed pieces
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
            (move.piece or move).movement.undo(move, move.piece)

    def undo_last_move(self) -> None:
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
            past = self.move_history[-1]
            if not past.is_edit:
                self.turn_side = self.turn_side.opponent()
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
                logged_move = copy(chained_move)
                if in_promotion:
                    logged_move.set(promotion=True)
                self.log(f'''[Ply {self.ply_count}] Undo: {
                    f"{'Edit' if logged_move.is_edit else 'Move'}: " + str(logged_move)
                }''')
                in_promotion = False
            if last_move.promotion is True:
                if last_move.piece.is_empty():
                    last_move.piece.side = Side.NONE
            if last_move.is_edit:
                if not self.edit_mode:
                    self.turn_side = self.turn_side.opponent()
        else:
            self.log(f"[Ply {self.ply_count}] Undo: Pass: {self.turn_side.name()}'s turn")
        if self.move_history:
            move = self.move_history[-1]
            if move is not None and (not move.is_edit or (move.pos_from == move.pos_to and move.promotion is None)):
                (move.piece or move).movement.reload(move, move.piece)
        future_move_history = self.future_move_history.copy()
        if self.chain_start is None:
            self.advance_turn()
        else:
            self.chain_start = None
            self.load_all_moves()
        self.chain_start = None
        self.future_move_history = future_move_history
        self.future_move_history.append(last_move)

    def redo_last_move(self) -> None:
        piece_was_moved = False
        if self.promotion_piece is not None:
            if self.move_history and self.future_move_history:
                past, future = self.move_history[-1], self.future_move_history[-1]
                if (
                    past.pos_from == future.pos_from and past.pos_to == future.pos_to
                    and not (past.captured_piece is not None and future.swapped_piece is not None)
                    and not (past.swapped_piece is not None and future.captured_piece is not None)
                    and future.promotion is not None
                ):
                    past.promotion = future.promotion
                    self.replace(self.promotion_piece, future.promotion)
                    self.end_promotion()
                else:
                    return
            else:
                return
            piece_was_moved = True
        if not self.future_move_history:
            return
        last_move = copy(self.future_move_history[-1])
        last_chain_move = last_move
        if last_move is None:
            self.log(f"[Ply {self.ply_count}] Redo: Pass: {self.turn_side.opponent().name()}'s turn")
            self.clear_en_passant()
            self.move_history.append(last_move)
        elif piece_was_moved:
            self.log(f'''[Ply {self.ply_count}] Redo: {
            f"{'Edit' if last_move.is_edit else 'Move'}: " + str(last_move)
            }''')
        else:
            if last_move.pos_from is not None:
                self.update_move(last_move)
                self.update_move(self.future_move_history[-1])
                side = self.get_side(last_move.pos_from)
                if not side:
                    side = Side.WHITE if last_move.pos_from[0] < self.board_height / 2 else Side.BLACK
                    last_move.piece.side = side
            chained_move = last_move
            history_move = self.future_move_history[-1]
            while chained_move:
                chained_move = copy(chained_move)
                chained_move.piece.move(chained_move)
                self.log(f'''[Ply {self.ply_count}] Redo: {
                f"{'Edit' if chained_move.is_edit else 'Move'}: " + str(chained_move)
                }''')
                last_chain_move = chained_move
                if chained_move:
                    chained_move = chained_move.chained_move
                if history_move:
                    history_move = history_move.chained_move
                if chained_move:
                    self.update_move(chained_move)
                if history_move:
                    self.update_move(history_move)
            if not isinstance(last_move.piece, abc.PromotablePiece) and last_move.promotion is not None:
                if last_move.promotion is True:
                    self.start_promotion(last_move.piece, self.edit_promotions[last_move.piece.side])
                else:
                    self.replace(last_move.piece, last_move.promotion)
            self.move_history.append(last_move)
        # do not pop move from future history because compare_history() will do it for us
        if last_move is not None and last_move.is_edit and not self.edit_mode:
            self.turn_side = self.turn_side.opponent()
        if (
            last_chain_move is None or last_chain_move.chained_move is False
            or not self.chain_moves.get((last_chain_move.pos_from, last_chain_move.pos_to))
        ):
            if self.promotion_piece is None:
                self.ply_count += 1 if last_move is None else not last_move.is_edit
                self.compare_history()
            self.advance_turn()
        elif last_chain_move.chained_move is None:
            self.load_all_moves()
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

    def start_promotion(self, piece: abc.Piece, promotions: list[Type[abc.Piece]]) -> None:
        if not self.edit_mode and not (isinstance(piece, abc.PromotablePiece) and promotions):
            return
        self.hide_moves()
        self.promotion_piece = piece
        piece_pos = piece.board_pos
        area = len(promotions)
        area_height = max(4, ceil(sqrt(area)))
        area_width = ceil(area / area_height)
        area_origin = piece_pos
        while self.not_on_board((area_origin[0] + piece.side.direction(area_height - 1), area_origin[1])):
            area_origin = add(area_origin, piece.side.direction((-1, 0)))
        area_origin = add(area_origin, piece.side.direction((area_height - 1, 0)))
        area_squares = []
        col_increment = 0
        aim_left = area_origin[1] >= board_width / 2
        for col, row in product(range(area_width), range(area_height)):
            current_row = area_origin[0] + piece.side.direction(-row)
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
            piece_sets = {}
            for side in self.piece_sets:
                piece_group = piece_groups[self.piece_sets[side]]
                piece_sets[side] = piece_group.get(f"set_{side.key_name()[0]}", piece_group.get('set', [])).copy()
            promotion_side = piece.side
            if self.should_hide_pieces == 2:  # if in Penultima mode, mark promotion pieces with their respective sides
                if promotion not in piece_sets[promotion_side] and promotion not in [fide.Pawn]:
                    promotion_side = promotion_side.opponent()
            elif self.should_hide_pieces == 0:  # if in regular mode, mark king replacements with their respective sides
                if issubclass(promotion, abc.RoyalPiece) and promotion not in piece_sets[promotion_side]:
                    promotion_side = promotion_side.opponent()
            promotion_piece = promotion(self, pos, promotion_side)
            self.update_piece(promotion_piece)
            promotion_piece.scale = self.square_size / promotion_piece.texture.width
            promotion_piece.set_color(
                self.color_scheme.get(
                    f"{promotion_piece.side.key_name()}piece_color",
                    self.color_scheme["piece_color"]
                ),
                self.color_scheme["colored_pieces"]
            )
            self.promotion_piece_sprite_list.append(promotion_piece)
            self.promotion_area[pos] = promotion

    def end_promotion(self) -> None:
        self.promotion_piece = None
        self.promotion_area = {}
        self.promotion_area_sprite_list.clear()
        self.promotion_piece_sprite_list.clear()

    def replace(
            self, piece: abc.Piece, new_type: Type[abc.Piece | abc.PromotablePiece], new_side: Side | None = None
    ) -> None:
        if new_side is None:
            new_side = piece.side
        pos = piece.board_pos
        self.piece_sprite_list.remove(piece)
        self.pieces[pos[0]][pos[1]] = new_type(
            self, pos, new_side,
            promotions=self.promotions[new_side],
            promotion_squares=promotion_squares[new_side],
        ) if issubclass(new_type, abc.PromotablePiece) else new_type(self, pos, new_side)
        self.update_piece(self.pieces[pos[0]][pos[1]])
        self.pieces[pos[0]][pos[1]].set_color(
            self.color_scheme.get(
                f"{new_side.key_name()}piece_color",
                self.color_scheme["piece_color"]
            ),
            self.color_scheme["colored_pieces"]
        )
        self.pieces[pos[0]][pos[1]].scale = self.square_size / self.pieces[pos[0]][pos[1]].texture.width
        self.piece_sprite_list.append(self.pieces[pos[0]][pos[1]])
        self.pieces[pos[0]][pos[1]].board_pos = pos
        if pos in self.en_passant_markers and not self.not_a_piece(pos):
            self.en_passant_markers.remove(pos)

    def color_pieces(self, side: Side = Side.ANY, color: tuple[int, int, int] | None = None) -> None:
        for piece in self.movable_pieces.get(side, sum(self.movable_pieces.values(), [])):
            piece.set_color(
                color if color is not None else
                self.color_scheme.get(
                    f"{piece.side.key_name()}piece_color",
                    self.color_scheme["piece_color"]
                ),
                self.color_scheme["colored_pieces"]
            )

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

    def advance_turn(self) -> None:
        self.deselect_piece()
        # if we're promoting, we can't advance the turn yet
        if self.promotion_piece:
            return
        self.game_over = False
        if self.edit_mode:
            self.color_pieces()  # reverting the piece colors to normal in case they were changed
            return  # let's not advance the turn while editing the board to hopefully make things easier for everyone
        pass_check_side = Side.NONE
        if self.move_history and (self.move_history[-1] is None or self.move_history[-1].is_edit):
            self.load_check()  # here's something that can only happen if the board was edited or the turn was passed:
            if self.check_side == self.turn_side:  # if the player is in check at the end of their turn, the game ends
                self.game_over = True
                pass_check_side = self.check_side
        if self.move_history and self.move_history[-1] and self.move_history[-1].is_edit:
            # if the board was edited, reset probabilistic moves because they would need to be recalculated
            self.roll_history = self.roll_history[:self.ply_count - 1]
        self.turn_side = self.turn_side.opponent()
        self.load_all_moves()  # this updates the check status as well
        self.show_moves()
        if not sum(self.moves.values(), []):
            self.game_over = True
        if pass_check_side:
            self.check_side = pass_check_side
        if self.game_over:
            # the game has ended. let's find out who won and show it by changing piece colors
            if pass_check_side:
                # the last player was in check and passed the turn, the game ends and the current player wins
                self.log(f"[Ply {self.ply_count}] Info: Game over! {pass_check_side.opponent().name()} wins.")
            elif self.check_side:
                # the current player was checkmated, the game ends and the opponent wins
                self.log(f"[Ply {self.ply_count}] Info: Checkmate! {self.check_side.opponent().name()} wins.")
            else:
                # the current player was stalemated, the game ends in a draw
                self.log(f"[Ply {self.ply_count}] Info: Stalemate! It's a draw.")
        else:
            if self.check_side:
                # the game is still going, but the current player is in check
                self.log(f"[Ply {self.ply_count}] Info: {self.check_side.name()} is in check!")
            else:
                # the game is still going and there is no check
                pass
        self.color_all_pieces()

    def update_colors(self) -> None:
        self.color_scheme = colors[self.color_index]
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
                        f"{sprite.side.key_name()}piece_color",
                        self.color_scheme["piece_color"]
                    ),
                    self.color_scheme["colored_pieces"]
                )
        self.color_all_pieces()
        self.selection.color = self.color_scheme["selection_color"] if self.selection.alpha else (0, 0, 0, 0)
        self.highlight.color = self.color_scheme["highlight_color"] if self.highlight.alpha else (0, 0, 0, 0)
        self.show_moves()

    def color_all_pieces(self) -> None:
        if self.game_over:
            if self.check_side:
                self.color_pieces(
                    self.check_side,
                    self.color_scheme.get(
                        f"{self.check_side.key_name()}loss_color",
                        self.color_scheme["loss_color"]
                    ),
                )
                self.color_pieces(
                    self.check_side.opponent(),
                    self.color_scheme.get(
                        f"{self.check_side.opponent().key_name()}win_color",
                        self.color_scheme["win_color"]
                    ),
                )
            else:
                self.color_pieces(
                    Side.WHITE,
                    self.color_scheme.get(
                        f"{Side.WHITE.key_name()}draw_color",
                        self.color_scheme["draw_color"]
                    ),
                )
                self.color_pieces(
                    Side.BLACK,
                    self.color_scheme.get(
                        f"{Side.BLACK.key_name()}draw_color",
                        self.color_scheme["draw_color"]
                    ),
                )
        else:
            if self.check_side:
                self.color_pieces(
                    self.check_side,
                    self.color_scheme.get(
                        f"{self.check_side.key_name()}check_color",
                        self.color_scheme["check_color"]
                    ),
                )
                self.color_pieces(self.check_side.opponent())
            else:
                self.color_pieces()

    def update_piece(self, piece: abc.Piece) -> None:
        if self.should_hide_pieces == 1 or (self.should_hide_pieces == 2 and type(piece) in self.penultima_pieces):
            asset_folder = 'other'
        else:
            asset_folder = None
        if self.should_hide_pieces == 1:
            file_name = 'ghost'
        elif self.should_hide_pieces == 2 and type(piece) in self.penultima_pieces:
            file_name = self.penultima_pieces[type(piece)]
        else:
            file_name = None
        hidden = self.should_hide_moves if self.should_hide_moves is not None else bool(self.should_hide_pieces)
        piece.reload(hidden=hidden, asset_folder=asset_folder, file_name=file_name)

    def update_pieces(self) -> None:
        for piece in sum(self.movable_pieces.values(), [*self.promotion_piece_sprite_list]):
            self.update_piece(piece)

    def is_trickster_mode(self, value: bool = True) -> bool:
        return value == (self.trickster_color_index != 0)

    def update_trickster_mode(self) -> None:
        if self.is_trickster_mode(False):
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
        self.update_colors()
        for sprite_list in (self.piece_sprite_list, self.promotion_piece_sprite_list, [self.active_piece]):
            for sprite in sprite_list:
                if isinstance(sprite, abc.Piece) and not sprite.is_empty():
                    sprite.angle = 0

    def load_all_moves(self) -> None:
        self.load_check()
        movable_pieces = {side: self.movable_pieces[side].copy() for side in self.movable_pieces}
        royal_pieces = {side: self.royal_pieces[side].copy() for side in self.royal_pieces}
        quasi_royal_pieces = {side: self.quasi_royal_pieces[side].copy() for side in self.quasi_royal_pieces}
        probabilistic_pieces = {side: self.probabilistic_pieces[side].copy() for side in self.probabilistic_pieces}
        check_side = self.check_side
        castling_threats = self.castling_threats.copy()
        en_passant_target = self.en_passant_target
        en_passant_markers = self.en_passant_markers.copy()
        last_chain_move = self.chain_start
        if last_chain_move:
            while last_chain_move.chained_move:
                last_chain_move = last_chain_move.chained_move
        chain_moves = (
            self.chain_moves[(last_chain_move.pos_from, last_chain_move.pos_to)]
            if last_chain_move is not None else None
        )
        self.moves = {}
        self.chain_moves = {}
        generate_rolls = len(self.roll_history) < self.ply_count
        final_check = False
        moves_exist = None
        iterations = 0
        while not final_check:
            rolled_moves_exist = False
            for piece in movable_pieces[self.turn_side] if chain_moves is None else [last_chain_move.piece]:
                for move in piece.moves() if chain_moves is None else chain_moves:
                    self.update_move(move)
                    self.move(move)
                    move_chain = [move]
                    chained_move = move.chained_move
                    while chained_move:
                        self.update_move(chained_move)
                        self.move(chained_move)
                        move_chain.append(chained_move)
                        chained_move = chained_move.chained_move
                    self.ply_simulation += 1
                    self.load_check()
                    self.ply_simulation -= 1
                    if self.check_side != self.turn_side:
                        self.moves.setdefault(move.pos_from, []).append(move)
                        if move.chained_move:
                            self.chain_moves.setdefault((move.pos_from, move.pos_to), []).append(move.chained_move)
                        if moves_exist is None:
                            moves_exist = True
                        rolled_moves_exist = True
                    for chained_move in move_chain[::-1]:
                        self.undo(chained_move)
                    self.check_side = check_side
                    self.castling_threats = castling_threats.copy()
                    if en_passant_target is not None:
                        self.en_passant_target = en_passant_target
                        self.en_passant_markers = en_passant_markers.copy()
                        for marker in self.en_passant_markers:
                            self.mark_en_passant(self.en_passant_target.board_pos, marker)
            if moves_exist is None:
                moves_exist = False
            final_check = True
            if probabilistic_pieces[self.turn_side] and generate_rolls:
                if len(self.roll_history) < self.ply_count:
                    self.roll_history.append({})
                if moves_exist and (not iterations or not rolled_moves_exist):
                    for piece in probabilistic_pieces[self.turn_side]:
                        self.roll_history[-1][piece.board_pos] = piece.movement.roll()
                    self.moves = {}
                    self.chain_moves = {}
                    final_check = False
                    iterations += 1
        self.theoretical_moves = {}
        for piece in movable_pieces[self.turn_side.opponent()]:
            for move in piece.moves(theoretical=True):
                self.theoretical_moves.setdefault(move.pos_from, []).append(move)
        self.movable_pieces = movable_pieces
        self.royal_pieces = royal_pieces
        self.quasi_royal_pieces = quasi_royal_pieces
        self.probabilistic_pieces = probabilistic_pieces
        self.check_side = check_side
        self.castling_threats = castling_threats

    def unique_moves(self) -> list[Move]:
        move_list = []
        data_set = set()
        for move in sum(self.moves.values(), []):
            move_data = []
            while move:
                move_data.append(move.pos_from)
                if move.pos_from == move.pos_to and move.captured_piece:
                    move_data.append(move.captured_piece.board_pos)
                else:
                    move_data.append(move.pos_to)
                if move.promotion is not None:
                    move_data.append(move.promotion)
                move = move.chained_move
            move_data = tuple(move_data)
            if move_data not in data_set:
                data_set.add(move_data)
                move_list.append(move)
        return move_list

    def load_pieces(self):
        self.movable_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.royal_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.quasi_royal_pieces = {Side.WHITE: [], Side.BLACK: []}
        self.probabilistic_pieces = {Side.WHITE: [], Side.BLACK: []}
        for row, col in product(range(self.board_height), range(self.board_width)):
            piece = self.get_piece((row, col))
            if piece.side:
                self.movable_pieces[piece.side].append(piece)
                if isinstance(piece, abc.RoyalPiece):
                    self.royal_pieces[piece.side].append(piece)
                elif isinstance(piece, abc.QuasiRoyalPiece):
                    self.quasi_royal_pieces[piece.side].append(piece)
                if isinstance(piece.movement, movement.ProbabilisticMovement):
                    self.probabilistic_pieces[piece.side].append(piece)
        for side in (Side.WHITE, Side.BLACK):
            if len(self.quasi_royal_pieces[side]) == 1:
                self.royal_pieces[side].append(self.quasi_royal_pieces[side].pop())

    def load_check(self):
        self.load_pieces()
        self.check_side = Side.NONE
        self.castling_threats = set()
        for royal in self.royal_pieces[self.turn_side]:
            castle_moves = [
                move for move in royal.moves() if isinstance(move.movement, movement.CastlingMovement)
            ]
            castle_movements = set(move.movement for move in castle_moves)
            castle_squares = set(
                add(royal.board_pos, offset)
                for castling in castle_movements
                for offset in castling.gap + [castling.direction]
            )
            self.ply_simulation += 1
            for piece in self.movable_pieces[self.turn_side.opponent()]:
                for move in piece.moves():
                    last_move = move
                    while last_move.chained_move:
                        last_move = last_move.chained_move
                    if last_move.pos_to == royal.board_pos or last_move.captured_piece == royal:
                        self.check_side = self.turn_side
                        self.castling_threats = castle_squares
                        break
                    if last_move.pos_to in castle_squares:
                        self.castling_threats.add(last_move.pos_to)
                if self.check_side:
                    break
            self.ply_simulation -= 1
            if self.check_side:
                break

    def mark_en_passant(self, piece_pos: Position, marker_pos: Position) -> None:
        if self.en_passant_target is not None and self.en_passant_target.board_pos != piece_pos:
            return
        self.en_passant_target = self.get_piece(piece_pos)
        self.en_passant_markers.add(marker_pos)

    def clear_en_passant(self) -> None:
        self.en_passant_target = None
        self.en_passant_markers = set()

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
                positions = {move.pos_to for move in self.moves.get(self.selected_square, {})}
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
        if symbol == key.R:  # Restart
            if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:  # Randomize piece sets (same for both sides)
                piece_set = randrange(len(piece_groups))
                self.piece_sets = {side: piece_set for side in self.piece_sets}
                self.reset_board(update=True)
            elif modifiers & key.MOD_SHIFT:  # Randomize piece sets (separately for each side)
                self.piece_sets = {side: randrange(len(piece_groups)) for side in self.piece_sets}
                self.reset_board(update=True)
            elif modifiers & key.MOD_ACCEL:  # Restart with the same piece sets
                self.reset_board()
        if symbol == key.F11:  # Full screen (toggle)
            self.set_fullscreen(not self.fullscreen)
        if symbol == key.MINUS:  # (-) Decrease window size
            if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:
                self.set_size((self.board_width + 2) * min_size, (self.board_height + 2) * min_size)
            elif modifiers & key.MOD_ACCEL:
                width, height = self.get_size()
                self.set_size(
                    width - (self.board_width + 2) * size_step,
                    height - (self.board_height + 2) * size_step
                )
            elif modifiers & key.MOD_SHIFT:
                width, height = self.get_size()
                size = min(round(width / (self.board_width + 2)), round(height / (self.board_height + 2)))
                self.set_size((self.board_width + 2) * size, (self.board_height + 2) * size)
        if symbol == key.EQUAL:  # (+) Increase window size
            if modifiers & key.MOD_ACCEL and modifiers & key.MOD_SHIFT:
                self.set_size((self.board_width + 2) * max_size, (self.board_height + 2) * max_size)
            elif modifiers & key.MOD_ACCEL:
                width, height = self.get_size()
                self.set_size(
                    width + (self.board_width + 2) * size_step,
                    height + (self.board_height + 2) * size_step
                )
            elif modifiers & key.MOD_SHIFT:
                width, height = self.get_size()
                size = max(round(width / (self.board_width + 2)), round(height / (self.board_height + 2)))
                self.set_size((self.board_width + 2) * size, (self.board_height + 2) * size)
        if symbol == key.KEY_0 and modifiers & key.MOD_ACCEL:  # Reset window size
            self.set_size((self.board_width + 2) * self.square_size, (self.board_height + 2) * self.square_size)
        if symbol == key.E and modifiers & key.MOD_ACCEL:  # Edit mode (toggle)
            self.edit_mode = not self.edit_mode
            self.log(f"[Ply {self.ply_count}] Mode: {'EDIT' if self.edit_mode else 'PLAY'}")
            self.deselect_piece()
            self.hide_moves()
            if self.edit_mode:
                self.compare_history()
                self.advance_turn()
                self.moves = {}
                self.chain_moves = {}
                self.theoretical_moves = {}
                self.show_moves()
            else:
                self.turn_side = self.turn_side.opponent()
                self.compare_history()
                self.advance_turn()
                self.show_moves()
        if symbol == key.W:  # White
            if modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:  # White is in control
                if self.turn_side != Side.WHITE:
                    self.move_history.append(None)
                    self.log(f"[Ply {self.ply_count}] Pass: {Side.WHITE.name()}'s turn")
                    self.ply_count += 1
                    self.clear_en_passant()
                    self.compare_history()
                    self.advance_turn()
            elif modifiers & key.MOD_SHIFT:  # Shift white piece set
                d = -1 if modifiers & key.MOD_ACCEL else 1
                self.piece_sets[Side.WHITE] = (self.piece_sets[Side.WHITE] + d) % len(piece_groups)
                self.reset_board(update=True)
        if symbol == key.B:  # Black
            if modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:  # Black is in control
                if self.turn_side != Side.BLACK:
                    self.move_history.append(None)
                    self.log(f"[Ply {self.ply_count}] Pass: {Side.BLACK.name()}'s turn")
                    self.ply_count += 1
                    self.clear_en_passant()
                    self.compare_history()
                    self.advance_turn()
            elif modifiers & key.MOD_SHIFT:  # Shift black piece set
                d = -1 if modifiers & key.MOD_ACCEL else 1
                self.piece_sets[Side.BLACK] = (self.piece_sets[Side.BLACK] + d) % len(piece_groups)
                self.reset_board(update=True)
        if symbol == key.N:  # Next
            if modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:  # Next player is in control
                self.move_history.append(None)
                self.log(f"[Ply {self.ply_count}] Pass: {self.turn_side.opponent().name()}'s turn")
                self.ply_count += 1
                self.clear_en_passant()
                self.compare_history()
                self.advance_turn()
            elif modifiers & key.MOD_SHIFT:
                if self.piece_sets[Side.WHITE] == self.piece_sets[Side.BLACK]:  # Next piece set
                    d = -1 if modifiers & key.MOD_ACCEL else 1
                    self.piece_sets[Side.WHITE] = (self.piece_sets[Side.WHITE] + d) % len(piece_groups)
                    self.piece_sets[Side.BLACK] = (self.piece_sets[Side.BLACK] + d) % len(piece_groups)
                else:  # Next player goes first
                    piece_sets = self.piece_sets[Side.WHITE], self.piece_sets[Side.BLACK]
                    self.piece_sets[Side.BLACK], self.piece_sets[Side.WHITE] = piece_sets
                self.reset_board(update=True)
        if symbol == key.F:
            if modifiers & key.MOD_ACCEL:  # Flip
                self.flip_board()
            elif modifiers & key.MOD_SHIFT:  # Fast-forward
                while self.future_move_history:
                    self.redo_last_move()
        if symbol == key.G:  # Graphics
            if modifiers & key.MOD_ACCEL and not modifiers & key.MOD_SHIFT:  # Graphics reset
                self.color_index = 0
            elif modifiers & key.MOD_SHIFT:  # Graphics shift
                self.color_index = (self.color_index + (-1 if modifiers & key.MOD_ACCEL else 1)) % len(colors)
            if self.color_scheme["scheme_type"] == "cherub" and self.is_trickster_mode():
                self.trickster_color_index = 0
                self.reset_trickster_mode()
            else:
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
                        f"{piece_groups[self.piece_sets[Side.WHITE]]['name']} vs. "
                        f"{piece_groups[self.piece_sets[Side.BLACK]]['name']}"
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
        if symbol == key.T and modifiers & key.MOD_ACCEL:  # Trickster mode
            if self.color_scheme["scheme_type"] == "cherub":
                self.trickster_color_index = (
                    randrange(len(trickster_colors)) + 1 if self.is_trickster_mode(False) else 0
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
            if modifiers & key.MOD_SHIFT:  # Random piece
                self.deselect_piece()
                if self.moves:
                    self.select_piece(choice(list(self.moves.keys())))
            if modifiers & key.MOD_ACCEL:  # Random move
                if self.game_over:
                    return
                choices = (
                    self.moves.get(self.selected_square, [])
                    if self.selected_square            # Pick from moves of selected piece
                    else sum(self.moves.values(), [])  # Pick from all possible moves
                )
                if choices:
                    random_move = choice(choices)
                    chained_move = random_move
                    while chained_move:
                        self.update_move(chained_move)
                        random_move.piece.move(random_move)
                        self.log(f"[Ply {self.ply_count}] Move: {chained_move}")
                        chained_move = chained_move.chained_move
                    self.move_history.append(random_move)
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

    def update_sprite(
            self, sprite: Sprite, from_size: float, from_origin: tuple[float, float], from_flip_mode: bool
    ) -> None:
        old_position = sprite.position
        sprite.scale = self.square_size / sprite.texture.width
        sprite.position = self.get_screen_position(self.get_board_position(
            old_position, from_size, from_origin, from_flip_mode
        ))

    def update_sprites(self, width: float, height: float, flip_mode: bool) -> None:
        super().on_resize(width, height)
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

    def flip_board(self) -> None:
        self.update_sprites(self.width, self.height, not self.flip_mode)

    def log(self, string: str) -> None:
        self.log_data.append(string)
        print(string)

    def save_log(
            self,
            log_data: list[str] | None = None,
            log_name: str = "log",
            ts_format: str = "%Y-%m-%d_%H-%M-%S"
    ) -> None:
        if not log_data:
            log_data = self.log_data
        if log_data:
            name_args = [log_name, datetime.now().strftime(ts_format)]
            file_name = '_'.join(s for s in name_args if s).translate(invalid_chars_trans_table)
            with open(join(base_dir, f"{file_name}.txt"), "w") as log_file:
                log_file.write("\n".join(log_data))

    def clear_log(self) -> None:
        self.log_data.clear()
        system("cls" if os_name == "nt" else "clear")

    def debug_info(self) -> list[str]:
        debug_log_data = []  # noqa
        debug_log_data.append(f"Board size: {self.board_width}x{self.board_height}")
        debug_log_data.append("Color scheme:")
        color_scheme = deepcopy(self.color_scheme)  # just in case trickster mode messes with the color scheme RIGHT NOW
        for k, v in color_scheme.items():
            debug_log_data.append(f"  {k} = {v}")
        debug_log_data.append(f"Armies defined: {len(piece_groups)}")
        digits = len(str(len(piece_groups)))
        for i, group in enumerate(piece_groups):
            debug_log_data.append(f"ID {i:0{digits}d}: {group['name']}")
        white, black = self.piece_sets[Side.WHITE], self.piece_sets[Side.BLACK]
        debug_log_data.append(
            f"Game: "
            f"(ID {white:0{digits}d}) {piece_groups[white]['name']} vs. "
            f"(ID {black:0{digits}d}) {piece_groups[black]['name']}"
        )
        piece_sets = {}
        for side in self.piece_sets:
            piece_group = piece_groups[self.piece_sets[side]]
            piece_sets[side] = piece_group.get(f"set_{side.key_name()[0]}", piece_group.get('set', [])).copy()
            debug_log_data.append(f"{side.name()} setup: {', '.join(piece.name for piece in piece_sets[side])}")
            debug_log_data.append(f"{side.name()} pieces:")
            for piece in self.movable_pieces[side]:
                debug_log_data.append(f'  {piece.board_pos}: {piece.name}')
            if not self.movable_pieces[side]:
                debug_log_data[-1] += " None"
            debug_log_data.append(f"{side.name()} royal pieces:")
            for piece in self.royal_pieces[side]:
                debug_log_data.append(f'  {piece.board_pos}: {piece.name}')
            if not self.royal_pieces[side]:
                debug_log_data[-1] += " None"
            debug_log_data.append(f"{side.name()} quasiroyal pieces:")
            for piece in self.quasi_royal_pieces[side]:
                debug_log_data.append(f'  {piece.board_pos}: {piece.name}')
            if not self.quasi_royal_pieces[side]:
                debug_log_data[-1] += " None"
            debug_log_data.append(f"{side.name()} probabilistic pieces:")
            for piece in self.probabilistic_pieces[side]:
                debug_log_data.append(f'  {piece.board_pos}: {piece.name}')
            if not self.probabilistic_pieces[side]:
                debug_log_data[-1] += " None"
            piece_list = ', '.join(piece.name for piece in self.promotions[side])
            debug_log_data.append(f"{side.name()} promotions: {piece_list if piece_list else 'None'}")
            piece_list = ', '.join(piece.name for piece in self.edit_promotions[side])
            debug_log_data.append(f"{side.name()} replacements: {piece_list if piece_list else 'None'}")
        piece_modes = {0: 'Shown', 1: 'Hidden', 2: 'Penultima'}
        debug_log_data.append(f"Piece visibility: {piece_modes[self.should_hide_pieces]}")
        move_modes = {None: 'Default', False: 'Shown', True: 'Hidden'}
        debug_log_data.append(f"Move visibility: {move_modes[self.should_hide_moves]}")
        debug_log_data.append(f"Board mode: {'Edit' if self.edit_mode else 'Play'}")
        debug_log_data.append(f"Turn side: {self.turn_side.name() if self.turn_side else 'None'}")
        debug_log_data.append(f"Current ply: {self.ply_count}")
        debug_log_data.append(f"Actions made: {len(self.move_history)}")
        debug_log_data.append(f"Future actions: {len(self.future_move_history)}")
        debug_log_data.append(f"Moves possible: {len(sum(self.moves.values(), []))}")
        debug_log_data.append(f"Unique moves: {len(self.unique_moves())}")
        debug_log_data.append(f"Check side: {self.check_side.name() if self.check_side else 'None'}")
        debug_log_data.append(f"Game over: {self.game_over}")
        debug_log_data.append("Action history:")
        for move in self.move_history:
            if not move:
                debug_log_data.append("  (Pass) None")
            while move:
                debug_log_data.append(f"  ({'Edit' if move.is_edit else 'Move'}) {move}")
                move = move.chained_move
        if not self.move_history:
            debug_log_data[-1] += " None"
        debug_log_data.append("Future action history:")
        for move in self.future_move_history[::-1]:
            if not move:
                debug_log_data.append("  (Pass) None")
            while move:
                debug_log_data.append(f"  ({'Edit' if move.is_edit else 'Move'}) {move}")
                move = move.chained_move
        if not self.future_move_history:
            debug_log_data[-1] += " None"
        debug_log_data.append("Roll history:")
        for i, roll in enumerate(self.roll_history):
            debug_log_data.append(f"  Roll {i + 1}:")
            for pos, value in roll.items():
                debug_log_data.append(f"    {pos}: {value}")
        if not self.roll_history:
            debug_log_data[-1] += " None"
        return debug_log_data

    def on_resize(self, width: float, height: float):
        self.update_sprites(width, height, self.flip_mode)

    def on_deactivate(self):
        self.hovered_square = None
        self.clicked_square = None
        self.held_buttons = 0
        self.highlight.alpha = 0
        self.show_moves()

    def run(self):
        pass
