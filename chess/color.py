from colorsys import hls_to_rgb, hsv_to_rgb, rgb_to_hls, rgb_to_hsv

from PIL.ImageColor import getrgb


def average(color1: tuple[int, int, int], color2: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(min(255, max(0, round((x1 + x2) / 2))) for x1, x2 in zip(color1, color2))  # type: ignore


def lighten(color: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    h, l, s = rgb_to_hls(*(x / 255 for x in color))
    return tuple(  # type: ignore
        min(255, max(0, round(x * 255))) for x in hls_to_rgb(h, min(1.0, max(0.0, l + amount)), s)
    )


def darken(color: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return lighten(color, -amount)


def lighten_or_darken(color: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    h, l, s = rgb_to_hls(*(x / 255 for x in color))
    return tuple(  # type: ignore
        min(255, max(0, round(x * 255))) for x in
        hls_to_rgb(h, min(1.0, max(0.0, l + (amount if l < 0.5 else -amount))), s)
    )


def saturate(color: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    h, l, s = rgb_to_hls(*(x / 255 for x in color))
    return tuple(  # type: ignore
        min(255, max(0, round(x * 255))) for x in hls_to_rgb(h, l, min(1.0, max(0.0, s + amount)))
    )


def desaturate(color: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return saturate(color, -amount)


default_colors = {
    "colored_pieces": False,
    "text_color": (0, 0, 0),
    "piece_color": (255, 255, 255),
    "check_color": (200, 200, 200),
    "win_color": (225, 225, 225),
    "draw_color": (175, 175, 175),
    "loss_color": (125, 125, 125),
}

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
        "light_square_color": pair[0],
        "dark_square_color": pair[1],
        "scheme_type": pair[2],
        "background_color": average(pair[0], pair[1]),
        "text_color": (0, 0, 0),
    } for pair in [
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
        (getrgb('#00c060'), getrgb('#008040'), 'color'),
        (getrgb('#9060c0'), getrgb('#604080'), 'color'),
        (getrgb('#ff8080'), getrgb('#c04040'), 'color'),
        (getrgb('#ffff80'), getrgb('#c0c040'), 'color'),
        (getrgb('#80ff80'), getrgb('#40c040'), 'color'),
        (getrgb('#80c0ff'), getrgb('#4080c0'), 'color'),
        (getrgb('#c080ff'), getrgb('#8040c0'), 'color'),
        (getrgb('#ff80ff'), getrgb('#c040c0'), 'color'),
        (getrgb('#00d5f2'), getrgb('#0715cd'), 'sburb'),
        (getrgb('#f141ef'), getrgb('#b536da'), 'sburb'),
        (getrgb('#f2a400'), getrgb('#e00707'), 'sburb'),
        (getrgb('#4ac925'), getrgb('#1f9400'), 'sburb'),
        (getrgb('#a10000'), getrgb('#303030'), 'troll'),
        (getrgb('#a15000'), getrgb('#484848'), 'troll'),
        (getrgb('#a1a100'), getrgb('#505050'), 'troll'),
        (getrgb('#626262'), getrgb('#404040'), 'troll'),
        (getrgb('#416600'), getrgb('#404040'), 'troll'),
        (getrgb('#008141'), getrgb('#484848'), 'troll'),
        (getrgb('#008282'), getrgb('#484848'), 'troll'),
        (getrgb('#005682'), getrgb('#303030'), 'troll'),
        (getrgb('#000056'), getrgb('#383838'), 'troll'),
        (getrgb('#2b0057'), getrgb('#404040'), 'troll'),
        (getrgb('#6a006a'), getrgb('#484848'), 'troll'),
        (getrgb('#77003c'), getrgb('#505050'), 'troll'),
        (getrgb('#696969'), getrgb('#252525'), 'cherub'),
    ]
]


for i in range(len(colors)):
    colors[i]["promotion_area_color"] = lighten_or_darken(colors[i]["background_color"], 0.25)  # type: ignore
    if colors[i]["scheme_type"] in ("troll", "cherub"):
        r, g, b = (x / 255 for x in colors[i]["background_color"])
        colors[i]["text_color"] = tuple(  # type: ignore
            min(255, max(0, round(x * 255))) for x in hsv_to_rgb(0, 0, rgb_to_hsv(r, g, b)[2] + 0.3)
        )
    elif colors[i]["scheme_type"] == "color":
        colors[i]["text_color"] = colors[i]["promotion_area_color"]
    else:
        colors[i]["text_color"] = (0, 0, 0)
    if colors[i]["scheme_type"] == "cherub":
        colors[i]["colored_pieces"] = True
        colors[i]["white_piece_color"] = (0, 255, 0)
        colors[i]["black_piece_color"] = (255, 0, 0)
        colors[i]["white_check_color"] = (0, 192, 0)
        colors[i]["black_check_color"] = (192, 0, 0)
        colors[i]["white_draw_color"] = (64, 192, 64)
        colors[i]["black_draw_color"] = (192, 64, 64)
        colors[i]["win_color"] = None
    for key in default_colors:
        if key not in colors[i]:
            colors[i][key] = default_colors[key]
