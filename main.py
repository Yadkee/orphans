#! python3
from logging import (
    getLogger,
    DEBUG)
import tkinter as tk
from widgets.idle import Idle
from widgets.hub import Hub
from client import Client

logger = getLogger("Main")
logger.setLevel(DEBUG)


def run():
    def join(data):
        tagStr = data[2:].decode() + "#" + data[:2].hex()
        hub = Hub(root, client, tagStr)
        hub.grid(column=0, row=0, sticky="NSEW")
        print("JOINED")

    client = Client(join)

    root = tk.Tk()
    root.title("GameHub")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    app = Idle(root, client)
    app.grid(column=0, row=0, sticky="NSEW")
    root.mainloop()

if __name__ == "__main__":
    run()
