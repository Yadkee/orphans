#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk


def make_expandable(widget, columnRange, rowRange):
    for i in range(*columnRange):
        widget.columnconfigure(i, weight=1)
    for i in range(*rowRange):
        widget.rowconfigure(i, weight=1)


class AutoScrollbar(tk.Scrollbar):
    def __init__(self, master, **kw):
        tk.Scrollbar.__init__(self, master, **kw)
        self.showing = True

    def set(self, lo, hi):
        if self.showing and lo == "0.0" and hi == "1.0":
            self.grid_remove()
            self.showing = False
        elif not self.showing and not (lo == "0.0" and hi == "1.0"):
            self.grid()
            self.showing = True
        tk.Scrollbar.set(self, lo, hi)


class ScrollableFrame(tk.Frame):
    def __init__(self, master, **kw):
        self.frame = tk.Frame(master)
        self.canvas = tk.Canvas(self.frame, bd=0, highlightthickness=0)
        scrollbar = AutoScrollbar(self.frame, command=self.canvas.yview)
        tk.Frame.__init__(self, self.canvas, **kw)

        self.canvas.config(yscrollcommand=scrollbar.set)
        self.id = self.canvas.create_window(0, 0, window=self, anchor="nw")
        make_expandable(self.frame, [1], [1])

        self.canvas.grid(column=0, row=0, sticky="NSEW")
        scrollbar.grid(column=1, row=0, sticky="NSEW")

        self.bind("<Configure>", self.canvas_config)
        self.bind_all("<MouseWheel>", self.on_mousewheel)
        self.bind_all("<KeyPress-Up>",
                      lambda e: self.canvas.yview_scroll(-1, "units"))
        self.bind_all("<KeyPress-Down>",
                      lambda e: self.canvas.yview_scroll(1, "units"))

    def canvas_config(self, event):
        canvas = self.canvas
        canvas.configure(scrollregion=canvas.bbox(
            self.id), width=self.winfo_width())

    def on_mousewheel(self, event):
        direction = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(direction, "units")

    def grid(self, **kw):
        self.frame.grid(**kw)


class App(tk.Frame):
    def __init__(self, master, **kw):
        tk.Frame.__init__(self, master, **kw)
        self.wrongText = None
        self.oldColors = {}
        self.checking = {}
        self.secondList = tk.IntVar()
        self.thirdList = tk.IntVar()
        self.bg = "PaleTurquoise1"
        self.normalFont = ("Arial", 12)
        self.boldFont = self.normalFont + ("bold",)
        self.italicFont = self.normalFont + ("italic",)
        self.underlineFont = self.normalFont + ("underline",)
        self.fonts = {"1": self.boldFont,
                      "2": self.normalFont,
                      "3": self.italicFont}
        with open("list.txt", "r") as f:
            self.verbs = list(
                map(lambda x: x.split(", "), f.read().splitlines()))

        self.rowconfigure(0, weight=1)
        self.verbsFrame = ScrollableFrame(self)
        self.verbsFrame.canvas.config(height=600)
        self.verbsFrame.grid(column=0, row=0, sticky="NSEW")
        listsFrame = tk.Frame(self, bg=self.bg)
        listsFrame.grid(column=1, row=0, sticky="NSEW")
        tk.Checkbutton(listsFrame, bg=self.bg, activebackground=self.bg, text="Recommended by me",
                       variable=self.secondList, command=self.update).grid(column=0, row=0, sticky="NSW")
        tk.Checkbutton(listsFrame, bg=self.bg, activebackground=self.bg, text="Useless verbs",
                       variable=self.thirdList, command=self.update).grid(column=0, row=1, sticky="NSW")

        self.names = ("Base form", "Past simp.", "Past part.", "Translation")
        self.maxLenghts = tuple(max(max(len(i[j]) for i in self.verbs if len(
            i) > j), len(self.names[j])) for j in range(4))

        self.update()

        self.bind_class("Entry", "<FocusIn>", self.focus_in)
        self.bind_class("Entry", "<FocusOut>", self.check)
        self.bind_class("Entry", "<KeyPress-Return>",
                        lambda e: self.event_generate("<KeyPress-Tab>"))
        self.bind_class("Entry", "<Enter>", self.enter)
        self.bind_class("Entry", "<Leave>", self.leave)

    def update(self):
        lists = "1"
        if self.secondList.get():
            lists += "2"
        if self.thirdList.get():
            lists += "3"
        self.add_verbs(lists)

    def add_verbs(self, lists):
        children = set(self.verbsFrame.children.values())
        for i in children:
            i.destroy()
        for i in range(4):
            tk.Label(self.verbsFrame, text=self.names[i], font=self.underlineFont, bg=self.bg).grid(
                column=i, row=0, sticky="NSEW")
        a = 1
        for i in self.verbs:
            if i[0][0] in lists:
                self.add_line(i, a)
                a += 1

    def add_line(self, line, lineNumber):
        color = "PaleTurquoise1" if lineNumber & 1 else "PaleTurquoise2"
        font = self.fonts[line[0][0]]
        label1 = tk.Label(self.verbsFrame, font=font,
                          width=self.maxLenghts[0], bg=color, text=line[0][1:])
        label2 = tk.Label(self.verbsFrame, font=self.normalFont,
                          width=self.maxLenghts[3], bg=color, text=line[3] if len(line) > 3 else "")
        entry1 = tk.Entry(self.verbsFrame, font=font,
                          width=self.maxLenghts[1], bg=color)
        entry2 = tk.Entry(self.verbsFrame, font=font,
                          width=self.maxLenghts[2], bg=color)
        self.checking[hash(entry1)] = line[1]
        self.checking[hash(entry2)] = line[2]
        label1.grid(column=0, row=lineNumber, sticky="NSEW")
        label2.grid(column=3, row=lineNumber, sticky="NSEW")
        entry1.grid(column=1, row=lineNumber, sticky="NSEW")
        entry2.grid(column=2, row=lineNumber, sticky="NSEW")

    def focus_in(self, event):
        if self.wrongText is not None:
            widget = event.widget
            widget.config(bg=self.oldColors[hash(widget)])
            widget.delete(0, "end")
            widget.insert(0, self.wrongText)
            self.wrongText = None

    def check(self, event):
        widget = event.widget
        if hash(widget) not in self.oldColors:
            self.oldColors[hash(widget)] = widget.cget("bg")
        text = widget.get().lower().strip()
        if not text:
            widget.config(bg=self.oldColors[hash(widget)])
            widget.delete(0, "end")
        elif text == self.checking[hash(widget)]:
            widget.config(bg="lime")
            widget.delete(0, "end")
            widget.insert(0, text)
        else:
            widget.config(bg="red")
            widget.bell()

    def enter(self, event):
        widget = event.widget
        if widget.cget("bg") == "red":
            self.wrongText = widget.get()
            widget.config(bg="pink")
            widget.delete(0, "end")
            widget.insert(0, self.checking[hash(widget)])

    def leave(self, event):
        if self.wrongText is not None:
            widget = event.widget
            widget.config(bg="red")
            widget.delete(0, "end")
            widget.insert(0, self.wrongText)
            self.wrongText = None


if __name__ == "__main__":
    root = tk.Tk()
    make_expandable(root, [1], [1])
    root.title("Irregular verbs")
    App(root).grid(column=0, row=0, sticky="NSEW")

    root.mainloop()
