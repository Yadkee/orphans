#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter
import time
from PIL import Image
from PIL import ImageTk

dificultad = 4
VACIO = " "
ORIGINAL = "rnbqkbnr" + \
    "pppppppp" + \
    VACIO * 32 + \
    "PPPPPPPP" + \
    "RNBQKBNR"

evaluados = {}
historial = [ORIGINAL]

imagenes = "bbishop,bking,bnight,bpawn,bqueen,brook,wbishop,wking,wnight,wpawn,wqueen,wrook".split(
    ",")

direcciones = {"B": frozenset(((-1, -1), (-1, 1), (1, -1), (1, 1))),
               "N": frozenset(((1, 2), (1, -2), (2, 1), (2, -1), (-1, 2), (-1, -2), (-2, 1), (-2, -1))),
               "R": frozenset(((0, 1), (0, -1), (1, 0), (-1, 0))),
               "Q": frozenset(((0, 1), (0, -1), (1, 0), (-1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1))),
               "K": frozenset(((0, 1), (0, -1), (1, 0), (-1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)))}

rango = {"B": 7, "N": 1, "R": 7, "Q": 7, "K": 1}

casillas = {"seleccionada": None, "opciones": None}

utilidad = {"B": -3, "b": 3, "N": -3, "n": 3, "K": -49,
            "k": 50, "Q": -9, "q": 9, "R": -5, "r": 5, "P": -1, "p": 1}


def cargar_imagenes():
    global imgs
    img_n = Image.open("images/_.png").resize((90, 90))
    img_n = ImageTk.PhotoImage(img_n)

    imgs = {VACIO: img_n}
    for i in imagenes:
        imgs[(i[1].upper() if i[0] is "w" else i[1])] = ImageTk.PhotoImage(
            Image.open("images/{}.png".format(i)).resize((90, 90), Image.ANTIALIAS))


