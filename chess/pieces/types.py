class Double(object):
    # Can capture other pieces of its own side
    pass

class Immune(object):
    # Cannot be captured by other pieces
    pass

class Royal(object):
    # Subject to check and checkmate rules
    pass

class QuasiRoyal(object):
    # Considered royal if it is the only such piece of their side
    pass

class Slow(object):
    # Can be captured en passant on any squares it moved through during the last move chain
    pass

class Delayed(object):
    # Can be captured en passant during the opponent's turn, even if it hasn't moved immediately before
    pass

class Delayed1(object):
    # Same as above, but only on the opponent's first move after the piece's last move
    pass
