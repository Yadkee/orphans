#! python3
import pygame as pg
from time import gmtime
from datetime import datetime, timedelta
from math import ceil, cos, pi, exp
from json import load
from os.path import join

YEAR = datetime.today().year
DAY = timedelta(1)
pg.font.init()
WEEK_DAY_FONT = pg.font.SysFont("Arial", 40)
DAY_FONT = pg.font.SysFont("Arial", 40)
TEXT_FONT = pg.font.SysFont("Times", 25)
CAKE = pg.image.load(join("images", "cake.png"))
PLANE1 = pg.image.load(join("images", "plane1.png"))
PLANE2 = pg.image.load(join("images", "plane2.png"))
A4 = {75: (595, 842), 96: (794, 1123),
      150: (1240, 1754), 300: (2480, 3508)}
SIZE = A4[150]
WIDTH = SIZE[0] // 7
HEADER_SIZE = 55
BD = 1
WEEK_DAYS = ("L", "M", "X", "J", "V", "S", "D")
GRAY = [(i, i, i) for i in range(256)]
WHITE = GRAY[255]
BLACK = GRAY[0]
away=0


def blit_text(surface, font, pos, text, fontColor, backgroundColor=None,
              size=None, anchor="NW", fill=True):
    """Blits text into a pygame Surface following the parameters"""
    antialiasing = True
    renderedFont = font.render(text, antialiasing, fontColor, backgroundColor)
    if size is not None:
        if backgroundColor is not None and fill:
            surface.fill(backgroundColor, (pos, size))
        textRect = renderedFont.get_rect()
        # North, South and Center
        if "N" in anchor:
            textRect.top = pos[1]
        elif "S" in anchor:
            textRect.bottom = pos[1] + size[1]
        else:
            textRect.centery = pos[1] + size[1] // 2
        # West, East and Center
        if "W" in anchor:
            textRect.left = pos[0]
        elif "E" in anchor:
            textRect.right = pos[0] + size[0]
        else:
            textRect.centerx = pos[0] + size[0] // 2
        surface.blit(renderedFont, textRect)
    else:
        surface.blit(renderedFont, pos)


def wave_pattern(x, y, width, height, times=2, step=1, away=None):
    """Generates a list of points following this wave pattern"""
    if away is not None:
        # Values from 1 to 10 reached first at (0, 1, 2, 3, 4, 5, 7, 9, 12, 17)
        times = int(11 - 10 * exp(-away / 7))
    M = 2 * pi * times
    out = []
    for i in range(0, width + 1, step):
        value = -cos(i / width * M) * height
        out.append((x + i, y + value))
    out.append((x + width, y - height))
    return out


def str2Date(s):
    """Create a date object from a string in the format dd/mm/yyyy"""
    args = [int(i) for i in s.split("/")]
    if len(args) == 2:  # 1/1 to 1/1/{user year}
        args.append(YEAR)
    if args[2] < 1000:  # 1/1/18 to 1/1/2018
        args[2] += 2000
    return datetime(*args[::-1])


def str2Birthday(s):
    day, name = s.split("-", 1)
    return (str2Date(day), name)


def generate(path, initialDay, weeks, birthdays, holidays, trips):
    def paint_birthday(day, x, y, width, height, color):
        blit_text(image, TEXT_FONT, (x + 80, y + 5),
                  birthdays[currentDay], BLACK,
                  color, size=(width - 80, height - 5),
                  anchor="NW")
        image.blit(CAKE, (x + 40, y + 5))

    def paint_holiday(day, x, y, width, height, color):
        pos = (x + width // 2, y + 3 * height // 4)
        pg.draw.circle(image, GRAY[230], pos, height // 4, height // 9)

    def paint_day(day, wDay, week):
        global away
        dayNumber = day.day
        x = wDay * WIDTH + (dayNumber == 1)
        y = HEADER_SIZE + week * HEIGHT
        width = WIDTH - (dayNumber == 1)
        height = HEIGHT - (dayNumber < 8)
        color = GRAY[245 if wDay & 1 else 255]
        args = (day, x, y, width, height, color)
        if dayNumber == 1:
            text = "%d %s" % (dayNumber, currentDay.strftime("%b"))
        else:
            text = str(dayNumber)

        blit_text(image, DAY_FONT, (x, y), text, BLACK,
                  color, size=(width, height), anchor="NW")
        if day in birthdays:
            paint_birthday(*args)
        if day in holidays:
            paint_holiday(*args)
        if currentDay in trips:
            destination = trips[currentDay]
            name = destination.lstrip("><")
            if name:
                blit_text(image, TEXT_FONT, (x, y + height - 38),
                          name, BLACK, color,
                          size=(width - 40, 38), anchor="E")
            if "<" in destination:
                away = 0
                image.blit(PLANE2, (x + 5, y + height - 35))
            if ">" in destination:
                away = 1
                image.blit(PLANE1, (x + width - 35, y + height - 35))
        elif away:
            pg.draw.aalines(image, BLACK, False,
                            wave_pattern(x, y + height - 13,
                                         width, 11, away=away))
            away += 1
    """Generate the calendar png"""
    imgPath = path + ".png"
    image = pg.surface.Surface(SIZE)
    image.fill(BLACK)
    HEIGHT = (SIZE[1] - HEADER_SIZE) // weeks
    # Paint header
    for wDay in range(7):
        x = wDay * WIDTH
        color = GRAY[215 if wDay & 1 else 225]
        blit_text(image, WEEK_DAY_FONT, (x, 0), WEEK_DAYS[wDay], WHITE, color,
                  size=(WIDTH, HEADER_SIZE), anchor="")
    # Blit every week
    y = HEADER_SIZE
    currentDay = initialDay
    for week in range(weeks):
        for wDay in range(7):
            paint_day(currentDay, wDay, week)
            currentDay += DAY
        y += HEIGHT
        if week != weeks - 1:
            image.fill(GRAY[200], rect=((0, y - 1), (SIZE[0], 1)))
    pg.image.save(image, imgPath)
    print("PNG was created")
    pg.font.quit()


def create_calendar(path, iDay, fDay, dates):
    """Parses the json file into python types"""
    days = str2Date(iDay), str2Date(fDay)
    birthdays = dict(map(str2Birthday, dates["birthdays"]))
    holidays = set(map(str2Date, dates["holidays"]))
    trips = dict(map(str2Birthday, dates["trips"]))
    # Adjust to mondays and sundays (first and last respectively)
    initialDay = days[0] - timedelta(days[0].weekday())
    finalDay = days[1] + timedelta(6 - days[1].weekday())
    weeks = ceil((finalDay - initialDay).days / 7)
    # Pass arguments to generate
    generate(path, initialDay, weeks, birthdays, holidays, trips)


def main():
    """Create a calendar with the configuration set in cPath"""
    cPath = "config.json"
    try:
        with open(cPath, "rb") as f:
            config = load(f)
    except FileNotFoundError:
        raise Exception("Missing %s" % cPath)
    create_calendar(**config)

if __name__ == "__main__":
    main()
