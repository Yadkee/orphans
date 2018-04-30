#! python3
from itertools import chain


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


def vertical_moves(pos):
    r, c = divmod(pos, 8)
    up = zip(range(-8, -64, -8), (r > i for i in range(0, 8)))
    down = zip(range(8, 64, 8), (r < i for i in range(7, 0, -1)))
    left = zip(range(-1, -8, -1), (c > i for i in range(0, 8)))
    right = zip(range(1, 8, 1), (c < i for i in range(7, 0, -1)))
    return [[i for i, cond in d if cond]
            for d in (up, down, left, right)]
VERTICAL_CACHE = [vertical_moves(i) for i in range(64)]


def diagonal_moves(pos):
    up, down, left, right = VERTICAL_CACHE[pos]
    combinations = (zip(up, left), zip(up, right),
                    zip(down, left), zip(down, right))
    return [[v + h for v, h in d] for d in combinations]
DIAGONAL_CACHE = [diagonal_moves(i) for i in range(64)]


def separate(board, pos):
    blank = set()
    enemy = set()
    isWhite = board[pos] // 10
    for i in movements(board, pos):
        p = board[i]
        if not p:
            blank.add(i)
        elif p // 10 != isWhite:
            enemy.add(i)
    return blank, enemy


def develop(directions, board, pos):
    isWhite = board[pos] // 10
    options = set()
    for d in directions:
        for i in d:
            aPos = pos + i
            aIsWhite, aPiece = divmod(board[aPos], 10)
            if not aPiece:
                options.add(aPos)
            elif aIsWhite == isWhite:
                break
            else:
                options.add(aPos)
                break
    return options


def movements(board, pos):
    isWhite, piece = divmod(board[pos], 10)
    if piece == 4:  # Pawn
        row = pos // 8
        options = set()
        step = (-8 if isWhite else 8)
        l, n, r = (pos + step - 1, pos + step, pos + step + 1)
        if board[l]:
            options.add(l)
        if board[r]:
            options.add(r)
        if not board[n]:
            options.add(n)
            if (isWhite and row == 6) or (not isWhite and row == 1):
                nn = pos + step * 2
                if not board[nn]:
                    options.add(nn)
        return options
    elif piece == 3:  # Night
        return NIGHT_CACHE[pos]
    elif piece == 1:  # Bishop
        return develop(DIAGONAL_CACHE[pos], board, pos)
    elif piece == 5:  # Queen
        return develop(DIAGONAL_CACHE[pos] + VERTICAL_CACHE[pos], board, pos)
    elif piece == 2:  # King
        return KING_CACHE[pos]
    elif piece == 6:  # Rook
        return develop(VERTICAL_CACHE[pos], board, pos)


def is_under_attack(board, pos):
    isWhite = board[pos] // 10
    for directions, pieces in ((DIAGONAL_CACHE[pos], (1, 5)),
                               (VERTICAL_CACHE[pos], (6, 5))):
        for d in directions:
            for i in d:
                aPos = pos + i
                aIsWhite, aPiece = divmod(board[aPos], 10)
                if aPiece:
                    if aIsWhite != isWhite and aPiece in pieces:
                        return True
                    break
    for i in KING_CACHE[pos]:
        aIsWhite, aPiece = divmod(board[i], 10)
        if aIsWhite != isWhite:
            if aPiece == 2:
                return True
            elif aPiece == 4:
                step = (-8 if aIsWhite else 8)
                l, r = (i + step - 1, i + step + 1)
                if l == pos or r == pos:
                    return True
    for i in NIGHT_CACHE[pos]:
        aIsWhite, aPiece = divmod(board[i], 10)
        if aIsWhite != isWhite and aPiece == 3:
            return True
    return False


def can_lcastle(board, isWhite):
    i, p = [(0, 0), (56, 10)][isWhite]
    return board[i:i + 5] == [p + 6, 0, 0, 0, p + 2]


def can_rcastle(board, isWhite):
    i, p = [(0, 0), (56, 10)][isWhite]
    return board[i + 4:i + 8] == [p + 2, 0, 0, p + 6]


def is_checked(board, isWhite):
    p = [0, 10][isWhite]
    pos = board.index(p)
    return is_under_attack(board, pos)

if __name__ == "__main__":
    from main import run
    run()
    raise SystemExit
