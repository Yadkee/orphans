#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
import datetime

# calendar.mdays
MONTH_DAYS = [31, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTHS = [0, "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
          "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
DAYS = ["Lunes", "Martes", "Miércoles",
        "Jueves", "Viernes", "Sábado", "Domingo"]
DAY = datetime.timedelta(days=1)


class Calendar(tk.Frame):
    def __init__(self, master=None, **kw):
        tk.Frame.__init__(self, master, **kw)
        self.today = datetime.date.today()
        self.selection = datetime.date.today()
        self.specialDays = {}
        self.firstWeekDay = 0

        self.width = 175
        self.height = 140 + 30

        self.selectionColor = "light blue"
        self.canvasFont = ("Arial", 10)
        self.config(bg="white")

        self.topFrame = tk.Frame(
            master=self, bg=self.selectionColor, height=30)
        self.lbutton = tk.Button(master=self.topFrame,
                                 text="◀ ", command=self.prev_month)
        self.label = tk.Label(master=self.topFrame, text="junio de 2017",
                              bg=self.selectionColor, font=("Arial", 8, "bold"))
        self.rbutton = tk.Button(master=self.topFrame,
                                 text="▶", command=self.next_month)
        self.canvas = tk.Canvas(master=self, bg="white", width=self.width,
                                height=self.height - 30, bd=0, highlightthickness=0)

        self.topFrame.grid(column=0, row=0, sticky="NSEW")
        self.lbutton.place(anchor="center", relx=.1,
                           rely=.5, relwidth=.1, relheight=.5)
        self.label.place(anchor="center", relx=.5, rely=.5,
                         relwidth=.70, relheight=.5)
        self.rbutton.place(anchor="center", relx=.9,
                           rely=.5, relwidth=.1, relheight=.5)
        self.canvas.grid(column=0, row=1, sticky="NSEW")

        self.fill_month()

        self.canvas.bind("<ButtonPress-1>", self.click)
        self.canvas.bind("<B1-Motion>", self.move)
        self.label.bind("<ButtonPress-1>", self.reset)

    def reset(self, _):
        self.selection = self.today
        self.fill_month()

    def prev_month(self):
        self.selection -= DAY * MONTH_DAYS[self.selection.month - 1]
        self.fill_month()

    def next_month(self):
        initialMonth = self.selection.month
        self.selection += DAY * MONTH_DAYS[self.selection.month]
        if self.selection.month < initialMonth:
            initialMonth -= 12
        if self.selection.month - initialMonth > 1:
            self.selection -= DAY
        self.fill_month()

    def fill_month(self):
        self.today = datetime.date.today()
        self.label.config(text=MONTHS[self.selection.month].lower(
        ) + " de " + str(self.selection.year))
        self.canvas.delete("all")
        self.month = []
        starting_day = self.selection - self.selection.day * DAY
        starting_day -= (starting_day.weekday() - self.firstWeekDay) * DAY
        for i in range(6):
            for j in range(7):
                self.month.append(starting_day + DAY * (i * 7 + j))
        # Days of the week
        x = 12
        y = 10
        for i in range(7):
            self.canvas.create_text(
                x, y, text=DAYS[i][:2].lower(), fill="light gray")
            x += 25
        # Separator line and days
        x = 22
        y += 10
        self.canvas.create_line(4, y, self.width - 4, y)
        y += 5
        for a, i in enumerate(self.month):
            col, row = a % 7, a // 7
            if i in self.specialDays:
                fill, outline = self.specialDays[i]
                self.paint(col, row, fill=fill, outline=outline)
            if i == self.today:
                self.paint(col, row, outline="blue")
            if i == self.selection:
                self.select(col, row)
            if i.month == self.selection.month:
                self.canvas.create_text(x, y, text=i.day, anchor="ne")
            else:
                self.canvas.create_text(
                    x, y, text=i.day, fill="gray", anchor="ne")
            x += 25
            if col == 6:
                x = 22
                y += 20

    def move(self, event):
        self.click(event, False)

    def click(self, event, acceptOtherMonths=True):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        col, row = self.get_field(x, y)
        if col is None:
            return

        date = self.get_date(col, row)
        if self.selection.month == date.month or acceptOtherMonths:
            oldDate = self.selection
            self.selection = date
            if oldDate.month != self.selection.month:
                self.fill_month()
            else:
                self.select(col, row)

    def get_field(self, x, y):
        if not 20 < y < 140 or not 0 < x < 175:
            return (None, None)
        col = int(x / 25)
        row = int((y - 20) / 20)
        return col, row

    def get_date(self, col, row):
        return self.month[row * 7 + col]

    def select(self, col, row):
        self.paint(col, row, fill=self.selectionColor, tag="selection")

    def paint(self, col, row, fill="", outline="", tag=None):
        if tag is not None:
            self.canvas.delete(tag)
        _id = self.canvas.create_rectangle(
            col * 25, (row + 1) * 20, (col + 1) * 25 - 1, (row + 2) * 20 - 1, fill=fill, outline=outline, tag=tag)
        self.canvas.tag_lower(_id)


if __name__ == "__main__":
    root = tk.Tk()
    Calendar().pack(expand=True)
    root.mainloop()
