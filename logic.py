#! python3
from itertools import chain
# "♝", "♚", "♞", "♟", "♛", "♜")
#  1     2     3     4     5    6


def movements(piece, pos):
    # TODO: Consider pieces in between my path
    isWhite, piece = divmod(piece, 10)
    c, r = divmod(pos, 8)
    if piece == 1:  # Bishop
        zip1 = list(zip(range(-56, 57, 8),
                        chain((c >= i for i in (range(7, 0, -1))),
                              (c < i for i in range(7, 1, -1)))))
        zip2 = list(zip(range(-56, 57, 8),
                        chain((r >= i for i in (range(7, 0, -1))),
                              (r < i for i in range(7, 1, -1)))))
        return set(pos + v + h for v, c1 in zip1 if c1
                   for h, c2 in zip2 if c2 and v | h)
    elif piece == 2:  # King
        zip1 = list(zip((-8, 0, 8), (r, 1, r < 7)))
        zip2 = list(zip((-1, 0, 1), (c, 1, c < 7)))
        return set(pos + v + h for v, c1 in zip1 if c1
                   for h, c2 in zip2 if c2 and v | h)
    elif piece == 3:  # Night
        zip11 = zip((-16, 16), (r > 1, r < 6))
        zip21 = zip((-1, 1), (c, c < 7))
        zip12 = zip((-8, 8), (r, r < 7))
        zip22 = zip((-2, 2), (c > 1, c < 6))
        zips = chain(zip(zip11, zip21), zip(zip12, zip22))
        return set(pos + v + h for v, c1 in zip1 if c1
                   for h, c2 in zip2 if c2 and v | h for zip1, zip2 in zips)
    elif piece == 4:  # Pawn
        out = set()
        extra = (isWhite and r == 6) or (not isWhite and r == 1)
        out.add(pos + (-8 if isWhite else 8))
        if extra:
            out.add(pos + (-16 if isWhite else 16))
        return out
    elif piece == 5:  # Queen
        pass
    elif piece == 6:  # Rook
        pass
