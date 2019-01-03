#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
import widgets
from struct import unpack_from, pack
from collections import OrderedDict

MONOSPACE = ("Consolas", 9)
ARIAL = ("Arial, 8")

OP_CODES = {}
with open("opcodes") as f:
    for i in f.read().splitlines():
        data = i.split(";")
        OP_CODES[data[0].upper()] = data[1:]


def fancy_newlines(s, maxPerLine=128):
    s += " "
    out = []
    while s:
        line, rest = s[:maxPerLine].rsplit(" ", 1)
        out.append(line)
        s = rest + s[maxPerLine:]
    return "\n".join(out)


class App(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, border=5)
        w, h = 700, 500
        master.geometry("%dx%d+100+100" % (w, h))
        master.minsize(w, h)
        self.entryVariable = tk.StringVar()
        self.current = [0, 0]

        self.filebutton = tk.Menubutton(self, text="File", bd=0, relief="flat",
                                        activebackground="blue", activeforeground="white")
        self.filemenu = tk.Menu(self.filebutton, tearoff=0)
        self.notebook = ttk.Notebook(self)
        self.constantPool = tk.Frame(self)
        self.cpList = widgets.ScrolledListbox(
            self.constantPool, font=MONOSPACE)
        self.cpXscrollbar = widgets.AutoScrollbar(
            self.constantPool, command=self.cpList.xview, orient="horizontal")
        self.methods = tk.Frame(self)
        self.methodFrame = tk.Frame(self.methods)
        self.methodList = widgets.ScrolledListbox(
            self.methodFrame, width=26, height=5)
        self.methodLabelFrame = ttk.Labelframe(
            self.methodFrame, text="Selected instruction")
        self.methodEntry = tk.Entry(
            self.methodLabelFrame, width=16, font=MONOSPACE, textvariable=self.entryVariable)
        self.methodLabel1 = tk.Label(
            self.methodLabelFrame, anchor="w", font=ARIAL)
        self.methodLabel2 = tk.Label(
            self.methodLabelFrame, anchor="w", font=ARIAL, justify="left")
        kw = {"width": 8, "font": MONOSPACE, "activestyle": "dotbox"}
        self.methodIndexes = tk.Listbox(self.methods, **kw)
        self.methodCode = tk.Listbox(self.methods, **kw)
        self.methodExplanation = tk.Listbox(self.methods, **kw)
        self.methodXscrollbar = widgets.AutoScrollbar(
            self.methods, command=self.methodExplanation.xview, orient="horizontal")
        self.methodYscrollbar = widgets.AutoScrollbar(
            self.methods, command=self.yview_methods)

        self.filebutton.config(menu=self.filemenu)
        self.filemenu.add_command(label="Open")
        self.filemenu.add_command(label="Save")
        self.notebook.add(self.constantPool, text="Constant Pool")
        self.notebook.add(self.methods, text="Methods")
        self.cpList.config(xscrollcommand=self.cpXscrollbar.set)
        self.methodIndexes.config(yscrollcommand=self.yscroll_methods)
        self.methodCode.config(yscrollcommand=self.yscroll_methods)
        self.methodExplanation.config(
            xscrollcommand=self.methodXscrollbar.set, yscrollcommand=self.yscroll_methods)
        # app
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.filebutton.grid(column=0, row=0, sticky="NSW")
        self.notebook.grid(column=0, row=1, sticky="NSEW")
        # cp
        self.constantPool.columnconfigure(0, weight=1)
        self.constantPool.rowconfigure(0, weight=1)
        self.cpList.grid(column=0, row=0, sticky="NSEW")
        self.cpXscrollbar.grid(column=0, row=1, sticky="NSEW")
        # methods
        self.methods.columnconfigure(2, weight=1)
        self.methods.rowconfigure(1, weight=1)
        self.methodFrame.columnconfigure(1, weight=1)
        self.methodLabelFrame.columnconfigure(1, weight=1)

        self.methodFrame.grid(column=0, columnspan=3, row=0, sticky="NSEW")
        self.methodList.grid(column=0, row=0, sticky="NSEW")
        self.methodLabelFrame.grid(column=1, row=0, sticky="NSEW")
        self.methodEntry.grid(column=0, row=0, sticky="NSW")
        self.methodLabel1.grid(column=1, row=0, sticky="NSEW")
        self.methodLabel2.grid(column=0, columnspan=2, row=1, sticky="NSEW")

        self.methodIndexes.grid(column=0, row=1, sticky="NSEW", padx=2, pady=5)
        self.methodCode.grid(column=1, row=1, sticky="NSEW", padx=2, pady=5)
        self.methodExplanation.grid(
            column=2, row=1, sticky="NSEW", padx=2, pady=5)
        self.methodXscrollbar.grid(
            column=0, columnspan=3, row=2, sticky="NSEW")
        self.methodYscrollbar.grid(column=3, row=0, rowspan=3, sticky="NSEW")

        self.methodList.bind("<<ListboxSelect>>", self.select_method)
        self.methodIndexes.bind("<<ListboxSelect>>", self.select_index)
        self.methodCode.bind("<<ListboxSelect>>", self.select_index)
        self.methodExplanation.bind("<<ListboxSelect>>", self.select_index)
        self.methodEntry.bind("<Return>", self.update_code)

        # To open a file do:
        # self.f = File("CvcMinigame.xclass")
        # self.refresh()

    def yview_methods(self, *arg):
        self.methodIndexes.yview(*arg)
        self.methodCode.yview(*arg)
        self.methodExplanation.yview(*arg)

    def yscroll_methods(self, *arg):
        self.methodIndexes.yview_moveto(arg[0])
        self.methodCode.yview_moveto(arg[0])
        self.methodExplanation.yview_moveto(arg[0])
        self.methodYscrollbar.set(*arg)

    def refresh(self):
        self.code = []
        self.cpList.delete(0, "end")
        for a, i in enumerate(self.f.constantPool):
            if a == 0:
                continue
            short_name = i[0][9:]
            s = "{0:04X};{1}: {2}".format(a, short_name, self.f.format(a))
            self.cpList.insert("end", s)
        for method in self.f.methods:
            name = self.f.cp(method[1])[1]
            for attribute in method[4]:
                if len(attribute) == 5:
                    code = parse_code(attribute[3])
                    break
            self.methodList.insert("end", name)
            self.code.append(code)

    def select_method(self, _):
        self.methodIndexes.delete(0, "end")
        self.methodCode.delete(0, "end")
        self.methodExplanation.delete(0, "end")
        if self.methodList.curselection():
            self.current[0] = self.methodList.curselection()[0]
        a = 0
        for line in self.code[self.current[0]]:
            self.methodIndexes.insert("end", "%08X" % a)
            self.methodCode.insert("end", " ".join(line))
            op = OP_CODES[line[0]]
            explanation = op[0].ljust(20, " ")
            if "indexbyte" in op[1]:
                explanation += " %s" % self.f.format(
                    int(line[1] + line[2], 16))
            elif "index" in op[1]:
                explanation += " %s" % self.f.format(int(line[1], 16))
            elif "branchbyte" in op[1]:
                explanation += " pos.%08X" % (a + int(line[1] + line[2], 16))
            self.methodExplanation.insert("end", explanation)
            a += len(line)

    def select_index(self, e):
        if e and e.widget.curselection():
            self.current[1] = e.widget.curselection()[0]
        self.methodIndexes.selection_set(self.current[1])
        line = self.code[self.current[0]][self.current[1]]
        op = OP_CODES[line[0]]
        self.entryVariable.set(" ".join(line))
        self.methodLabel1.config(text="[%s]  %s" % (op[0], op[2]))
        self.methodLabel2.config(text=fancy_newlines(op[3], 100))

    def update_code(self, _):
        code = []
        for a, line in enumerate(self.code[self.current[0]]):
            if a == self.current[1]:
                line = self.methodEntry.get().split(" ")
            code.extend(line)
        raw = bytes.fromhex("".join(code))
        for attribute in self.f.methods[self.current[0]][4]:
            if len(attribute) == 5:
                attribute[3] = raw
        self.code[self.current[0]] = parse_code(raw)
        self.select_method(None)
        self.select_index(None)


