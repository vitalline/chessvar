import os
import sys

import arcade

from chess.board import Board

if __name__ == '__main__':
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        os.chdir(sys._MEIPASS)
    window = Board()
    arcade.run()
