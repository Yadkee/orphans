#! python3
import tkinter as tk


class Idle(tk.Frame):
    def __init__(self, master, callback):
        def click():
            callback(self.entry.get())
        tk.Frame.__init__(self, master)
        # Read serverAdress file
        with open("serverAddress", "rb") as f:
            encoded, _ = f.read().split(b"\n\r", 1)
        name = encoded.decode()
        self.label = tk.Label(self, text=name, font=("Times", 50, "bold"))
        self.entry = tk.Entry(self, width=16, font=("Consolas", 20))
        self.entry.insert(0, "MyName")
        self.button = tk.Button(self, text="JOIN", command=click,
                                font=("Times", 20, "bold"))

        self.label.place(relx=.5, rely=.2,
                         relwidth=.9, anchor="center")
        self.entry.place(relx=.5, rely=.6,
                         relwidth=.5, anchor="center")
        self.button.place(relx=.5, rely=.8, anchor="center")
