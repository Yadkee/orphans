#! python3
import pygame as pg
from datetime import date as date_class
from json import load
from os.path import join
from functools import lru_cache

YEAR = date_class.today().year
pg.font.init()
pgSysFont = pg.font.SysFont
MONO_FONT_NAME = "dejavusansmono"
BIRTHDAY_FONT_NAME = "dejavusans"
TEXT_FONT_NAME = "dejavuserif"
GIFT_PNG = pg.image.load(join("images", "gift.png"))
A4 = {75: (595, 842), 96: (794, 1123),
      150: (1240, 1754), 300: (2480, 3508)}
SIZE = A4[150]
WIDTH, EXTRA_WIDTH = divmod(SIZE[0], 7)
HEADER_HEIGHT = SIZE[1] // 35
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


@lru_cache(maxsize=None)
def fit_font(name, text, size, mn=1, mx=50, precision=1):
    """Returns a font (of type name) that fits size with text"""
    _width, _height = size
    while mx - mn > precision:
        value = (mx + mn) // 2
        width, height = pgSysFont(name, value).size(text)
        if width > _width or height > _height:
            mx = value
        else:
            mn = value
    return pgSysFont(name, (mx + mn) // 2)


def str2Date(s):
    """Create a date object from a string in the format dd/mm/yyyy"""
    args = [int(i) for i in s.split("/")]
    if len(args) == 2:  # 1/1 to 1/1/{user year}
        args.append(YEAR)
    if args[2] < 1000:  # 1/1/18 to 1/1/2018
        args[2] += 2000
    return date_class(*args[::-1]).toordinal() - 1


def str2Birthday(s):
    day, name = s.split("-")
    return (str2Date(day), name)


def str2Day(s):
    day, color, name = s.split("-")
    return (str2Date(day), (color, name))


def generate(_path, _iDay, _weeks, _birthdays, _periods, _smoothFactor):
    def paint_day(day):
        def smooth_color(color, isOdd):
            val = (255 - _smoothFactor) // 5
            if isOdd:
                return [_smoothFactor + i * val // 51 for i in color]
            else:
                return [_smoothFactor + 5 + i * (val - 1) // 51 for i in color]
        # Figure postion, size and color
        date = date_class.fromordinal(day + 1)
        dayNumber = date.day
        week = (day - iDay) // 7
        x = day % 7 * WIDTH
        y = HEADER_HEIGHT + week * HEIGHT + (dayNumber < 8)
        width = WIDTH + (EXTRA_WIDTH if day % 7 == 6 else 0)
        height = HEIGHT - (dayNumber < 8) - 1
        if week == weeks - 1:
            height += EXTRA_HEIGHT + 1
        _color, periodName = periods.pop(day, (WHITE, None))
        color = smooth_color(_color, day % 7 & 1)
        # Blit day number
        if dayNumber == 1:
            dayText = "%d %s" % (dayNumber, date.strftime("%b"))
            if day % 7:
                x += 1
                width -= 1
            dayFont = fit_font(MONO_FONT_NAME, dayText,
                               (width, height // 3))
        else:
            dayText = str(dayNumber)
            dayFont = fit_font(MONO_FONT_NAME, dayText,
                               (width // 4, height // 3))
        daySize = dayFont.size(dayText)
        blit_text(image, dayFont, (x, y), dayText, BLACK,
                  color, size=(width, height), anchor="NW")
        topY = y
        if dayNumber == 1:
            topY += daySize[1]
        bottomY = y + height
        # Blit birthdays
        try:
            names = enumerate(birthdays[day].split("\n"))
        except KeyError:
            names = []
        for a, name in names:
            offset = (daySize[0] if not a and dayNumber != 1 else 0)
            birthdayHeigth = min(bottomY - topY, height // 3)
            if birthdayHeigth >= 8:
                birthdayImageSide = min(int(birthdayHeigth * 0.8), width // 4)
                birthdayImageSize = (birthdayImageSide, birthdayImageSide)
                birthdayImage = pg.transform.scale(GIFT_PNG, birthdayImageSize)
                image.blit(birthdayImage, (x + offset, topY))
                offset += birthdayImageSide
            birthdayWidth = (width - offset)
            birthdaySize = (birthdayWidth, birthdayImageSide)
            birthdayFont = fit_font(BIRTHDAY_FONT_NAME, name, birthdaySize)
            blit_text(image, birthdayFont, (x + offset, topY),
                      name, GRAY[100], color, size=birthdaySize, anchor="SW")
            topY += birthdayImageSide
        # Blit period
        if day in show:
            periodText = "{%s}" % periodName
            periodSize = (width, min(bottomY - topY, height // 3))
            font = fit_font(TEXT_FONT_NAME, periodText, periodSize)
            blit_text(image, font, (x, bottomY - periodSize[1]),
                      periodText, BLACK, color, size=periodSize, anchor="SW")
    # Process arguments
    weeks = min(max(_weeks, 1), 52)
    iDay = str2Date(_iDay) // 7 * 7
    birthdays = dict(map(str2Birthday, _birthdays))
    periods = {}
    for period in _periods:
        _iDay = str2Date(period["iDay"])
        fDay = str2Date(period.pop("fDay", period["iDay"]))
        name = period.pop("name", None)
        if name == "":
            name = None
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
    HEIGHT, EXTRA_HEIGHT = divmod(SIZE[1] - HEADER_HEIGHT, weeks)
    for week in range(1, weeks):
        y = HEADER_HEIGHT + week * HEIGHT - 1
        image.fill(GRAY[200], rect=((0, y), (SIZE[0], 1)))
    # Paint header
    headerFont = fit_font(MONO_FONT_NAME, "0", (WIDTH // 4, HEADER_HEIGHT))
    for wDay in range(7):
        x = wDay * WIDTH
        width = WIDTH
        if wDay == 6:
            width += EXTRA_WIDTH
        color = GRAY[215 if wDay & 1 else 225]
        blit_text(image, headerFont, (x, 0), WEEK_DAYS[wDay], WHITE, color,
                  size=(width, HEADER_HEIGHT), anchor="")
    # Blit every week
    for day in range(iDay, iDay + weeks * 7):
        paint_day(day)
    pg.image.save(image, _path + ".png")
    print("PNG was created")


if __name__ == "__main__":
    try:
        with open("config.json", "rb") as f:
            config = load(f)
    except FileNotFoundError:
        raise Exception("Missing config.json")
    generate(**config)
