#! python3

if __name__ == "__main__":
    from main import run
    run()
    raise SystemExit


class Game():
    def __init__(self, moveCallback):
        self.moveCallback = moveCallback

    def start(self):
        self.board = ([6, 3, 1, 5, 2, 1, 3, 6] + [4] * 8 +
                      [0] * 32 +
                      [14] * 8 + [16, 13, 11, 15, 12, 11, 13, 16])
        self.canLCastle = [True, True]
        self.canRCastle = [True, True]

    def move(self, iPos, fPos):
        p = self.board[iPos]
        self.board[fPos] = p
        self.board[iPos] = 0
        self.moveCallback((fPos, p), (iPos, 0))

    def rcastle(self, isWhite):
        i, p = [(0, 0), (56, 10)][isWhite]
        self.board[i + 4:i + 7] = [0, p + 6, p + 2, 0]
        self.moveCallback((i + 6, p + 2), (i + 5, p + 6),
                          (i + 4, 0), (i + 7, 0))
        self.canLCastle[isWhite] = False
        self.canRCastle[isWhite] = False
