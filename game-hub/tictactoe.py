#! python3
from logging import (
    getLogger,
    DEBUG)
import tkinter as tk

logger = getLogger("TicTacToe")
logger.setLevel(DEBUG)

V0 = " "
P1 = "X"
P2 = "O"
BUTTON_STYLE = {"bg": "#F0F0F0", "activebackground": "#F0F0F0", "bd": 7,
                "relief": "ridge", "overrelief": "groove", "text": V0}
CLICKED_STYLE = {"fg": "#FFF", "activeforeground": "#000",
                 "overrelief": "ridge"}
WINNING_ROWS = ((0, 1, 2), (3, 4, 5), (6, 7, 8),
                (0, 3, 6), (1, 4, 7), (2, 5, 8),
                (0, 4, 8), (2, 4, 6))


def winner(board):
    for row in WINNING_ROWS:
        first = board[row[0]]
        if not first:
            continue
        if first == board[row[1]] == board[row[2]]:
            return first
    return 0


class Tictactoe():
    def start_ttt(self):
        def click(button):
            def w():
                if not self.starts:
                    logger.error("It is not your turn yet.")
                    return
                if self.board[button]:
                    logger.error("Could not choose that button.")
                    return
                kw = {"text": P1, "bg": "#F00", "activebackground": "#F00"}
                self.buttons[button].config(**CLICKED_STYLE, **kw)
                self.board[button] = 1
                self.starts = False
                self.esend(button.to_bytes(1, "big"))
            return w
        self.menu = "TTT"
        self.clear()
        self.master.minsize(600, 600)
        self.starts = False

        font = ("Arial", 80, "bold")
        self.buttons = []
        for a in range(9):
            button = tk.Button(self, command=click(a), font=font)
            button.place(relx=a % 3 / 3, rely=a // 3 / 3, relwidth=1 / 3,
                         relheight=1 / 3, anchor="nw")
            self.buttons.append(button)
        self.board = [0] * 9
        for button in self.buttons:
            button.config(**BUTTON_STYLE)

    def move_ttt(self, data):
        button = data[0]
        kw = {"text": P2, "bg": "#00F", "activebackground": "#00F"}
        self.buttons[button].config(**CLICKED_STYLE, **kw)
        self.board[button] = 2
        self.starts = True
        if winner(self.board) or 0 not in self.board:
            self.esend(b"!")
            
