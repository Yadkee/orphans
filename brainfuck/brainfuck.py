#! python3
# Brainfuck interpreter, assembler and dissasembler in python3 
from itertools import accumulate
from time import time

try:
    import msvcrt
except ImportError:
    get_char = input
else:
    get_char = msvcrt.getch

TAB = " " * 2


def precompile(raw):
    code = "".join(i for i in raw if i in "+-><.,[]")
    if code.count("[") != code.count("]"):
        raise SyntaxError("Incorrect use of loops")
    # Group instructions by type and get brackets
    instructions = []
    a = 0
    lc = len(code)
    while a < lc:
        i = code[a]
        if i in "+-":
            count = 0
            while a < lc and code[a] in "+-":
                count += 1 if code[a] == "+" else -1
                a += 1
            a -= 1
            instructions.append(("+", count))
        elif i in "><":
            count = 0
            while a < lc and code[a] in "><":
                count += 1 if code[a] == ">" else -1
                a += 1
            a -= 1
            instructions.append((">", count))
        else:
            if instructions[a:a + 3] == "[-]":
                a += 3
                instructions.append(("CLEAR", None))
            else:
                instructions.append((i, None))
        a += 1
    # Introduce arguments
    for a, i in enumerate(instructions):
        ins, arg = i
        if arg:
            pass
        elif ins in ".,":
            instructions[a] = (ins, a)
        elif ins == "[":
            b = a
            c = 1
            while c:
                b += 1
                if instructions[b][0] == "[":
                    c += 1
                elif instructions[b][0] == "]":
                    c -= 1
            instructions[a] = (ins, b)
        elif ins == "]":
            b = a
            c = 1
            while c:
                b -= 1
                if instructions[b][0] == "[":
                    c -= 1
                elif instructions[b][0] == "]":
                    c += 1
            instructions[a] = (ins, b)
    return instructions


def run(code, debug=False):
    instructions = precompile(code)
    array = [0]
    la = len(array)
    p = 0
    lc = len(instructions)
    a = 0
    while a < lc:
        ins, arg = instructions[a]
        if ins == "+":
            array[p] = (array[p] + arg) % 256
        elif ins == ">":
            p += arg
            while la <= p:
                array.append(0)
                la += 1
            while p < 0:
                array.insert(0, 0)
                la += 1
                p += 1
        elif ins == "[":
            if not array[p]:
                a = arg
        elif ins == "]":
            if array[p]:
                a = arg
        elif ins == ".":
            if debug:
                print(array[p], chr(array[p]))
            else:
                print(chr(array[p]), end="")
        elif ins == ",":
            char = get_char()
            if char == b"\r" or char == "":
                array[p] = 0
            elif type(char) is str:
                array[p] = ord(char[0])
            else:
                array[p] = char[0]
        elif ins == "CLEAR":
            array[p] = 0
        a += 1
    print("\n", array, sep="")
    print(la, len(array))


def disassembly(code):
    explanation = []
    instructions = precompile(code)
    tabLevel = 0
    for i in instructions:
        ins, arg = i
        if ins == "+":
            explanation.append("%sADD %d" % (TAB * tabLevel, arg))
        elif ins == ">":
            explanation.append("%sSHIFT %d" % (TAB * tabLevel, arg))
        elif ins == "[":
            explanation.append("%sWHILE:" % (TAB * tabLevel))
            tabLevel += 1
        elif ins == "]":
            tabLevel -= 1
        elif ins == ".":
            explanation.append("%sPRINT" % (TAB * tabLevel))
        elif ins == ",":
            explanation.append("%sINPUT" % (TAB * tabLevel))
    return "\n".join(explanation)


def assembly(code):
    brainfuck = []
    genLevel = 0
    for i in code.upper().splitlines():
        try:
            i = i[:i.index("/")]
        except ValueError:
            pass
        if not i:
            continue
        while i.count(TAB) < genLevel:
            genLevel -= 1
            brainfuck.append("]")
        line = "".join(i.split())
        if line.startswith("ADD"):
            if line[3:]:
                value = int(line[3:])
                if value > 0:
                    brainfuck.append("+" * value)
                else:
                    brainfuck.append("-" * -value)
            else:
                brainfuck.append(">[<+>-]<")  # Add next memory to this
        elif line.startswith("SHIFT"):
            if line[5:]:
                value = int(line[5:])
                if value > 0:
                    brainfuck.append(">" * value)
                else:
                    brainfuck.append("<" * -value)
            else:
                brainfuck.append("[>+<-]")  # Move this to next memory
        elif line.startswith("PRINT"):
            string = line[5:]
            if string:
                brainfuck.append("[-]")
                prev = 0
                for i in map(ord, string):
                    value = i - prev
                    if value > 0:
                        brainfuck.append("+" * value)
                    else:
                        brainfuck.append("-" * -value)
                    brainfuck.append(".")
                    prev = i
            else:
                brainfuck.append(".")
        elif line == "INPUT":
            brainfuck.append(",")
        elif line == "WHILE:":
            genLevel += 1
            brainfuck.append("[")
        elif line == "SUB":
            brainfuck.append(">[<->-]<")  # Substract next memory from this
        elif line == "EQ":
            brainfuck.append("[>-<-]+>[<->[-]]<")  # Is this equal to next?
        elif line == "COPY":  # Copy this to next 2 memories
            brainfuck.append("[>+>+<<-]")
        elif line == "CLEAR":
            brainfuck.append("[-]")
        else:
            brainfuck.append(line)
    brainfuck.append("]" * genLevel)
    return "".join(brainfuck)


if __name__ == "__main__":
    name = "new"
    with open(name + ".b") as f:
        code = assembly(f.read())
    with open(name + ".bf", "w") as f:
        f.write("".join(i for i in code if i in "+-><.,[]"))
    print("Running:")
    t0 = time()
    run(code, 0)
    print("%d ms" % ((time() - t0) * 1000))
    print()
    # print(disassembly(code))
