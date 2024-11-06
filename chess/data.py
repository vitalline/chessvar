from __future__ import annotations

from math import ceil
from random import Random

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
from chess.pieces.piece import Piece
from chess.pieces.side import Side
from chess.pieces.util import NoPiece


default_board_width = 8
default_board_height = 8

min_width = 150.0
min_height = 75.0
default_size = 50.0
min_size = 25.0
max_size = 100.0
size_step = 5.0

base_rng = Random()
max_seed = 2 ** 32 - 1

penultima_textures = [f'ghost{s}' if s else None for s in ('R', 'N', 'B', 'Q', None, 'B', 'N', 'R')]

action_types = {
    v: k for k, vs in {
        'move': ('m', 'move'),
        'capture': ('c', 'capture'),
        'drop': ('d', 'drop'),
        'promotion': ('p', 'promote', 'promotion'),
        'pass': ('s', 'skip', 'pass'),  # 's' for 'skip' - 'p' is already taken by 'promote'
    }.items() for v in vs
}

end_types = {
    v: k for k, vs in {
        'check': ('+', 'check'),
        'checkmate': ('#', 'mate', 'checkmate'),
        'stalemate': ('=', 'stale', 'stalemate'),
        'capture': ('x', 'capture'),
    }.items() for v in vs
}

piece_groups: list[dict[str, str | list[type[Piece]]]] = [
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


def get_piece_types(side: Side = Side.WHITE) -> dict[type[Piece], str]:
    piece_types = {
        get_set_data(side, i)[j]
        for i in range(len(piece_groups)) for j in [i for i in range(4)] + [7]
        if j < 4 or get_set_data(side, i)[j] != get_set_data(side, i)[7 - j]
    } | {fide.Pawn, fide.King, cb.King}
    return {t: t.name + (' (CB)' if t.is_colorbound() or t == cb.King else '') for t in piece_types}


def get_set_data(side: Side, set_id: int) -> list[type[Piece]]:
    piece_group = piece_groups[set_id]
    return piece_group.get(f"set_{side.key()[0:1]}", piece_group.get('set', [NoPiece] * default_board_width))


def get_set_name(piece_set: list[type[Piece]], include_royals: bool = False) -> str:
    piece_name_order = [[i, len(piece_set) - 1 - i] for i in range(ceil(len(piece_set) / 2))]
    piece_names = []
    for group in piece_name_order:
        name_order = []
        used_names = set()
        for pos in group:
            if not piece_set[pos] or issubclass(piece_set[pos], NoPiece):
                continue
            if piece_set[pos] in {fide.King, cb.King} and pos == piece_name_order[-1][-1] and not include_royals:
                continue
            name = piece_set[pos].name
            if name not in used_names:
                name_order.append(name)
                used_names.add(name)
        piece_names.append('/'.join(name_order))
    piece_set_name = ', '.join(n for n in piece_names if n)
    return f"({piece_set_name})"
