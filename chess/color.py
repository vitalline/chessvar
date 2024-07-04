from colorsys import hls_to_rgb, hsv_to_rgb, rgb_to_hls, rgb_to_hsv

from PIL.ImageColor import getrgb
from arcade import Color


def bound_float(x: float) -> float:
    return min(1.0, max(0.0, x))


def bound_color(color: Color) -> Color:
    return tuple(min(255, max(0, x)) for x in color)  # type: ignore


def to_float(color: Color) -> tuple[float, float, float]:
    return tuple(x / 255 for x in color[:3])  # type: ignore


def to_color(color: tuple[float, float, float] | Color) -> Color:
    return bound_color([round(x * 255) for x in color])


def average(color1: Color, color2: Color) -> Color:
    return bound_color([round((x1 + x2) / 2) for x1, x2 in zip(color1, color2)])


def multiply(color: Color, amount: float) -> Color:
    return bound_color([round(x * amount) for x in color[:3]]) + color[3:]


def lighten(color: Color, amount: float) -> Color:
    h, l, s = rgb_to_hls(*to_float(color))
    return to_color(hls_to_rgb(h, bound_float(l + amount), s)) + color[3:]


def darken(color: Color, amount: float) -> Color:
    return lighten(color, -amount)


def lighten_or_darken(color: Color, amount: float) -> Color:
    return lighten(color, amount if rgb_to_hls(*to_float(color))[1] < 0.5 else -amount)


def saturate(color: Color, amount: float) -> Color:
    h, l, s = rgb_to_hls(*to_float(color))
    return to_color(hls_to_rgb(h, l, bound_float(s + amount))) + color[3:]


def desaturate(color: Color, amount: float) -> Color:
    return saturate(color, -amount)


# defaults for colors that are not defined in the color schemes
# these are used as fallbacks in case a color scheme does not define a color
default_colors = {
    "colored_pieces": False,
    "text_color": (0, 0, 0),
    "highlight_color": (0, 0, 0, 80),
    "selection_color": (0, 0, 0, 120),
    "piece_color": (255, 255, 255),
    "check_color": (200, 200, 200),
    "win_color": (225, 225, 225),
    "draw_color": (175, 175, 175),
    "loss_color": (125, 125, 125),
}

# base colors for trickster mode
# these are used to generate the rest of the trickster colors in Board.update_colors()
trickster_colors = [
    getrgb('#ffd1d1'),
    getrgb('#ffe6d1'),
    getrgb('#fff6d1'),
    getrgb('#d1ffe3'),
    getrgb('#d1f9ff'),
    getrgb('#d1dcff'),
    getrgb('#f0d1ff'),
]

colors = [
    {
        "scheme_type": pair[2],
        "light_square_color": pair[0],
        "dark_square_color": pair[1],
        "background_color": average(pair[0], pair[1]),
        "text_color": (0, 0, 0),
    } for pair in [
        # light square color, dark square color, type

        # chess: general chessboard colors
        (getrgb('#eeeed2'), getrgb('#769656'), 'chess'),
        (getrgb('#f0d9b5'), getrgb('#b58863'), 'chess'),
        (getrgb('#ffcc99'), getrgb('#bb7733'), 'chess'),
        (getrgb('#c8ad78'), getrgb('#885c38'), 'chess'),
        (getrgb('#d8e4e8'), getrgb('#789cb0'), 'chess'),
        (getrgb('#e8e8e4'), getrgb('#32684c'), 'chess'),
        (getrgb('#eae9d2'), getrgb('#4b7399'), 'chess'),
        (getrgb('#ffffff'), getrgb('#fcd8dd'), 'chess'),
        (getrgb('#c8c4ac'), getrgb('#686460'), 'chess'),
        (getrgb('#7a8593'), getrgb('#303844'), 'chess'),
        (getrgb('#a0a0a0'), getrgb('#606060'), 'chess'),
        (getrgb('#e8eeee'), getrgb('#a8aeae'), 'chess'),
        (getrgb('#7da1c0'), getrgb('#5285b0'), 'chess'),

        # color: monotone color schemes
        (getrgb('#00c060'), getrgb('#008040'), 'color'),  # green vi
        (getrgb('#9060c0'), getrgb('#604080'), 'color'),  # purple vi
        (getrgb('#ff8080'), getrgb('#c04040'), 'color'),  # (0/12) red
        (getrgb('#ffff80'), getrgb('#c0c040'), 'color'),  # (2/12) yellow
        (getrgb('#80ff80'), getrgb('#40c040'), 'color'),  # (4/12) green
        (getrgb('#80c0ff'), getrgb('#4080c0'), 'color'),  # (7/12) blue
        (getrgb('#c080ff'), getrgb('#8040c0'), 'color'),  # (9/12) purple
        (getrgb('#ff80ff'), getrgb('#c040c0'), 'color'),  # (10/12) pink

        # sburb: homestuck kid colors
        (getrgb('#00d5f2'), getrgb('#0715cd'), 'sburb'),  # jane / john
        (getrgb('#ff6ff2'), getrgb('#b536da'), 'sburb'),  # roxy / rose
        (getrgb('#f2a400'), getrgb('#e00707'), 'sburb'),  # dirk / dave
        (getrgb('#4ac925'), getrgb('#1f9400'), 'sburb'),  # jade / jake
        # (jade's color is brighter so it's used for the light squares)

        # troll: homestuck troll colors
        (getrgb('#a10000'), getrgb('#303030'), 'troll'),  # aradia
        (getrgb('#a15000'), getrgb('#484848'), 'troll'),  # tavros
        (getrgb('#a1a100'), getrgb('#505050'), 'troll'),  # sollux
        (getrgb('#626262'), getrgb('#404040'), 'troll'),  # karkat
        (getrgb('#416600'), getrgb('#404040'), 'troll'),  # nepeta
        (getrgb('#008141'), getrgb('#484848'), 'troll'),  # kanaya
        (getrgb('#008282'), getrgb('#484848'), 'troll'),  # terezi
        (getrgb('#005682'), getrgb('#303030'), 'troll'),  # vriska
        (getrgb('#000056'), getrgb('#383838'), 'troll'),  # equius
        (getrgb('#2b0057'), getrgb('#404040'), 'troll'),  # gamzee
        (getrgb('#6a006a'), getrgb('#484848'), 'troll'),  # eridan
        (getrgb('#77003c'), getrgb('#505050'), 'troll'),  # feferi
        # light squares are the troll's associated (text) color
        # dark squares are shades of gray matching the perceived brightness of the light squares

        # cherub: NOT the homestuck cherub colors, instead the colors of the cherub chess set
        (getrgb('#696969'), getrgb('#252525'), 'cherub'),
        # the rest of the cherub colors are generated below
    ]
]