class File():
    def __init__(self, path):
        self.path = path
        self.info = OrderedDict()
        with open(path, "rb") as f:
            self.data = f.read()
        self.parse()
        self.unparse()
        print(self.data == self.newData)

    def cp(self, number_or_index):
        try:
            return "#%d" % number_or_index
        except TypeError:
            return self.constantPool[int(number_or_index[1:])]

    def format(self, a):
        constant = self.constantPool[a]
        if constant[0] == "CONSTANT_String":
            return "'%s'" % self.cp(constant[1])[1]
        out = []
        for j in constant[1:]:
            if type(j) is str and j.startswith("#"):
                j = self.format(int(j[1:]))
            out.append(str(j))
        return ", ".join(out).replace("/", ".")

    def parse(self):
        d = self.data
        i = 0

        self.info["magic_number"], self.info["minor_version"], self.info["major_version"], \
            self.info["constant_pool_count"] = unpack_from(">IHHH", d, i)
        i += 10
        # ===========================================================================
        self.constantPool = [None]
        n = 1
        while n < self.info["constant_pool_count"]:
            tag = d[i]
            i += 1
            if tag == 1:
                lenght = unpack_from(">H", d, i)[0]
                i += 2
                text = d[i:i + lenght]
                i += lenght
                self.constantPool.append(("CONSTANT_Utf8", text.decode()))
            elif 3 <= tag <= 4:
                name = ("CONSTANT_Integer", "CONSTANT_Float")[tag - 3]
                value = unpack_from(">I", d, i)[0]
                i += 4
                self.constantPool.append((name, value))
            elif 5 <= tag <= 6:
                n += 1
                name = ("CONSTANT_Long", "CONSTANT_Double")[tag - 5]
                value = unpack_from(">Q", d, i)[0]
                i += 8
                self.constantPool.append((name, value))
            elif tag == 7:
                index = unpack_from(">H", d, i)[0]
                i += 2
                self.constantPool.append(("CONSTANT_Class", self.cp(index)))
            elif tag == 8:
                string_index = unpack_from(">H", d, i)[0]
                i += 2
                self.constantPool.append(
                    ("CONSTANT_String", self.cp(string_index)))
            elif 9 <= tag <= 11:
                name = ("CONSTANT_Fieldref", "CONSTANT_Methodref",
                        "CONSTANT_InterfaceMethodref")[tag - 9]
                class_index, name_and_type_index = unpack_from(">HH", d, i)
                i += 4
                self.constantPool.append(
                    (name, self.cp(class_index), self.cp(name_and_type_index)))
            elif tag == 12:
                name_index, descriptor_index = unpack_from(">HH", d, i)
                i += 4
                self.constantPool.append(
                    ("CONSTANT_NameAndType", self.cp(name_index), self.cp(descriptor_index)))
            elif tag == 15:
                reference_kind = d[i]
                i += 1
                reference_index = unpack_from(">H", d, i)[0]
                i += 2
                self.constantPool.append(
                    ("CONSTANT_MethodHandle", reference_kind, self.cp(reference_index)))
            elif tag == 16:
                descriptor_index = unpack_from(">H", d, i)[0]
                i += 2
                self.constantPool.append(
                    ("CONSTANT_MethodType", self.cp(descriptor_index)))
            elif tag == 18:
                bootstrap_method_attr_index, name_and_type_index = unpack_from(">HH", d, i)[
                    0]
                i += 4
                self.constantPool.append(("CONSTANT_InvokeDynamic", self.cp(
                    bootstrap_method_attr_index), self.cp(name_and_type_index)))
            else:
                raise Exception("!cp error [%d]" % tag)
            n += 1
        # ===========================================================================
        self.info["access_flags"], self.info["this_class"], self.info["super_class"], \
            self.info["interfaces_count"] = unpack_from(">HHHH", d, i)
        i += 8
        self.interfaces = []
        for _ in range(self.info["interfaces_count"]):
            self.interfaces.append(unpack_from(">H", d, i)[0])
            i += 2
        self.info["fields_count"] = unpack_from(">H", d, i)[0]
        i += 2
        self.fields, i = self.parse_fields(d, i, self.info["fields_count"])
        self.info["methods_count"] = unpack_from(">H", d, i)[0]
        i += 2
        self.methods, i = self.parse_fields(d, i, self.info["methods_count"])
        self.info["attributes_count"] = unpack_from(">H", d, i)[0]
        i += 2
        self.attributes, i = self.parse_attributes(
            d, i, self.info["attributes_count"])

    def parse_fields(self, d, i, count):
        fields = []
        for _ in range(count):
            access_flags, name_index, descriptor_index, attributes_count = unpack_from(
                ">HHHH", d, i)
            i += 8
            attributes, i = self.parse_attributes(d, i, attributes_count)
            fields.append((access_flags, self.cp(name_index), self.cp(
                descriptor_index), attributes_count, attributes))
        return fields, i

    def parse_attributes(self, d, i, count):
        attributes = []
        for _ in range(count):
            attribute_name_index = unpack_from(">H", d, i)[0]
            i += 2
            attribute_length = unpack_from(">I", d, i)[0]
            i += 4
            info = d[i:i + attribute_length]
            if self.constantPool[attribute_name_index][1] == "Code":
                max_stack, max_locals, code_length = unpack_from(">HHI", d, i)
                code = d[i + 8:i + 8 + code_length]
                attributes.append([self.cp(attribute_name_index), attribute_length,
                                   (max_stack, max_locals), code, info[8 + code_length:]])
            else:
                attributes.append(
                    [self.cp(attribute_name_index), attribute_length, info])
            i += attribute_length
        return attributes, i

    def unparse(self):
        d = []
        d.append(pack(">IHHH", self.info["magic_number"], self.info["minor_version"],
                      self.info["major_version"], self.info["constant_pool_count"]))
        d.append(unparse_constant_pool(self.constantPool))
        d.append(pack(">HHHH", self.info["access_flags"], self.info["this_class"],
                      self.info["super_class"], self.info["interfaces_count"]))
        for i in self.interfaces:
            d.append(pack(">H", i))
        d.append(pack(">H", self.info["fields_count"]))
        d.append(unparse_fields(self.fields))
        d.append(pack(">H", self.info["methods_count"]))
        d.append(unparse_fields(self.methods))
        d.append(pack(">H", self.info["attributes_count"]))
        d.append(unparse_attributes(self.attributes))
        self.newData = b"".join(d)


