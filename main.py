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
        tk.Frame.__init__(self, master)
        if HAS_PIL:
            self.load_images()

    def load_images(self):
        folder = join("media", "")
        self.images = [ImageTk.PhotoImage(
                            Image.open(
                                folder + name + ".png"
                            ).resize(
                                (imageSize, imageSize)
                                ), Image.ANTIALIAS
                        ) for name in NAMES]


if __name__ == "__main__":
    with open("config.json") as f:
        loaded = load(f)
        imageSize = int(loaded["imageSize"])
    root = tk.Tk()
    root.title("Chess")
    root.config(bg="white")
    root.iconbitmap(default=join("media", "icon.ico"))
    root.geometry("300x300+0+0")
    app = App(root, imageSize)
    app.grid(column=0, row=0)
    root.mainloop()
