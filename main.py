#! python3
from logging import (
    basicConfig,
    getLogger,
    DEBUG)
from json import load
from os.path import join
try:
    from PIL import Image
    from PIL import ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
import tkinter as tk

basicConfig(format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = getLogger("game")
logger.setLevel(DEBUG)

PIECES = ("bishop", "king", "night", "pawn", "queen", "rook")
NAMES = [i + j for i in ("b", "w") for j in PIECES]
CHARS = ("♝", "♚", "♞", "♟", "♛", "♜", "♗", "♔", "♘", "♙", "♕", "♖")
#         1     2     3     4     5    6     11    12    13   14    15    16
CHARACTERS = dict(zip(NAMES, CHARS))


class App(tk.Frame):
    def __init__(self, master, imageSize):
        imageSize8 = 8 * imageSize + 32
        tk.Frame.__init__(self, master, width=imageSize8, height=imageSize8)
        self.grid_propagate(0)
        self.imageSize = imageSize
        if HAS_PIL:
            self.load_images()

        for i in range(8):
            self.columnconfigure(i, weight=1, uniform="same")
            self.rowconfigure(i, weight=1, uniform="same")
        self.buttons = []
        for a in range(64):
            color = "plum" if (a + a // 8) & 1 else "white"
            button = tk.Button(self, command=self.press(a),
                               bg=color, activebackground=color,
                               font=("Arial", -imageSize))
            button.grid(column=a % 8, row=a // 8, sticky="NSEW")
            self.buttons.append(button)

    def press(self, button):
        def wrapper():
            print(button)
        return wrapper

    def change_button(self, button, value):
        d, m = divmod(value, 10)
        toIndex = m - 1 + d * 6
        if HAS_PIL:
            kw = {"image": self.images[toIndex]}
        else:
            kw = {"text": CHARS[toIndex]}
        self.buttons[button].config(**kw)

    def load_images(self):
        folder = join("media", "")
        self.images = [ImageTk.PhotoImage(
                            Image.open(
                                folder + name + ".png"
                            ).resize(
                                (self.imageSize, self.imageSize)
                                ), Image.ANTIALIAS
                        ) for name in NAMES]


if __name__ == "__main__":
    with open("config.json") as f:
        loaded = load(f)
        imageSize = int(loaded["imageSize"])
    imageSize8 = 8 * imageSize + 32
    root = tk.Tk()
    root.title("Chess")
    root.config(bg="gray")
    root.iconbitmap(default=join("media", "icon.ico"))
    root.geometry("%dx%d+0+0" % (imageSize8, imageSize8))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    app = App(root, imageSize)
    app.grid(column=0, row=0)
    root.mainloop()
