class Double(object):
    # Can capture other pieces of its own side
    pass

class Immune(object):
    # Cannot be captured
    pass

class Royal(object):
    # Subject to check and checkmate
    pass

class QuasiRoyal(object):
    # Considered royal if it is the only such piece of their side
    pass

class Slow(object):
    # Can be captured en passant on any squares it moved through during the last move chain
    pass

class Delayed(object):
    # Can be captured en passant on the opponent's first move even if it hasn't moved immediately before
    pass

class Delayed2(object):
    # Same as above, but for any move until the next turn
    pass