def unparse_constant_pool(constantPool):
    d = []
    for constant in constantPool:
        if constant is None:
            continue
        name = constant[0]
        if name == "CONSTANT_Utf8":
            d.append(b"\x01")
            d.append(pack(">H", len(constant[1])))
            d.append(constant[1].encode())
        elif name == "CONSTANT_Integer":
            d.append(b"\x03")
            d.append(pack(">I", constant[1]))
        elif name == "CONSTANT_Float":
            d.append(b"\x04")
            d.append(pack(">I", constant[1]))
        elif name == "CONSTANT_Long":
            d.append(b"\x05")
            d.append(pack(">Q", constant[1]))
        elif name == "CONSTANT_Double":
            d.append(b"\x06")
            d.append(pack(">Q", constant[1]))
        elif name == "CONSTANT_Class":
            d.append(b"\x07")
            d.append(pack(">H", int(constant[1][1:])))
        elif name == "CONSTANT_String":
            d.append(b"\x08")
            d.append(pack(">H", int(constant[1][1:])))
        elif name == "CONSTANT_Fieldref":
            d.append(b"\x09")
            d.append(pack(">HH", int(constant[1][1:]), int(constant[2][1:])))
        elif name == "CONSTANT_Methodref":
            d.append(b"\x0A")
            d.append(pack(">HH", int(constant[1][1:]), int(constant[2][1:])))
        elif name == "CONSTANT_InterfaceMethodref":
            d.append(b"\x0B")
            d.append(pack(">HH", int(constant[1][1:]), int(constant[2][1:])))
        elif name == "CONSTANT_NameAndType":
            d.append(b"\x0C")
            d.append(pack(">HH", int(constant[1][1:]), int(constant[2][1:])))
        elif name == "CONSTANT_MethodHandle":
            d.append(b"\x0F")
            d.append(bytes([constant[1]]))
            d.append(pack(">H", int(constant[2][1:])))
        elif name == "CONSTANT_MethodType":
            d.append(b"\x10")
            d.append(pack(">H", int(constant[1][1:])))
        elif name == "CONSTANT_InvokeDynamic":
            d.append(b"\x12")
            d.append(pack(">HH", int(constant[1][1:]), int(constant[2][1:])))
    return b"".join(d)


def unparse_attributes(attributes):
    d = []
    for attribute in attributes:
        d.append(pack(">H", int(attribute[0][1:])))
        if len(attribute) == 5:
            d.append(pack(">I", 8 + len(attribute[3]) + len(attribute[4])))
            d.append(pack(">HHI", attribute[2][0],
                          attribute[2][1], len(attribute[3])))
            d.append(attribute[3])
            d.append(attribute[4])
        else:
            d.append(pack(">I", attribute[1]))
            d.append(attribute[2])
    return b"".join(d)


def unparse_fields(fields):
    d = []
    for field in fields:
        d.append(pack(">HHHH", field[0], int(
            field[1][1:]), int(field[2][1:]), field[3]))
        d.append(unparse_attributes(field[4]))
    return b"".join(d)


def parse_code(d):
    lines = []
    i = 0
    while i < len(d):
        h = "%02X" % d[i]
        i += 1
        opc = OP_CODES[h]
        args = int(opc[1].split(":")[0])
        lines.append([h] + list("%02X" % d[i + j] for j in range(args)))
        i += args
    return lines


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Bytecode editor")
    app = App(root)
    app.pack(expand=True, fill="both")
    root.mainloop()
