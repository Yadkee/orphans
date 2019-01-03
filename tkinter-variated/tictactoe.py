#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import time
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from tkinter.font import Font

RESOLUTION = (600, 600)
POSITION = (0, 0)

WINNING_ROWS = ((0, 1, 2), (3, 4, 5), (6, 7, 8),
                (0, 3, 6), (1, 4, 7), (2, 5, 8),
                (0, 4, 8), (2, 4, 6))
VOID = " "
PLAYER1 = "X"
PLAYER2 = "O"

DEBUG = True
dprint = lambda *args: print(*args)


def hex_str(c1, c2=None, c3=None):
    if c2 is None or c3 is None:
        c1, c2, c3 = c1
    return "#{:02X}{:02X}{:02X}".format(c1, c2, c3)


BLACK = hex_str(0, 0, 0)
WHITE = hex_str(255, 255, 255)
lGRAY = hex_str(230, 230, 230)
llGRAY = hex_str(240, 240, 240)
GRAY = hex_str(150, 150, 150)
lBLUE = hex_str(150, 200, 255)
BLUE = hex_str(0, 0, 255)
RED = hex_str(255, 0, 0)


def winner(board):
    for row in WINNING_ROWS:
        if board[row[0]] is VOID:
            continue
        if len(set(board[i] for i in row)) == 1:
            return board[row[0]]
    return False


def minimax(board, playerTurn=False, alpha=(-15, None), beta=(15, None), depth=5):
    if winner(board) == PLAYER2:
        return (+15 - depth, None)  # pc wins
    elif winner(board) == PLAYER1:
        return (-15 - depth, None)  # pc loses
    elif VOID not in board or depth < 1:
        return (0, None)  # tie
    elif playerTurn:
        for a in range(9):
            if board[a] is VOID:
                value = minimax(
                    board[:a] + PLAYER1 + board[a + 1:], not playerTurn, alpha, beta, depth - 1)[0]
                if value < beta[0]:
                    # Player tries to get the less benefit for PC
                    beta = (value, a)
                if beta[0] <= alpha[0]:
                    break
        return beta
    else:
        for a in range(9):
            if board[a] is VOID:
                value = minimax(
                    board[:a] + PLAYER2 + board[a + 1:], not playerTurn, alpha, beta, depth - 1)[0]
                if value > alpha[0]:
                    alpha = (value, a)  # PC tries to get the biggest benefit
                if beta[0] <= alpha[0]:
                    break
        return alpha


class Game():
    def __init__(self, difficulty=None):
        screen.title("Local mode")
        for w in set(screen.children.values()):
            w.destroy()

        self.difficulty = difficulty
        self.board = VOID * 9
        self.clickable = True

        self.buttons = []
        buttonStyle = {"bg": llGRAY, "activebackground": llGRAY, "font": (
            "Arial", 120, "bold"), "bd": 7, "relief": "ridge", "overrelief": "groove"}
        for y in range(3):
            for x in range(3):
                button = tk.Button(text=VOID, command=self.pulse(
                    y * 3 + x), **buttonStyle)
                button.place(relx=x / 3, rely=y / 3, relwidth=1 /
                             3, relheight=1 / 3, anchor="nw")
                self.buttons.append(button)

    def finished(self):
        if winner(self.board) or VOID not in self.board:
            return True
        else:
            return False

    def check(self):
        if self.finished() and messagebox.askyesno("Replay", "Play Again?"):
            self.start_wait()
            screen.update()
            screen.after(100, self.__init__(self.difficulty))

    def pulse(self, n):
        def w(n=n):  # wrapper
            if self.clickable and not self.finished() and self.player1_movement(n):
                if not self.finished():
                    self.player2_movement()
            self.check()
        return w

    def player1_movement(self, n):
        if self.board[n] is VOID:
            self.buttons[n].config(text=PLAYER1, bg=BLUE, activebackground=BLUE,
                                   fg=WHITE, activeforeground=BLACK, overrelief="ridge")
            self.board = self.board[:n] + PLAYER1 + self.board[n + 1:]
            return True
        else:
            return False

    def player2_movement(self):
        n = self.pc_movement()
        if n is not None and self.board[n] is VOID:
            self.buttons[n].config(text=PLAYER2, bg=RED, activebackground=RED,
                                   fg=WHITE, activeforeground=BLACK, overrelief="ridge")
            self.board = self.board[:n] + PLAYER2 + self.board[n + 1:]

    def pc_movement(self):
        t0 = time.time()
        if self.board[4] == VOID:
            n = 4
        elif self.difficulty < 1:
            n = random.choice(
                tuple(i for i in range(9) if self.board[i] == VOID))
        elif self.difficulty >= 1:
            n = minimax(self.board, depth=self.difficulty)[1]
        dprint("it took {:.5f} ms for the pc to think".format(
            (time.time() - t0) * 1000))
        return n

    def start_wait(self):
        self.clickable = False
        for i in self.buttons:
            if i.cget("bg") == llGRAY:
                i.config(bg=GRAY, activebackground=GRAY, overrelief="ridge")

    def stop_wait(self):
        self.clickable = True
        for i in self.buttons:
            if i.cget("bg") == GRAY:
                i.config(bg=llGRAY, activebackground=llGRAY,
                         overrelief="groove")


screen = tk.Tk()
screen.geometry(
    "{}x{}+{}+{}".format(RESOLUTION[0], RESOLUTION[0], POSITION[0], POSITION[1]))
screen.configure(background=WHITE)

newGame = Game(4)
screen.mainloop()
