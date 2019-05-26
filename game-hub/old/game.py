#! python3
from logic import (
    can_lcastle,
    can_rcastle)


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

    def can_castle(self, isWhite, isRight):
        if isRight and can_rcastle(self.board, isWhite):
            return self.canRCastle[isWhite]
        elif not isRight and can_lcastle(self.board, isWhite):
            return self.canLCastle[isWhite]
        return False

    def castle(self, isWhite, isRight):
        i, p = [(0, 0), (56, 10)][isWhite]
        if isRight:
            self.board[i + 4:i + 8] = [0, p + 6, p + 2, 0]
            self.moveCallback((i + 6, p + 2), (i + 5, p + 6),
                              (i + 4, 0), (i + 7, 0))
        else:
            self.board[i:i + 5] = [0, 0, p + 2, p + 6, 0]
            self.moveCallback((i, 0), (i + 1, 0), (i + 2, p + 2),
                              (i + 3, p + 6), (i + 4, 0))
        self.canLCastle[isWhite] = False
        self.canRCastle[isWhite] = False

if __name__ == "__main__":
    from main import run
    run()
