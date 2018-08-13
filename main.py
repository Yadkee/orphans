#! python3
import pygame as pg
from datetime import date
from json import load
from os.path import join

YEAR = date.today().year
pg.font.init()
DAY_FONT = pg.font.SysFont("Arial", 40)
TEXT_FONT = pg.font.SysFont("Times", 25)
CAKE = pg.image.load(join("images", "cake.png"))
A4 = {75: (595, 842), 96: (794, 1123),
      150: (1240, 1754), 300: (2480, 3508)}
SIZE = A4[150]
WIDTH, EXTRA_WIDTH = divmod(SIZE[0], 7)
HEADER_SIZE = 55
BD = 1
WEEK_DAYS = ("L", "M", "X", "J", "V", "S", "D")  # You may want to change this
GRAY = [(i, i, i) for i in range(256)]
WHITE = GRAY[255]
BLACK = GRAY[0]
COLORS = {"F00": (255, 0, 0), "0F0": (0, 255, 0), "00F": (0, 0, 255),
          "FF0": (255, 255, 0), "0FF": (0, 255, 255), "F0F": (255, 0, 255),
          "FFF": WHITE, "000": BLACK}


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


def str2Date(s):
    """Create a date object from a string in the format dd/mm/yyyy"""
    args = [int(i) for i in s.split("/")]
    if len(args) == 2:  # 1/1 to 1/1/{user year}
        args.append(YEAR)
    if args[2] < 1000:  # 1/1/18 to 1/1/2018
        args[2] += 2000
    return date(*args[::-1]).toordinal() - 1


def str2Birthday(s):
    day, name = s.split("-")
    return (str2Date(day), name)


def str2Day(s):
    day, color, name = s.split("-")
    return (str2Date(day), (color, name))


def smooth_color(color, isOdd):
    if isOdd:
        return [235 + i * 4 // 51 for i in color]
    else:
        return [240 + i * 3 // 51 for i in color]


def generate(_path, _iDay, _weeks, _birthdays, _periods):
    def paint_day(day):
        _date = date.fromordinal(day + 1)
        dayNumber = _date.day
        week = (day - iDay) // 7
        x = day % 7 * WIDTH
        y = HEADER_SIZE + week * HEIGHT + (dayNumber < 8)
        width = WIDTH
        height = HEIGHT - (dayNumber < 8) - 1
        if day % 7 == 6:
            width += EXTRA_WIDTH
        if week == _weeks - 1:
            height += EXTRA_HEIGHT + 1
        _color, name = periods.pop(day, (WHITE, None))
        color = smooth_color(_color, day % 7 & 1)
        if dayNumber == 1:
            text = "%d %s" % (dayNumber, _date.strftime("%b"))
            if day % 7:
                x += 1
                width -= 1
        else:
            text = str(dayNumber)
        blit_text(image, DAY_FONT, (x, y), text, BLACK,
                  color, size=(width, height), anchor="NW")
        if day in birthdays:
            offset = 50 if dayNumber > 9 else 30
            blit_text(image, TEXT_FONT, (x + offset + 40, y + 5),
                      birthdays[day], BLACK,
                      color, size=(width - offset - 40, height - 5),
                      anchor="NW")
            image.blit(CAKE, (x + offset, y + 5))
        if day in show:
            blit_text(image, TEXT_FONT, (x, y + height - 40),
                      name, BLACK, color,
                      size=(width, 40), anchor="SW")
    # Process arguments
    iDay = str2Date(_iDay) * 7 // 7
    birthdays = dict(map(str2Birthday, _birthdays))
    periods = {}
    for period in _periods:
        _iDay = str2Date(period["iDay"])
        fDay = str2Date(period.pop("fDay", period["iDay"]))
        name = period.pop("name", None)
        _color = period.pop("color", "F00")
        color = COLORS[_color]
        weekend = COLORS[period.pop("weekend", _color)]
        exceptions = set(map(str2Date, period.pop("exceptions", tuple())))
        for day in range(_iDay, fDay + 1):
            if day in exceptions:
                continue
            if day % 7 > 4:
                periods[day] = (weekend, name)
            else:
                periods[day] = (color, name)
    show = set()
    last = []
    for day, (_, name) in periods.items():
        if name is not None and name not in last[-7:]:
            show.add(day)
        last.append(name)
    # Create image
    image = pg.surface.Surface(SIZE)
    image.fill(BLACK)
    HEIGHT, EXTRA_HEIGHT = divmod(SIZE[1] - HEADER_SIZE, _weeks)
    for week in range(1, _weeks):
        y = HEADER_SIZE + week * HEIGHT - 1
        image.fill(GRAY[200], rect=((0, y), (SIZE[0], 1)))
    # Paint header
    for wDay in range(7):
        x = wDay * WIDTH
        width = WIDTH
        if wDay == 6:
            width += EXTRA_WIDTH
        color = GRAY[215 if wDay & 1 else 225]
        blit_text(image, DAY_FONT, (x, 0), WEEK_DAYS[wDay], WHITE, color,
                  size=(width, HEADER_SIZE), anchor="")
    # Blit every week
    y = HEADER_SIZE
    day = iDay
    for day in range(day, day + _weeks * 7):
        paint_day(day)
        y += HEIGHT
    pg.image.save(image, _path + ".png")
    print("PNG was created")


def main():
    """Create a calendar with the configuration set in cPath"""
    cPath = "config.json"
    try:
        with open(cPath, "rb") as f:
            config = load(f)
    except FileNotFoundError:
        raise Exception("Missing %s" % cPath)
    generate(**config)

if __name__ == "__main__":
    main()
