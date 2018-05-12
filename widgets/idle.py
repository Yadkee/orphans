#! python3
import tkinter as tk
from threading import Thread


class Idle(tk.Frame):
    def __init__(self, master, client):
        def click():
            client.name = self.entry.get().encode()
            Thread(target=client.run, daemon=True).start()
        tk.Frame.__init__(self, master)
        master.minsize(400, 400)
        self.label = tk.Label(self, text=client.server[0],
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
