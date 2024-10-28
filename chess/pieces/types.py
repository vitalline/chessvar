class Double(object):
    # Pieces with this attribute can capture other pieces of their own side
    pass

class Immune(object):
    # Pieces with this attribute cannot be captured
    pass

class Royal(object):
    # Pieces with this attribute are subject to check and checkmate
    pass

class QuasiRoyal(object):
    # Pieces with this attribute are considered royal if they are the only such piece of their side
    pass

class Fast(object):
    # Pieces with this attribute cannot be captured en passant on squares they moved through during the last move chain
    pass

class Slow(object):
    # Pieces with this attribute can be captured en passant even if they haven't moved immediately before
    pass
