#! python3
import tkinter as tk


class Idle(tk.Frame):
    def __init__(self, master, callback):
        def click():
            callback(self.entry.get())
        tk.Frame.__init__(self, master, width=800, height=800)
        # Read serverAdress file
        with open("serverAddress", "rb") as f:
            encoded, _ = f.read().split(b"\n\r", 1)
        name = encoded.decode()
        self.label = tk.Label(self, text=name, font=("Times", 50, "bold"))
        self.entry = tk.Entry(self)
        self.entry.insert(0, "MyName")
        self.button = tk.Button(self, text="JOIN", command=click)

        self.label.grid(column=0, row=0, columnspan=3)
        self.entry.grid(column=1, row=1)
        self.button.grid(column=1, row=2)