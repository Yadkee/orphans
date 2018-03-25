#! python3
from utilities import blit_text
import pygame as pg
from reportlab.pdfgen import canvas
from datetime import timedelta
from math import ceil

DEFAULT_CONFIG = """// This is the config file for timetable.py
// Introduce the path name of the output files (png and pdf)
//  extension will added later. Program expects just a name
//  (e.g "-> path=Output" would generate Output.pdf and Output.png)
-> path=timetable
// Introduce the periods in the following format:
//  Hour, Minute, Duration (in minutes), Monday, Tuesday, Wednesday, etc...
// If any period is left in blank the image will also have blank spaces
//  !But remember using commas!
*PERIODS*
8,  20, 55: History, Chemistry, Maths,     Literature, P.E.
9,  15, 55: FREE,    Maths,     Chemistry, FREE,       History
11, 5,  25:      ,        ,     Only Wed,      ,
// Assign colors to your activities (or not, it's up to you)
// Use either html tag or 3 comma separated RGB values
// VALID: "#FF00DD" or "255, 0, 221"
*COLORS*
History:   230, 230, 230
Chemistry: 50, 255, 50
Maths:     #FFFF00"""


def create_timetable(path, periods, colors):
    # Set variables
    weekHas = len(periods[0]) - 3
    imgPath = path + ".png"
    pdfPath = path + ".pdf"
    a4 = {75: (595, 842), 96: (794, 1123),
          150: (1240, 1754), 300: (2480, 3508)}
    size = a4[150]
    size = size[0], size[1] // 2  # Half A4
    wDays = ("L", "M", "X", "J", "V", "S", "D")
    gray = [(i, i, i) for i in range(256)]
    # Prepare fonts
    pg.font.init()
    wDayFont = pg.font.SysFont("Arial", 40)
    periodFont = pg.font.SysFont("Arial", 40)
    activityFont = pg.font.SysFont("Arial", 40)
    # Prepare surface
    image = pg.surface.Surface(size)
    image.fill(gray[255])
    # Set sizes and border
    width = (size[0] - 200) / weekHas
    height = (size[1] - 50) / len(periods)
    bd = 5
    # Create Image
    for a, period in enumerate(["wDays"] + periods):
        if period != "wDays":
            t0 = (period[0]) * 3600 + period[1] * 60
            t1 = t0 + period[2] * 60
            y = (a - 1) * height + 50
            text = "%02d:%02d - %02d:%02d" % (t0 // 3600, t0 % 3600 // 60,
                                              t1 // 3600, t1 % 3600 // 60)
            blit_text(image, periodFont, (0, y), text, gray[0], gray[255],
                      size=(200, height), anchor="W")
        for wDay in range(weekHas):
            x = wDay * width + 200
            if period == "wDays":
                color = gray[255]
                blit_text(image, wDayFont, (x, 0), wDays[wDay], gray[0], color,
                          size=(width, 50), anchor="N")
            else:
                activity = period[wDay + 3]
                if activity in colors:
                    color = colors[activity]
                else:
                    color = gray[255]
                blit_text(image, activityFont, (x + bd, y + bd), activity,
                          gray[0], color, size=(width - 2 * bd,
                          height - 2 * bd), anchor="")
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
    cPath = "timetable_config.txt"
    try:
        with open(cPath, "rb") as f:
            config = f.read().decode()
    except FileNotFoundError:
        with open(cPath, "w") as f:
            f.write(DEFAULT_CONFIG)
        raise Exception("Introduce the configuration in %s" % cPath)

    path = "output"
    periodLooking = colorLooking = False
    periods = []
    colors = {}
    for line in config.splitlines():
        if line.startswith("//"):
            continue
        elif line.startswith("->"):
            _, path = line.split("=")
            continue
        elif line == "*PERIODS*":
            periodLooking = True
            continue
        elif line == "*COLORS*":
            periodLooking = False
            colorLooking = True
            continue
        if periodLooking:
            lineList = []
            hour, activities = line.split(":")
            for i in hour.split(","):
                lineList.append(int(i))
            for i in activities.split(","):
                lineList.append(i.strip())
            periods.append(lineList)
        elif colorLooking:
            activitiy, color = tuple(i.strip() for i in line.split(":"))
            if color.startswith("#"):
                color = tuple(int(color[1:][i:i+2], 16) for i in range(3))
            else:
                color = tuple(int(i) for i in color.split(","))
            colors[activitiy] = color
    create_timetable(path, periods, colors)

if __name__ == "__main__":
    main()
