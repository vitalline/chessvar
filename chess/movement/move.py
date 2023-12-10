from chess.movement.util import Position


class Move(object):
    def __init__(self, pos_from: Position, pos_to: Position):
        self.pos_from = pos_from
        self.pos_to = pos_to
