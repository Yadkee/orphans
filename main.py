#! python3
from logging import (
    basicConfig,
    getLogger,
    DEBUG)
from json import load
from os.path import (
    join,
    exists)
from os import mkdir
try:
    from PIL import (
        Image,
        ImageTk)
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
import tkinter as tk
from logic import (
    movements,
    separate)
from game import Game
from client import Client

basicConfig(format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = getLogger("game")
logger.setLevel(DEBUG)

PIECES = ("bishop", "king", "night", "pawn", "queen", "rook")
#                           Knight would also start with K. That's why.
NAMES = [i + j for i in ("b", "w") for j in PIECES]
CHARS = ("♝", "♚", "♞", "♟", "♛", "♜", "♗", "♔", "♘", "♙", "♕", "♖")
#         1     2     3     4     5    6     11    12    13   14    15    16
CHARACTERS = dict(zip(NAMES, CHARS))
PIECES = (1, 2, 3, 4, 5, 6, 11, 12, 13, 14, 15, 16)

COLOR = {"blank": "lime", "enemy": "red", "castle": "yellow"}


class App(tk.Frame):
    def __init__(self, master, imageSize):
        imageSize8 = 8 * imageSize + 32
        tk.Frame.__init__(self, master, width=imageSize8, height=imageSize8)
        self.grid_propagate(0)
        self.imageSize = imageSize
        if HAS_PIL:
            self.load_images()
        self.game = Game(self.paint_button)
        self.client = Client(self.listen)

        for i in range(8):
            self.columnconfigure(i, weight=1, uniform="same")
            self.rowconfigure(i, weight=1, uniform="same")
        self.buttons = []
        for a in range(64):
            color = "plum" if (a + a // 8) & 1 else "white"
            button = tk.Button(self, bg=color, activebackground=color,
                               font=("Arial", -imageSize))
            button.grid(column=a % 8, row=a // 8, sticky="NSEW")
            self.buttons.append(button)
        self.start()

    def start(self):
        self.game.start()
        self.paint_button(*enumerate(self.game.board))
        self.options = [None, set(), set(), set()]  # p, blank, enemy, castle
        [b.config(command=self.press(a)) for a, b in enumerate(self.buttons)]

    def listen(self, data):
        if data.startswith(b"Welcome"):
            self.client.send(b"Ty")

    def press(self, button):
        def wrapper():
            if options[0] is not None:
                colorize(options[0], *options[1], *options[2], *options[3])
                if button in options[1] or button in options[2]:
                    # Move
                    game.move(options[0], button)
                elif button in options[3]:
                    # Castle
                    game.castle(options[0] > 32, button % 8 > 4)
                elif options[0] != button:
                    # Try to select
                    options[0] = None
                    wrapper()
                    return
                options[0] = None
            elif board[button]:
                # Select
                isWhite, piece = divmod(board[button], 10)
                blank, enemy = separate(board, button)
                options[0:4] = button, blank, enemy, set()
                colorize(button, aColor=color)
                colorize(*blank, aColor=COLOR["blank"])
                colorize(*enemy, aColor=COLOR["enemy"])
                if piece == 2:
                    for isRight in (False, True):
                        if game.can_castle(isWhite, isRight):
                            pos = isWhite * 56 + 2 + isRight * 4
                            colorize(pos, aColor=COLOR["castle"])
                            options[3].add(pos)
        color = "blue" if (button + button // 8) & 1 else "cyan"
        game = self.game
        board = self.game.board
        colorize = self.colorize
        options = self.options
        return wrapper

    def colorize(self, *arg, aColor=None):
        color = aColor
        for button in arg:
            if not aColor:
                color = "plum" if (button + button // 8) & 1 else "white"
            self.buttons[button].config(bg=color, activebackground=color)

    def paint_button(self, *arg):
        for button, value in arg:
            if not value:
                self.buttons[button].config(text="", image="")
            else:
                d, m = divmod(value, 10)
                toIndex = m - 1 + d * 6
                if HAS_PIL:
                    kw = {"image": self.images[toIndex]}
                else:
                    kw = {"text": CHARS[toIndex]}
                self.buttons[button].config(**kw)

    def load_images(self):
        folder = join("media", "")
        arg = ((self.imageSize, self.imageSize), Image.ANTIALIAS)
        self.images = [ImageTk.PhotoImage(
            Image.open(folder + name + ".png").resize(*arg)
        ) for name in NAMES]


def run():
    with open("config.json") as f:
        loaded = load(f)
        imageSize = int(loaded["imageSize"])
    imageSize8 = 8 * imageSize + 32
    root = tk.Tk()
    root.title("Chess")
    root.config(bg="gray")
    root.iconbitmap(default=join("media", "icon.ico"))
    root.geometry("%dx%d+0+0" % (imageSize8, imageSize8))
    root.minsize(imageSize8, imageSize8)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    app = App(root, imageSize)
    app.grid(column=0, row=0)
    root.mainloop()


if __name__ == "__main__":
    run()
