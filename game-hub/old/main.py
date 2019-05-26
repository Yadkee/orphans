#! python3
from logging import (
    basicConfig,
    getLogger,
    DEBUG)
from json import load
from os.path import join
import tkinter as tk
from client import Client
from chessboard import Board

basicConfig(format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = getLogger("lobby")
logger.setLevel(DEBUG)


class App(tk.Frame):
    def __init__(self, master, imageSize):
        self.client = Client(self.listen)
        self.args = (master, imageSize, self.client)

        tk.Frame.__init__(self, master)
        self.label = tk.Label(self, text="You are in the main lobby")
        self.label.grid(column=0, row=0)
        self.grid(column=0, row=0)

    def listen(self, data):
        if data.startswith(b"MATCH"):
            self.board = Board(*self.args, b"WHITE" in data, self.finnish)

    def finnish(self):
        self.client.listenCallback = self.listen
        print("Game ended")


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
    App(root, imageSize)
    root.mainloop()


if __name__ == "__main__":
    run()
