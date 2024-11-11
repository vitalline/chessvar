class Empty(object):
    # Can be passed through by non-opposing pieces
    pass

class Enemy(object):
    # Can only capture pieces that do not belong to its opponent
    pass

class Double(object):
    # Can capture any piece that can be captured
    pass

class Immune(object):
    # Cannot be captured by other pieces
    pass

class Neutral(object):
    # Does not belong to any player
    pass

class Shared(object):
    # Can be moved by either player
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
