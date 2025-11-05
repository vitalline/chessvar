import os
import sys

from pyglet import options

from chess.util import no_print

with no_print():
    from arcade import version  # noqa

from chess.board import Board

if __name__ == '__main__':
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):  # noqa
        os.chdir(sys._MEIPASS)  # noqa
    options.dpi_scaling = 'real'
    Board().run()
