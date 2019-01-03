#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import colorchooser
from widgets import ScrolledListbox, ScrolledText

POSSIBLE_TAGS = set("_" + str(i) for i in range(0xFF))


class Editor(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        self.entry = tk.Entry(self, width=30)
        self.button0 = tk.Button(self, text="X", command=self.hide)
        self.text = ScrolledText(self, width=30, height=10)
        self.button1 = tk.Button(self, text="Set", command=self.set)
        self.button2 = tk.Button(self, text="Clear", command=self.clear)

        self.item = self.master.create_window(
            0, 0, anchor="nw", window=self, state="hidden")

        self.entry.grid(column=0, row=0, sticky="NSEW")
        self.button0.grid(column=1, row=0, sticky="NSEW")
        self.text.grid(column=0, columnspan=2, row=1, sticky="NSEW")
        self.button1.grid(column=0, row=2, sticky="NSEW")
        self.button2.grid(column=1, row=2, sticky="NSEW")

    def center(self):
        cWidth, cHeight = self.master.winfo_width(), self.master.winfo_height()
        width, height = self.winfo_reqwidth(), self.winfo_reqheight()
        self.master.coords(self.item, (cWidth - width) //
                           2, (cHeight - height) // 2)

    def show(self):
        self.center()
        self.master.itemconfig(self.item, state="normal")

    def start(self, noteTag):
        self.noteTag = noteTag
        text = self.master.itemcget(self.noteTag, "text")
        title, text = text.split("\n", 1)
        self.entry.insert(0, title)
        self.text.insert("1.0", text)
        self.show()

    def hide(self):
        self.clear()
        self.master.itemconfig(self.item, state="hidden")

    def set(self):
        self.master.itemconfig(self.noteTag, text=self.entry.get(
        ) + "\n" + self.text.get("1.0", "end").rstrip())
        self.hide()

    def clear(self):
        self.entry.delete(0, "end")
        self.text.delete("1.0", "end")


class Notes(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, relief="flat", border=5)

        self.initialPos = (10, 10)
        self.initialSize = (100, 100)
        self.initialBg = "lavender"
        self.initialFg = "black"
        self.border = 1
        self.active = ""
        self.dict = {}

        self.canvas = tk.Canvas(self, bg="aqua", bd=0, highlightthickness=0)
        self.frame = tk.Frame(self, width=50)
        self.button0 = tk.Button(
            self.frame, text="New", command=self.create_note)
        self.button1 = tk.Button(
            self.frame, text="Delete", command=self.delete_note)
        self.button2 = tk.Button(
            self.frame, text="Edit", command=self.edit_note)
        self.button3 = tk.Button(self.frame, bitmap="gray75", fg=self.initialBg, activeforeground=self.initialBg,
                                 command=self.change_bg)
        self.button4 = tk.Button(self.frame, bitmap="gray12", fg=self.initialFg, activeforeground=self.initialFg,
                                 command=self.change_fg)
        self.entry0 = tk.Entry(self.frame, width=3)
        self.entry1 = tk.Entry(self.frame, width=3)
        self.listbox = ScrolledListbox(self.frame)
        self.menu = tk.Menu(self, tearoff=0)
        self.editor = Editor(self.canvas)

        self.entry0.insert(0, str(self.initialSize[0]))
        self.entry1.insert(0, str(self.initialSize[1]))
        self.menu.add_command(label="New", command=self.create_note_at_pos)

        self.canvas.grid(column=0, row=0, sticky="NSEW")
        self.frame.grid(column=1, row=0, padx=(5, 0), sticky="NSEW")
        self.button0.grid(column=0, columnspan=4,
                          row=0, ipady=5, sticky="NSEW")
        self.button1.grid(column=0, columnspan=4,
                          row=1, ipady=5, sticky="NSEW")
        self.button2.grid(column=0, columnspan=4,
                          row=2, ipady=5, sticky="NSEW")
        self.button3.grid(column=0, row=3, sticky="NSEW")
        self.button4.grid(column=1, row=3, sticky="NSEW")
        self.entry0.grid(column=2, row=3, sticky="NSEW")
        self.entry1.grid(column=3, row=3, sticky="NSEW")
        self.listbox.grid(column=0, columnspan=4,
                          row=4, ipady=5, sticky="NSEW")

        self.canvas.bind("<ButtonPress-1>", self.press)
        self.canvas.bind("<B1-Motion>", self.move)
        self.canvas.bind("<ButtonRelease-1>", self.release)
        self.canvas.bind("<Double-Button-1>", self.edit_note)
        self.canvas.bind("<ButtonPress-3>", self.popup_menu)
        self.listbox.bind("<ButtonPress-1>", self.listbox_select)
        self.entry0.bind("<Return>", self.change_size)
        self.entry1.bind("<Return>", self.change_size)

    def change_size(self, event):
        if self.active:
            cWidth, cHeight = self.canvas.winfo_width(), self.canvas.winfo_height()
            x, y = self.canvas.coords(self.active_rect())[:2]
            width = min(
                int(self.entry0.get() or self.initialSize[0]), cWidth - self.border)
            height = min(
                int(self.entry1.get() or self.initialSize[1]), cHeight - self.border)
            self.canvas.coords(self.active_rect(), x, y, x + width, y + height)
            self.canvas.coords(self.active_text(), x, y)
            self.canvas.itemconfig(self.active_text(), width=width)
            self.clamp()

    def change_bg(self):
        ask = colorchooser.askcolor(self.initialBg)
        if ask:
            if not ask[1]:
                return
            self.initialBg = ask[1]
            self.button3.config(fg=ask[1], activeforeground=ask[1])
            if self.active:
                self.canvas.itemconfig(self.active_rect(), fill=ask[1])
                index = self.listbox.get(0, "end").index(self.active)
                self.listbox.itemconfig(
                    index, background=self.initialBg, foreground=self.initialFg)

    def change_fg(self):
        ask = colorchooser.askcolor(self.initialFg)
        if ask:
            self.initialFg = ask[1]
            self.button4.config(fg=ask[1], activeforeground=ask[1])
            if self.active:
                self.canvas.itemconfig(self.active_text(), fill=ask[1])
                index = self.listbox.get(0, "end").index(self.active)
                self.listbox.itemconfig(
                    index, background=self.initialBg, foreground=self.initialFg)

    def get_tag(self):
        return (POSSIBLE_TAGS ^ set(self.dict)).pop()

    def item(self, tag, object):
        for i in self.canvas.find_withtag(tag):
            if self.canvas.type(i) == object:
                return i

    def rect(self, tag):
        return self.item(tag, "rectangle")

    def text(self, tag):
        return self.item(tag, "text")

    def active_rect(self):
        return self.rect(self.active)

    def active_text(self):
        return self.text(self.active)

    def create_note_at_pos(self):
        self.create_note(*self.lastPos)

    def create_note(self):
        x, y = self.initialPos
        self.initialPos = (x + 20, y + 20)
        self.desactivate_note()
        noteTag = self.get_tag()

        cWidth, cHeight = self.canvas.winfo_width(), self.canvas.winfo_height()
        width = min(
            int(self.entry0.get() or self.initialSize[0]), cWidth - self.border)
        height = min(
            int(self.entry1.get() or self.initialSize[1]), cHeight - self.border)
        if x + width > cWidth:
            self.initialPos = (0, len(self.dict))
            x = cWidth - width
        elif y + height > cHeight:
            self.initialPos = (len(self.dict), 0)
            y = cHeight - height

        self.canvas.create_rectangle(
            x, y, x + width, y + height, width=self.border, fill=self.initialBg, outline="black", tags=noteTag)
        self.canvas.create_text(x, y, anchor="nw", width=width,
                                text="LOL\nLinea", fill=self.initialFg, tags=noteTag)
        self.activate_note(noteTag)
        self.dict[noteTag] = "Note"
        self.listbox.insert("end", noteTag)
        self.listbox.itemconfig(
            "end", background=self.initialBg, foreground=self.initialFg)

    def delete_note(self):
        if self.active:
            self.canvas.delete(self.active)
            self.dict.pop(self.active)
            index = self.listbox.get(0, "end").index(self.active)
            self.listbox.delete(index)
            for i in self.canvas.find_all()[::-1]:
                if i != 1:
                    self.activate_note(self.canvas.gettags(i)[0])
                    break
            else:
                self.active = ""

    def edit_note(self, event=None):
        if self.active:
            self.editor.start(self.active_text())

    def desactivate_note(self):
        if self.active:
            self.canvas.itemconfigure(self.active_rect(), outline="gray")
            self.active = ""

    def activate_note(self, noteTag):
        self.desactivate_note()
        self.canvas.itemconfigure(self.rect(noteTag), outline="black")
        self.canvas.tag_raise(noteTag)
        self.active = noteTag

    def listbox_select(self, event):
        noteTag = self.listbox.get("@%d,%d" % (event.x, event.y))
        self.activate_note(noteTag)

    def popup_menu(self, event):
        self.lastPos = (event.x, event.y)
        self.menu.post(event.x_root, event.y_root)

    # Canvas dragging
    def press(self, event):
        self.desactivate_note()
        found = self.canvas.find_withtag("current")
        if found:
            self.activate_note(self.canvas.gettags(found[0])[0])
            self.lastPos = (event.x, event.y)
        else:
            self.active = ""

    def move(self, event):
        if self.active:
            x0, y0 = self.lastPos
            xf, yf = event.x, event.y
            dx, dy = xf - x0, yf - y0
            self.canvas.move(self.active, dx, dy)
            self.lastPos = (xf, yf)

    def release(self, _):
        self.clamp()
    # /Canvas dragging

    def clamp(self):
        if self.active:
            x0, y0, xf, yf = self.canvas.bbox(self.active_rect())
            cWidth, cHeight = self.canvas.winfo_width(), self.canvas.winfo_height()
            if x0 < 0:
                dx = -x0 - 1
            elif xf > cWidth:
                dx = -(xf - cWidth)
            else:
                dx = 0
            if y0 < 0:
                dy = -y0 - 1
            elif yf > cHeight:
                dy = -(yf - cHeight)
            else:
                dy = 0
            self.canvas.move(self.active, dx, dy)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Notes")
    root.resizable(0, 0)
    app = Notes(root)
    app.grid(column=0, row=0)

    root.mainloop()
