#! python3
from utilities import blit_text
import pygame as pg
from reportlab.pdfgen import canvas
from datetime import datetime
from datetime import timedelta
from math import ceil
from json import load

DAY = timedelta(1)


def create_calendar(path, iDay, fDay, margins, specialDates, holidays):
    days = [datetime(*[int(i) for i in day.split("/")][::-1])
            for day in (iDay, fDay, *specialDates, *holidays)]
    specialSet = set(days[2:2 + len(specialDates)])
    holidaySet = set(days[2 + len(specialDates):])
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
    sDayFont = pg.font.SysFont("Arial", 55)
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
            if currentDay in specialSet:
                blit_text(image, sDayFont, (x + lB, y + uB), text, gray[0],
                          color, size=(width - lB, height - uB), anchor="NW")
            else:
                blit_text(image, dayFont, (x + lB, y + uB), text, gray[0],
                          color, size=(width - lB, height - uB), anchor="NW")
            if currentDay in holidaySet:
                pos = (x + lB + (width - lB) // 2,
                       y + uB + 3 * (height - uB) // 4)
                pg.draw.circle(image, gray[230], pos, height // 4, height // 9)
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
        with open(cPath) as f:
            config = load(f)["calendar"]
    except FileNotFoundError:
        raise Exception("Missing %s" % cPath)
    create_calendar(**config)

if __name__ == "__main__":
    main()
