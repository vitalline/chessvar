import os
import sys


if __name__ == '__main__':
    # Temporary workaround for arcade not loading its version in a PyInstaller freeze, which changes nothing whatsoever.
    from chess.util import no_print
    with no_print():
        import arcade.version
    import arcade
    from chess.board import Board

    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):  # noqa
        os.chdir(sys._MEIPASS)  # noqa
    window = Board()
    arcade.run()
