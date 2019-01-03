#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import messagebox
from widgets import Pad, InfoEntry, ScrollableFrame
from cipher import Cipher


class App(tk.Frame):
    def __init__(self, master, **kw):
        tk.Frame.__init__(self, master, **kw)
        self.logPath = "Passwords log"
        self.cipher = Cipher(b"")

        self.pad = Pad(self, (4, 4), width=200,
                       height=200, takefocus=0, bg="lime")
        self.click = tk.Button(self, text="Click here",
                               command=self.start_pad, takefocus=0)
        self.masterpass = InfoEntry(self, info="MASTERPASS")
        self.passwords = ScrollableFrame(self)
        self.passwords.canvas.config(height=1)
        self.new = tk.Button(self, text="New Password", command=self.add_pass)
        self.gmail = tk.Button(self, text="-> Gmail")
        self.open = tk.Button(self, text="OPEN", command=self._open)
        self.save = tk.Button(self, text="SAVE", command=self._save)

        self.pad.grid(column=0, row=0, sticky="NSEW")
        self.click.grid(column=0, row=1, sticky="NSEW")
        self.masterpass.grid(column=0, row=2, rowspan=2,
                             sticky="NSEW", padx=10, pady=10)
        self.passwords.grid(column=1, columnspan=2, row=0,
                            rowspan=2, sticky="NSEW")
        self.new.grid(column=1, row=2, sticky="NSEW")
        self.open.grid(column=2, row=2, sticky="NSEW")
        self.gmail.grid(column=1, row=3, sticky="NSEW")
        self.save.grid(column=2, row=3, sticky="NSEW")

        self.add_pass()

    def start_pad(self):
        self.pad.clear()
        self.pad.focus_set()

    def add_pass(self):
        newFrame = tk.Frame(self.passwords, bd=1, relief="ridge")
        newName = InfoEntry(newFrame, info="Service",
                            bd=0, highlightthickness=1)
        newPass = InfoEntry(newFrame, info="Password",
                            bd=0, highlightthickness=1)
        newFrame.pack(side="top", expand=True)
        newName.pack(side="left", expand=True)
        newPass.pack(side="left", expand=True)
        return (newName, newPass)

    def _open(self):
        password = self.masterpass.get().encode("utf-8") + bytes(self.pad.order)
        self.cipher.key = password
        try:
            with open(self.logPath, "rb") as f:
                data = f.read()
            data = self.cipher.decrypt(data)
            if data:
                data = data.decode("utf-8")
                for i in self.passwords.winfo_children():
                    i.destroy()
                for i in data.split(";"):
                    values = i.split("/")
                    serviceEntry, passEntry = self.add_pass()
                    serviceEntry.insert(0, values[0])
                    passEntry.insert(0, values[1])
        except FileNotFoundError as error:
            print(error)
        except UnicodeDecodeError as error:
            print(error)

    def _save(self):
        if messagebox.askokcancel("Are you sure?", "Saving the document will overwrite previous passwords."):
            password = self.masterpass.get().encode("utf-8") + bytes(self.pad.order)
            self.cipher.key = password
            data = []
            for i in self.passwords.winfo_children():
                for j in i.winfo_children():
                    if j.info == "Service":
                        service = j.get()
                    else:
                        password = j.get()
                data.append(("%s/%s" % (service, password)).encode("utf-8"))
            data = b";".join(data)
            data = self.cipher.encrypt(data)
            with open(self.logPath, "wb") as f:
                f.write(data)


if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(0, 0)
    root.title("Key Admin")
    App(root).grid(column=0, row=0, sticky="NSEW")
    root.mainloop()