def movimientos(tablero, a):
    pieza = tablero[a].upper()
    color = tablero[a].isupper()
    if pieza in rango:
        for dir in direcciones[pieza]:
            for i in range(1, rango[pieza] + 1):
                x = a + dir[0] * i + dir[1] * 8 * i
                if x // 8 != a // 8 + dir[1] * i:
                    break
                if not 0 <= x <= 63 or tablero[x].isupper() is color and tablero[x] is not " ":
                    break
                yield x
                if tablero[x] is VACIO:
                    continue
                elif tablero[x].isupper() is not color:
                    break
    elif pieza == "P":
        d = -1 if color else 1
        if tablero[a + d * 8] is VACIO:
            yield a + d * 8
            if (color and a // 8 == 6 or not color and a // 8 == 1) and tablero[a + d * 16] is VACIO:
                yield a + d * 16
        if tablero[a + d * 7] is not VACIO and tablero[a + d * 7].isupper() is not color and a % 8 != 7:
            yield a + d * 7
        if tablero[a + d * 9] is not VACIO and tablero[a + d * 9].isupper() is not color and a % 8 != 0:
            yield a + d * 9


def diferencia(t1, t2):
    a = 0
    for i in range(16):
        if t1[i] is not t2[i]:
            a += .01
    return a


def evaluar(tablero, turno):
    valor = diferencia(ORIGINAL, tablero)
    for i in tablero:
        if i is VACIO:
            continue
        valor += utilidad[i]
    return valor


def mover(tablero, origen, destino, dibujar=False):
    if dibujar:
        b[origen].config(image=imgs[VACIO])
        b[destino].config(image=imgs[tablero[origen]])
    tablero = tablero[:destino] + tablero[origen] + tablero[destino + 1:]
    if tablero[origen].upper() == "P" and (destino < 8 or destino >= 56):
        tablero = tablero[:8].replace(
            "P", "Q") + tablero[8:56] + tablero[56:64].replace("p", "q")
        if dibujar:
            b[destino].config(image=imgs[tablero[destino]])
    return tablero[:origen] + VACIO + tablero[origen + 1:]


def pintar(lista, color="gold"):
    for i in lista:
        b[i].config(bg=color, activebackground=color)


def repintar(lista):
    for i in lista:
        color = "plum" if (i + i // 8) & 1 else "white"
        b[i].config(bg=color, activebackground=color)


def minimax(tablero, turno_player, alfa=(-1000, None, None), beta=(1000, None, None), profundidad=5):
    if profundidad < 1:
        if tablero not in evaluados.keys():
            evaluados[tablero] = evaluar(tablero, turno_player)
        return (evaluados[tablero], None, None)
    elif turno_player:  # turno de jugador
        for a in range(64):
            if tablero[a].isupper():
                for d in movimientos(tablero, a):
                    valor = minimax(
                        mover(tablero, a, d), not turno_player, alfa, beta, profundidad - 1)[0]
                    if valor < beta[0]:
                        # jugador intenta causar el MENOR beneficio a pc
                        beta = (valor, a, d)
                    if beta[0] <= alfa[0]:
                        break
                if beta[0] <= alfa[0]:
                    break
        return beta
    else:  # turno de pc
        for a in range(64):
            if tablero[a].islower():
                for d in movimientos(tablero, a):
                    valor = minimax(
                        mover(tablero, a, d), not turno_player, alfa, beta, profundidad - 1)[0]
                    if valor > alfa[0]:
                        # pc intenta causar el MAYOR beneficio a si mismo
                        alfa = (valor, a, d)
                    if beta[0] <= alfa[0]:
                        break
                if beta[0] <= alfa[0]:
                    break
        return alfa


def movimiento_pc(tablero):
    d = None
    t0 = time.time()
    if dificultad < 1:
        for a in set(range(64)):
            if tablero[a].islower() and len(set(movimientos(tablero, a))):
                d = set(movimientos(tablero, a)).pop()
                break
    elif dificultad >= 1:
        a, d = minimax(tablero, False, profundidad=dificultad)[1:3]
    print("La maquina ha tardado {:.5f} ms".format((time.time() - t0) * 1000))
    if d is not None:
        tablero = mover(tablero, a, d, True)
    return tablero


def pulsar(a):
    def w(a=a):
        global tablero
        if casillas["seleccionada"] == None:  # seleccionar
            casillas["seleccionada"] = a
            casillas["opciones"] = frozenset(movimientos(tablero, a))
            pintar(casillas["opciones"])
        else:
            if a in casillas["opciones"]:  # mover
                historial.append(tablero)
                tablero = mover(tablero, casillas["seleccionada"], a, True)
                repintar(casillas["opciones"])
                casillas["seleccionada"] = None
                casillas["opciones"] = None

                historial.append(tablero)
                tablero = movimiento_pc(tablero)
            else:  # seleccionar
                repintar(casillas["opciones"])
                casillas["seleccionada"] = a
                casillas["opciones"] = frozenset(movimientos(tablero, a))
                pintar(casillas["opciones"])
    return w


def __pintar():
    for a, i in enumerate(tablero):
        color = "plum" if (a + a // 8) & 1 else "white"
        b[a].config(bg=color, activebackground=color, image=imgs[i])


def z(event):
    global tablero, historial
    if len(historial) <= 2:
        return 0
    historial = historial[:-1]
    tablero = historial[-1]
    __pintar()


def main():
    global tablero, b, root
    tablero = ORIGINAL

    root = tkinter.Tk()
    root.geometry("700x700")
    root.resizable(False, False)
    root.title("Ajedrez")

    cargar_imagenes()

    for i in range(8):
        tkinter.Grid.rowconfigure(root, i, weight=1)
        tkinter.Grid.columnconfigure(root, i, weight=1)

    b = []
    for a, i in enumerate(tablero):
        color = "plum" if (a + a // 8) & 1 else "white"
        img = imgs[i]
        b.append(tkinter.Button(command=pulsar(a), image=img,
                                bg=color, activebackground=color))
        b[a].grid(column=a % 8, row=a // 8, sticky="nsew")

    root.bind("z", z)
    root.mainloop()


if __name__ == "__main__":
    main()
    raise SystemExit
