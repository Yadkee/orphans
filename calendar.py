#! python3
from utilities import blit_text
import pygame as pg
from reportlab.pdfgen import canvas
from datetime import datetime
from datetime import timedelta
from math import ceil

DEFAULT_CONFIG = """// This is the config file for calendar.py
// Introduce the path name of the output files (png and pdf)
//  extension will added later. Program expects just a name
//  (e.g "-> path=Output" would generate Output.pdf and Output.png)
-> path=calendar
// Introduce the starting date and the final one in separate lines
// Use this format: dd/mm/yyyy
1/1/1
23/2/1"""
DAY = timedelta(1)


def create_calendar(path, iDay, fDay):
    # Get iDay (force monday) and fDay (force sunday) and number of weeks
    initialDay = iDay - timedelta(iDay.weekday())
    finalDay = fDay + timedelta(6 - fDay.weekday())
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
    # Prepare surface and set some sizes
    image = pg.surface.Surface(size)
    image.fill(gray[255])
    width = size[0] / 7
    height = (size[1] - 50) / weeks
    # Create Image
    currentDay = initialDay
    y = 0
    for week in range(-1, weeks + 1):
        for wDay in range(7):
            x = wDay * width
            if week == -1:
                color = gray[205 if wDay & 1 else 220]
                blit_text(image, wDayFont, (x, y), wDays[wDay], gray[0], color,
                          size=(width, 50), anchor="N")
            else:
                color = gray[240 if wDay & 1 else 255]
                blit_text(image, dayFont, (x, y), str(currentDay.day), gray[0],
                          color, size=(width, height), anchor="NW")
                currentDay += DAY
        if week == -1:
            y += 50
        else:
            y += height
            image.fill(gray[0], rect=((0, y - 1), (size[0], 1)))
    pg.image.save(image, imgPath)
    print("PNG was created")
    pg.font.quit()
    # Create PDF
    try:
        pdf = canvas.Canvas(pdfPath, pagesize=size)
        pdf.drawImage(imgPath, 0, 0, size[0], size[1],
                      preserveAspectRatio=True, anchor="n")
        pdf.save()
        print("PDF was created")
    except AttributeError:
        pass


def main():
    """Edit cPath to set the parameters"""
    cPath = "calendar_config.txt"
    try:
        with open(cPath) as f:
            config = f.read()
    except FileNotFoundError:
        with open(cPath, "w") as f:
            f.write(DEFAULT_CONFIG)
        raise Exception("Introduce the configuration in %s" % cPath)

    days = []
    path = "output"
    for line in config.splitlines():
        if line.startswith("//"):
            continue
        elif line.startswith("->"):
            _, path = line.split("=")
            continue
        try:
            day, month, year = tuple(int(i) for i in line.split("/"))
        except ValueError:
            raise Exception("Days are not in the correct format")
        days.append(datetime(year, month, day))
    if len(days) < 2:
        raise Exception("There must be at least 2 dates in the config file")
    create_calendar(path, days[0], days[1])

if __name__ == "__main__":
    main()
