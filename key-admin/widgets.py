#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk


def make_expandable(widget, columnRange, rowRange):
    for i in range(*columnRange):
        widget.columnconfigure(i, weight=1)
    for i in range(*rowRange):
        widget.rowconfigure(0, weight=1)


class Pad(tk.Canvas):
    def __init__(self, master, size, **kw):
        tk.Canvas.__init__(self, master, **kw)
        self.size = size
        self.order = bytearray()
        self.selected = set()
        self.select = True

        self.bind("<Motion>", self.motion)
        self.bind("<KeyPress-space>", self.turn_off)
        self.bind("<KeyRelease-space>", self.turn_on)

    def turn_on(self, event):
        self.select = True
        self.motion(event)

    def turn_off(self, event=None):
        self.select = False

    def motion(self, event):
        if self.winfo_containing(event.x_root, event.y_root) is self is event.widget is self.focus_get() and self.select:
            width = self.winfo_width()
            height = self.winfo_width()
            size = self.size
            square_width = width // size[0]
            square_height = height // size[1]
            x = event.x // square_width
            y = event.y // square_height
            i = x + y * size[0]
            if i not in self.selected:
                self.selected.add(i)
                self.order.append(i)
                self.create_rectangle(x * square_width, y * square_height, (x + 1) * square_width, (y + 1) * square_height,
                                      fill="black")

    def clear(self):
        self.order.clear()
        self.selected.clear()
        self.delete("all")


class InfoEntry(tk.Entry):
    def __init__(self, master, **kw):
        self.info = kw.pop("info", "")
        self.info_fg = kw.pop("info_fg", "gray")
        tk.Entry.__init__(self, master, **kw)
        self.showing_info = False
        self.show_info()
        self.bind("<Any-KeyPress>", self.keypress)
        self.bind("<Any-KeyRelease>", self.keyrelease)
        self.bind("<FocusIn>", self.keyrelease)
        self.bind("<FocusOut>", self.keyrelease)
        self.bind("<ButtonPress-1>", self.click)
        self.bind("<B1-Motion>", self.click)

    def show_info(self):
        if not self.showing_info:
            self.fg = self.cget("fg")
            self.show = self.cget("show")
            self.config(fg=self.info_fg, show="")
            tk.Entry.insert(self, 0, self.info)
            self.showing_info = True
        self.icursor(0)

    def unshow_info(self):
        if self.showing_info:
            self.config(fg=self.fg, show=self.show)
            self.delete(0, len(self.info))
            self.showing_info = False

    def keypress(self, event):
        self.unshow_info()

    def keyrelease(self, event):
        if (self.get() or self.info) == self.info:
            self.select_clear()
            self.show_info()
            return "break"

    def click(self, event=None):
        self.focus_set()
        if (self.get() or self.info) == self.info:
            self.icursor(0)
            self.select_clear()
            return "break"

    def insert(self, index, string):
        self.unshow_info()
        tk.Entry.insert(self, index, string)


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
