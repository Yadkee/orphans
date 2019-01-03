#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from time import time


class Crono(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, relief="flat", border=5)
        self.started = None
        self.saved = None

        self.label0 = tk.Label(self, text="00:00:00",
                               font=("Arial", 20, "bold"))
        self.button0 = tk.Button(self, text="Start", fg="lime",
                                 activeforeground="lime", width=5, takefocus=0, command=self.toggle)
        self.label1 = tk.Label(self, text="Or press spacebar")
        self.button1 = tk.Button(
            self, text="Reset", takefocus=0, command=self.reset)

        self.label0.grid(column=0, columnspan=2, row=0, sticky="NSEW")
        self.button0.grid(column=0, row=1, sticky="NSEW")
        self.label1.grid(column=1, row=1, sticky="NSEW")
        self.button1.grid(column=0, columnspan=2, row=2, sticky="NSEW")

    def toggle(self, event=None):
        # print(self.nametowidget(self.focus_displayof()).__class__)
        if not self.started:
            self.started = time() - self.saved if self.saved else time()
            self.button0.config(text="Pause", fg="red", activeforeground="red")
            self.loop()
        else:
            self.saved = time() - self.started
            self.started = None
            self.button0.config(text="Start", fg="lime",
                                activeforeground="lime")

    def reset(self):
        self.saved = None
        self.label0.config(text="00:00:00")

    def loop(self):
        if self.started:
            difference = int((time() - self.started) % 3600 * 100)
            decs = difference % 100
            secs = (difference // 100) % 60
            mins = difference // 6000
            self.label0.config(
                text="{:02}:{:02}:{:02}".format(mins, secs, decs))

            self.after_idle(self.loop)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Crono")
    root.resizable(0, 0)
    app = Crono(root)
    root.bind("<KeyPress-space>", app.toggle)
    app.grid(column=0, row=0)

    root.mainloop()