for i in range(len(colors)):
    # set the promotion area background color to be a lighter or darker version of the background color
    colors[i]["promotion_area_color"] = lighten_or_darken(colors[i]["background_color"], 0.25)
    if colors[i]["scheme_type"] in ("troll", "cherub"):
        # make the text, highlight, and selection colors lighter
        colors[i]["text_color"] = to_color(
            # grayscale text that is readable on the background color (30% brightness increase compared to bg)
            hsv_to_rgb(0, 0, bound_float(rgb_to_hsv(*to_float(colors[i]["background_color"]))[2] + 0.3))
        )
        colors[i]["highlight_color"] = (255, 255, 255, 80)
        colors[i]["selection_color"] = (255, 255, 255, 120)
    elif colors[i]["scheme_type"] == "color":
        # make the text color match the promotion background color
        colors[i]["text_color"] = colors[i]["promotion_area_color"]
    else:
        # make the text color black
        colors[i]["text_color"] = (0, 0, 0)
    if colors[i]["scheme_type"] == "troll":
        if colors[i]["light_square_color"] == getrgb('#626262'):
            # special case for karkat's color - make the white pieces gray and distinguishable
            colors[i]["white_piece_color"] = (128, 128, 128)
            colors[i]["white_check_color"] = (100, 100, 100)
            colors[i]["white_win_color"] = (112, 112, 112)
            colors[i]["white_draw_color"] = (88, 88, 88)
            colors[i]["white_loss_color"] = (62, 62, 62)
        else:
            # make the white pieces match the hue of the light squares (i.e. respective troll's color)
            colors[i]["white_piece_color"] = lighten(colors[i]["light_square_color"], 0.2)
            colors[i]["white_check_color"] = desaturate(colors[i]["white_piece_color"], 0.25)
            colors[i]["white_win_color"] = lighten(colors[i]["light_square_color"], 0.25)
            colors[i]["white_draw_color"] = desaturate(colors[i]["light_square_color"], 0.25)
            colors[i]["white_loss_color"] = desaturate(colors[i]["white_check_color"], 0.25)
        # make the black pieces depend on the dark square color (i.e. a perceptible shade of gray)
        colors[i]["black_piece_color"] = multiply(colors[i]["dark_square_color"], 2)
        colors[i]["black_check_color"] = multiply(colors[i]["dark_square_color"], 1.5625)
        colors[i]["black_win_color"] = multiply(colors[i]["dark_square_color"], 1.75)
        colors[i]["black_draw_color"] = multiply(colors[i]["dark_square_color"], 1.375)
        colors[i]["black_loss_color"] = multiply(colors[i]["dark_square_color"], 1)
    if colors[i]["scheme_type"] == "cherub":
        # define the cherub piece colors (white pieces are green, black pieces are red)
        colors[i]["colored_pieces"] = True
        colors[i]["white_piece_color"] = (0, 255, 0)
        colors[i]["black_piece_color"] = (255, 0, 0)
        colors[i]["white_check_color"] = (0, 192, 0)
        colors[i]["black_check_color"] = (192, 0, 0)
        colors[i]["white_draw_color"] = (64, 192, 64)
        colors[i]["black_draw_color"] = (192, 64, 64)
        colors[i]["win_color"] = None
    # add defaults for required colors that were not previously defined
    for key in default_colors:
        if key not in colors[i]:
            colors[i][key] = default_colors[key]
