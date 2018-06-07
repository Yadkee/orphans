#! python3
from utilities import blit_text
import pygame as pg
from reportlab.pdfgen import canvas
from datetime import datetime
from datetime import timedelta
from math import ceil
from math import cos
from math import pi
from math import exp
from json import load
from os.path import join

DAY = timedelta(1)
YEAR = datetime.today().year
CAKE = pg.image.load(join("images", "cake.png"))
PLANE1 = pg.image.load(join("images", "plane1.png"))
PLANE2 = pg.image.load(join("images", "plane2.png"))


def pattern(x, y, width, height, times=2, step=1):
    M = 2 * pi * times
    out = []
    for i in range(0, width + 1, step):
        value = -cos(i / width * M) * height
        out.append((x + i, y + value))
    out.append((x + width, y - height))
    return out


def f(x):
    """Values from 1 to 10 reached first at (0, 1, 2, 3, 4, 5, 7, 9, 12, 17)"""
    e = 11 - 10 * exp(-x / 7)
    return int(e)


def _datetime(s):
    args = [int(i) for i in s.split("/")]
    if len(args) == 2:  # 1/1 to 1/1/{user year}
        args.append(YEAR)
    if args[2] < 1000:  # 1/1/18 to 1/1/2018
        args[2] += 2000
    return datetime(*args[::-1])


def _birthday(s):
    day, name = s.split("-", 1)
    return (_datetime(day), name)


def create_calendar(path, iDay, fDay, margins, dates):
    days = _datetime(iDay), _datetime(fDay)
    birthdays = dict(map(_birthday, dates["birthdays"]))
    holidays = set(map(_datetime, dates["holidays"]))
    trips = dict(map(_birthday, dates["trips"]))
    # Adjust to mondays and sundays (first and last respectively)
    initialDay = days[0] - timedelta(days[0].weekday())
    finalDay = days[1] + timedelta(6 - days[1].weekday())
    weeks = ceil((finalDay - initialDay).days / 7)
    # Set variables
    imgPath = path + ".png"
    pdfPath = path + ".pdf"
    a4 = {75: (595, 842), 96: (794, 1123),
          150: (1240, 1754), 300: (2480, 3508)}
    size = a4[150]
    wDays = ("L", "M", "X", "J", "V", "S", "D")
    gray = [(i, i, i) for i in range(256)]
    # Prepare fonts
    pg.font.init()
    wDayFont = pg.font.SysFont("Arial", 40)
    dayFont = pg.font.SysFont("Arial", 40)
    textFont = pg.font.SysFont("Times", 25)
    # Prepare surface and set some sizes
    image = pg.surface.Surface(size)
    image.fill(gray[255])
    width = size[0] // 7
    headerSize = 55
    height = (size[1] - headerSize) // weeks
    image.fill(gray[0], ((0, headerSize), (width * 7, height * weeks)))
    # Blit header
    for wDay in range(7):
        x = wDay * width
        color = gray[205 if wDay & 1 else 220]
        blit_text(image, wDayFont, (x, 0), wDays[wDay], gray[0], color,
                  size=(width, headerSize), anchor="N")
    # Blit every week
    bd = 1  # Border size
    uB = 0  # Upper border
    currentDay = initialDay
    y = headerSize
    away = 0
    for week in range(weeks):
        for wDay in range(7):
            lB = 0  # Lateral border
            x = wDay * width
            color = gray[245 if wDay & 1 else 255]
            dayNumber = currentDay.day
            if dayNumber == 1:
                lB = bd
                uB = bd
                text = "%d %s" % (dayNumber, currentDay.strftime("%b"))
            else:
                if dayNumber == 8:
                    uB = 0
                text = str(dayNumber)
            px, py = x + lB, y + uB
            blit_text(image, dayFont, (px, py), text, gray[0],
                      color, size=(width - lB, height - uB), anchor="NW")
            if currentDay in birthdays:
                blit_text(image, textFont, (x + lB + 80, y + uB + 5),
                          birthdays[currentDay], gray[0],
                          color, size=(width - lB - 80, height - uB - 5),
                          anchor="NW")
                image.blit(CAKE, (px + 40, py + 5))
            if currentDay in holidays:
                pos = (px + (width - lB) // 2,
                       py + 3 * (height - uB) // 4)
                pg.draw.circle(image, gray[230], pos, height // 4, height // 9)
            if currentDay in trips:
                destination = trips[currentDay]
                name = destination.lstrip("><")
                if name:
                    blit_text(image, textFont, (px, y + height - 38),
                              name, gray[0], color,
                              size=(width - lB - 40, 38), anchor="E")
                if "<" in destination:
                    away = 0
                    image.blit(PLANE2, (px + 5, y + height - 35))
                if ">" in destination:
                    away = 1
                    image.blit(PLANE1, (x + width - 35, y + height - 35))
            elif away:
                pg.draw.aalines(image, gray[0], False,
                                pattern(px, y + height - 13, width - lB, 11,
                                        times=f(away)))
                away += 1
            currentDay += DAY
        y += height
        if week != weeks - 1:
            image.fill(gray[200], rect=((0, y - 1), (size[0], 1)))
    pg.image.save(image, imgPath)
    print("PNG was created")
    pg.font.quit()
    # Create PDF
    try:
        pdf = canvas.Canvas(pdfPath, pagesize=size)
        xm, ym = margins
        pdf.drawImage(imgPath, xm[0], ym[1],
                      size[0] - sum(xm), size[1] - sum(ym),
                      preserveAspectRatio=False, anchor="n")
        pdf.save()
        print("PDF was created")
    except AttributeError:
        pass


def main():
    """Edit cPath to set the parameters"""
    cPath = "config.json"
    try:
        with open(cPath, "rb") as f:
            config = load(f)["calendar"]
    except FileNotFoundError:
        raise Exception("Missing %s" % cPath)
    create_calendar(**config)

if __name__ == "__main__":
    main()
