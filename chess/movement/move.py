from typing import Tuple


class Move(object):
    def __init__(self, pos_from: Tuple[int, int], pos_to: Tuple[int, int]):
        self.pos_from = pos_from
        self.pos_to = pos_to
