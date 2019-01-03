#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tkinter import Text, Listbox, Scrollbar, Frame, Canvas


class AutoScrollbar(Scrollbar):
    def __init__(self, *args, **kwargs):
        Scrollbar.__init__(self, *args, **kwargs)
        self.showing = True

    def set(self, lo, hi):
        if self.showing and lo == "0.0" and hi == "1.0":
            self.grid_remove()
            self.showing = False
        elif not self.showing and not (lo == "0.0" and hi == "1.0"):
            self.grid()
            self.showing = True
        Scrollbar.set(self, lo, hi)


class ScrolledText(Text):
    def __init__(self, *args, **kwargs):
        # Widgets
        self.frame = Frame(*args)
        self.scrollbar = AutoScrollbar(self.frame, command=self.yview)
        # Init
        kwargs["yscrollcommand"] = self.scrollbar.set
        Text.__init__(self, self.frame, **kwargs)
        # Layout
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        Text.grid(self, column=0, row=0, sticky="NSEW")
        self.scrollbar.grid(column=1, row=0, sticky="NSEW")

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

    def insert(self, *args, **kwargs):
        if self["state"] == "normal":
            Text.insert(self, *args, **kwargs)
        else:
            self.config(state="normal")
            Text.insert(self, *args, **kwargs)
            self.config(state="disabled")
        if self.scrollbar.get()[1] == 1:
            self.see("end")

    def append(self, *args, **kwargs):
        self.insert("end", *args, **kwargs)

    def delete(self, *args, **kwargs):
        if self["state"] == "normal":
            Text.delete(self, *args, **kwargs)
        else:
            self.configure(state="normal")
            Text.delete(self, *args, **kwargs)
            self.configure(state="disabled")

    def clear(self):
        self.delete(1.0, "end")


class ScrolledListbox(Listbox):
    def __init__(self, *args, **kwargs):
        # Widgets
        self.frame = Frame(*args)
        self.scrollbar = AutoScrollbar(self.frame, command=self.yview)
        # Init
        kwargs["yscrollcommand"] = self.scrollbar.set
        Listbox.__init__(self, self.frame, **kwargs)
        # Layout
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        Listbox.grid(self, column=0, row=0, sticky="NSEW")
        self.scrollbar.grid(column=1, row=0, sticky="NSEW")

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

    def insert(self, *args, **kwargs):
        Listbox.insert(self, *args, **kwargs)
        if self.scrollbar.get()[1] == 1:
            self.see("end")

    def clear(self):
        self.delete(0, "end")


class ScrolledFrame(Frame):
    def __init__(self, master, **kw):
        self.frame = Frame(master)
        self.canvas = Canvas(self.frame, bd=0, highlightthickness=0)
        yscrollbar = AutoScrollbar(self.frame, command=self.canvas.yview)
        Frame.__init__(self, self.canvas, **kw)

        self.canvas.config(yscrollcommand=yscrollbar.set)
        self.id = self.canvas.create_window(0, 0, window=self, anchor="nw")
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self.canvas.grid(column=0, row=0, sticky="NSEW")
        yscrollbar.grid(column=1, row=0, rowspan=2, sticky="NSEW")

        self.frame.bind("<Configure>", self.canvas_config)
        self.bind_all("<MouseWheel>", self.on_mousewheel)
        self.bind_all("<KeyPress-Up>",
                      lambda e: self.canvas.yview_scroll(-1, "units"))
        self.bind_all("<KeyPress-Down>",
                      lambda e: self.canvas.yview_scroll(1, "units"))

    def canvas_config(self, event):
        frameWidth = self.frame.winfo_width()
        canvas = self.canvas
        canvas.itemconfig(self.id, width=frameWidth)
        canvas.configure(scrollregion=canvas.bbox(self.id), width=frameWidth)

    def on_mousewheel(self, event):
        direction = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(direction, "units")

    def grid(self, **kw):
        self.frame.grid(**kw)
