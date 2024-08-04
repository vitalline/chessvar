import os
import sys

from chess.board import Board

if __name__ == '__main__':
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):  # noqa
        os.chdir(sys._MEIPASS)  # noqa
    Board().run()
