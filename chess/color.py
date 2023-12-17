from colorsys import hls_to_rgb, rgb_to_hls

from PIL.ImageColor import getrgb

default_colors = {
    "colored_pieces": False,
    "text_color": (0, 0, 0),
    "piece_color": (255, 255, 255),
    "check_color": (200, 200, 200),
    "win_color": (225, 225, 225),
    "draw_color": (175, 175, 175),
    "loss_color": (125, 125, 125),
}

colors = [
    {
        "light_square_color": pair[0],
        "dark_square_color": pair[1],
        "background_color": tuple(round((a + b) / 2) for a, b in zip(pair[0], pair[1])),
        "text_color": (0, 0, 0),
    } for pair in [
        (getrgb('#eeeed2'), getrgb('#769656')),
        (getrgb('#f0d9b5'), getrgb('#b58863')),
        (getrgb('#ffcc99'), getrgb('#bb7733')),
        (getrgb('#c8ad78'), getrgb('#885c38')),
        (getrgb('#d8e4e8'), getrgb('#789cb0')),
        (getrgb('#e8e8e4'), getrgb('#32684c')),
        (getrgb('#eae9d2'), getrgb('#4b7399')),
        (getrgb('#ffffff'), getrgb('#fcd8dd')),
        (getrgb('#c8c4ac'), getrgb('#686460')),
        (getrgb('#7a8593'), getrgb('#303844')),
        (getrgb('#a0a0a0'), getrgb('#606060')),
        (getrgb('#e8eeee'), getrgb('#a8aeae')),
        (getrgb('#7da1c0'), getrgb('#5285b0')),
        (getrgb('#00c060'), getrgb('#008040')),
        (getrgb('#9060c0'), getrgb('#604080')),
        (getrgb('#ff8080'), getrgb('#c04040')),
        (getrgb('#ffff80'), getrgb('#c0c040')),
        (getrgb('#80ff80'), getrgb('#40c040')),
        (getrgb('#80c0ff'), getrgb('#4080c0')),
        (getrgb('#c080ff'), getrgb('#8040c0')),
        (getrgb('#ff80ff'), getrgb('#c040c0')),
        (getrgb('#00d5f2'), getrgb('#0715cd')),
        (getrgb('#f141ef'), getrgb('#b536da')),
        (getrgb('#f2a400'), getrgb('#e00707')),
        (getrgb('#4ac925'), getrgb('#1f9400')),
    ]
] + [
    {
        "light_square_color": pair[0],
        "dark_square_color": pair[1],
        "background_color": tuple(round((a + b) / 2) for a, b in zip(pair[0], pair[1])),
        "text_color": (224, 224, 224),
    } for pair in [
        (getrgb('#a10000'), getrgb('#303030')),
        (getrgb('#a15000'), getrgb('#484848')),
        (getrgb('#a1a100'), getrgb('#505050')),
        (getrgb('#626262'), getrgb('#404040')),
        (getrgb('#416600'), getrgb('#404040')),
        (getrgb('#008141'), getrgb('#484848')),
        (getrgb('#008282'), getrgb('#484848')),
        (getrgb('#005682'), getrgb('#303030')),
        (getrgb('#000056'), getrgb('#383838')),
        (getrgb('#2b0057'), getrgb('#404040')),
        (getrgb('#6a006a'), getrgb('#484848')),
        (getrgb('#77003c'), getrgb('#505050')),
        (getrgb('#696969'), getrgb('#252525')),
    ]
]


for i in range(len(colors)):
    h, l, s = rgb_to_hls(*colors[i]["background_color"])
    if l < 128:
        colors[i]["promotion_area_color"] = tuple(min(255, max(0, round(x))) for x in hls_to_rgb(h, l + 64, s))
    else:
        colors[i]["promotion_area_color"] = tuple(min(255, max(0, round(x))) for x in hls_to_rgb(h, l - 64, s))
    for key in default_colors:
        if key not in colors[i]:
            colors[i][key] = default_colors[key]


colors[-1]["colored_pieces"] = True
colors[-1]["white_piece_color"] = (0, 255, 0)
colors[-1]["black_piece_color"] = (255, 0, 0)
colors[-1]["white_check_color"] = (0, 192, 0)
colors[-1]["black_check_color"] = (192, 0, 0)
colors[-1]["white_draw_color"] = (64, 192, 64)
colors[-1]["black_draw_color"] = (192, 64, 64)
colors[-1]["win_color"] = None
