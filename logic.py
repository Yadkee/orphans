#! python3
from itertools import chain
# "♝", "♚", "♞", "♟", "♛", "♜")
#  1     2     3     4     5    6


def king_moves(pos):
    r, c = divmod(pos, 8)
    zip1 = zip((-8, 0, 8), (r, 1, r < 7))
    zip2 = list(zip((-1, 0, 1), (c, 1, c < 7)))
    return set(pos + v + h for v, c1 in zip1 if c1
               for h, c2 in zip2 if c2 and v | h)
KING_CACHE = [king_moves(i) for i in range(64)]


def night_moves(pos):
    r, c = divmod(pos, 8)
    zip11 = zip((-16, 16), (r > 1, r < 6))
    zip21 = list(zip((-1, 1), (c, c < 7)))
    zip12 = zip((-8, 8), (r, r < 7))
    zip22 = list(zip((-2, 2), (c > 1, c < 6)))
    zips = ((zip11, zip21), (zip12, zip22))
    return set(pos + v + h for zip1, zip2 in zips
               for v, c1 in zip1 if c1
               for h, c2 in zip2 if c2)
NIGHT_CACHE = [night_moves(i) for i in range(64)]


def movements(table, pos):
    # TODO: Consider pieces in between my path
    # TODO: Change 1, 3, 4, 5, 6
    isWhite, piece = divmod(table[pos], 10)
    if piece == 2:  # King
        return KING_CACHE[pos]
    elif piece == 3:  # Night
        return NIGHT_CACHE[pos]

    r, c = divmod(pos, 8)
    if piece == 1:  # Bishop
        zip1 = list(zip(range(-56, 57, 8),
                        chain((c >= i for i in (range(7, 0, -1))),
                              (c < i for i in range(7, 1, -1)))))
        zip2 = list(zip(range(-56, 57, 8),
                        chain((r >= i for i in (range(7, 0, -1))),
                              (r < i for i in range(7, 1, -1)))))
        return set(pos + v + h for v, c1 in zip1 if c1
                   for h, c2 in zip2 if c2 and v | h)
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
