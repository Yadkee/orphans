#! python3
from logging import (
    getLogger,
    DEBUG)
import tkinter as tk
from client import Client
from threading import Thread
from tictactoe import Tictactoe

logger = getLogger("Main")
logger.setLevel(DEBUG)
GAMES = ("TTT",)


def userAndTag(user, tag):
    return user.decode() + "#" + tag.hex()


class App(Client, tk.Frame, Tictactoe):
    def __init__(self, master):
        Client.__init__(self)
        tk.Frame.__init__(self, master)
        self.master = master
        self.start_idle()

    def clear(self):
        for i in self.winfo_children():
            i.destroy()

    def start_idle(self):
        def click(event=None):
            self.name = self.entry.get().encode()
            Thread(target=self.run, daemon=True).start()
        self.menu = "IDLE"
        self.clear()
        self.master.minsize(400, 400)
        self.label = tk.Label(self, text=self.server[0],
                              font=("Times", 50, "bold"))
        self.entry = tk.Entry(self, width=16, font=("Consolas", 20))
        self.entry.insert(0, "MyName")
        self.button = tk.Button(self, text="JOIN", command=click,
                                font=("Times", 20, "bold"))

        self.label.place(relx=.5, rely=.2,
                         relwidth=.9, anchor="center")
        self.entry.place(relx=.5, rely=.6,
                         relwidth=.5, anchor="center")
        self.button.place(relx=.5, rely=.8, anchor="center")

        self.entry.bind("<Return>", click)

    def start_hub(self):
        def click():
            configStr = b"TTT"
            queueFlags = self.queueFlags
            try:
                opponent = next(i for i in queueFlags
                                if queueFlags[i] == configStr)
            except StopIteration:
                self.esend(b"?%s" % configStr)
            else:
                self.esend(b"!%s" % opponent)
        self.menu = "HUB"
        self.clear()
        self.master.minsize(600, 400)
        self.last = (None, None, None)

        self.serverLabel = tk.Label(self, text=self.server[0],
                                    font=("Times", 50, "bold"))
        self.clientLabel = tk.Label(self, text=self.tagStr,
                                    font=("Times", 30), fg="gray")
        self.queueList = tk.Listbox(self)
        self.usersList = tk.Listbox(self)
        self.configLabel = tk.Label(self, text="CONFIG:")
        # TODO: configFrame containing all the config options
        self.button = tk.Button(self, command=click, text="PLAY")
        # TODO: Redesign all the widgets and organization

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        self.serverLabel.grid(column=0, row=0, columnspan=2, sticky="W")
        self.clientLabel.grid(column=2, row=0, sticky="E")
        self.queueList.grid(column=0, row=1, rowspan=2, sticky="NSEW")
        self.usersList.grid(column=2, row=1, rowspan=2, sticky="NSEW")
        self.configLabel.grid(column=1, row=1, sticky="NSEW")
        self.button.grid(column=1, row=2, sticky="SEW")

    def callback(self, event, data=None):
        print(",", event, data, self.menu)
        if event == "JOIN" and self.menu == "IDLE":
            self.tagStr = data[2:].decode() + "#" + data[:2].hex()
            self.users[data[:2]] = data[2:]
            self.tag = data[:2]
            self.start_hub()
            logger.info("JOINED")
        elif event == "LOBBY":
            self.start_hub()
            self.callback("U")
            logger.info("LOBBYED")
        elif event == "U" and self.menu == "HUB":
            users = self.users
            tags = self.tags
            queue = self.queue
            queueFlags = self.queueFlags
            lt, lq, lqf = self.last
            if lt != tags:
                self.usersList.delete(0, "end")
                self.usersList.insert("end", *(userAndTag(users[tag], tag)
                                               for tag in sorted(tags)))
            if lq != queue or lqf != queueFlags:
                self.queueList.delete(0, "end")
                iterable = (userAndTag(users[tag], tag) +
                            queueFlags[tag].decode()
                            for tag in sorted(queue) if tag != self.tag)
                self.queueList.insert(0, *iterable)
            self.last = (tags.copy(), queue.copy(), queueFlags.copy())
        elif event == "PLAY" and self.menu == "HUB":
            logger.info("PLAYING")
            if data == b"TTT":
                self.start_ttt()
            else:
                print("!play", data)
        elif event == "START" and self.menu in GAMES:
            logger.info("STARTING")
            self.starts = True
        elif event == "MOVE" and self.menu in GAMES:
            if self.menu == "TTT":
                self.move_ttt(data)
            else:
                print("!move", data, self.menu)
        else:
            print("!", event, data, self.menu)


def run():
    root = tk.Tk()
    root.title("GameHub")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    app = App(root)
    app.grid(column=0, row=0, sticky="NSEW")
    root.mainloop()

if __name__ == "__main__":
    run()
