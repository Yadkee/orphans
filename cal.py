#! python3
import datetime
import json
import os

import common

YEAR = datetime.date.today().year
GIFT_PNG = common.pg_load(os.path.join("images", "gift.png"))
SIZE = common.A4[150]
WIDTH, EXTRA_WIDTH = divmod(SIZE[0], 7)
HEADER_HEIGHT = SIZE[1] // 35
BIRTHDAY_FONT_NAME = common.FONT1
TEXT_FONT_NAME = common.FONT2


def str2Date(s):
    """Create a date object from a string in the format dd/mm/yyyy"""
    args = [int(i) for i in s.split("/")]
    if len(args) == 2:  # 1/1 to 1/1/{user year}
        args.append(YEAR)
    if args[2] < 1000:  # 1/1/18 to 1/1/2018
        args[2] += 2000
    return datetime.date(*args[::-1]).toordinal() - 1


def str2Birthday(s):
    day, name = s.split("-")
    d, m = map(int, day.split("/"))
    return m * 100 + d, name


def get_color(s):
    return [int(s[i] + "F", 16) for i in range(3)]


def generate(iDay_, weeks_, birthdays_, periods_, smoothFactor_, path_=None):
    def paint_day(day):
        def smooth_color(color, isOdd):
            val = (255 - smoothFactor_) // 5
            if isOdd:
                return [smoothFactor_ + i * val // 51 for i in color]
            else:
                return [smoothFactor_ + 5 + i * (val - 1) // 51 for i in color]

        # Figure postion, size and color
        date = datetime.date.fromordinal(day + 1)
        dayNumber = date.day
        birthdayDate = dayNumber + date.month * 100
        week = (day - iDay) // 7
        x = day % 7 * WIDTH
        y = HEADER_HEIGHT + week * HEIGHT + (dayNumber < 8)
        width = WIDTH + (EXTRA_WIDTH if day % 7 == 6 else 0)
        height = HEIGHT - (dayNumber < 8) - 1
        if week == weeks - 1:
            height += EXTRA_HEIGHT + 1
        _color, periodName = periods.pop(day, (common.WHITE, None))
        color = smooth_color(_color, day % 7 & 1)
        # Blit day number
        if dayNumber == 1:
            dayText = "%d %s" % (dayNumber, date.strftime("%b"))
            if day % 7:
                x += 1
                width -= 1
            dayFont = common.fit_font(common.FONT_MONO, dayText,
                                      (width, height // 3))
        else:
            dayText = str(dayNumber)
            dayFont = common.fit_font(common.FONT_MONO, dayText,
                                      (width // 4, height // 3))
        daySize = dayFont.size(dayText)
        common.blit_text(image, dayFont, (x, y), dayText, common.BLACK,
                         color, size=(width, height), anchor="NW")
        topY = y
        if dayNumber == 1:
            topY += daySize[1]
        bottomY = y + height
        # Blit birthdays
        try:
            names = enumerate(birthdays[birthdayDate].split("\n"))
        except KeyError:
            names = []
        for a, name in names:
            offset = (daySize[0] if not a and dayNumber != 1 else 0)
            birthdayHeigth = min(bottomY - topY, height // 3)
            if birthdayHeigth >= 8:
                birthdayImageSide = min(int(birthdayHeigth * 0.8), width // 4)
                birthdayImageSize = (birthdayImageSide, birthdayImageSide)
                birthdayImage = common.pg_scale(GIFT_PNG, birthdayImageSize)
                image.blit(birthdayImage, (x + offset, topY))
                offset += birthdayImageSide
            birthdayWidth = (width - offset)
            birthdaySize = (birthdayWidth, birthdayImageSide)
            birthdayFont = common.fit_font(BIRTHDAY_FONT_NAME, name,
                                           birthdaySize)
            common.blit_text(image, birthdayFont, (x + offset, topY),
                             name, common.GRAY[100], color,
                             size=birthdaySize, anchor="SW")
            topY += birthdayImageSide
        # Blit period
        if day in show:
            periodText = "{%s}" % periodName
            periodSize = (width, min(bottomY - topY, height // 3))
            font = common.fit_font(TEXT_FONT_NAME, periodText, periodSize)
            common.blit_text(image, font, (x, bottomY - periodSize[1]),
                             periodText, common.BLACK, color,
                             size=periodSize, anchor="SW")

    # Process arguments
    weeks = min(max(weeks_, 1), 52)
    iDay = str2Date(iDay_) // 7 * 7
    birthdays = dict(map(str2Birthday, birthdays_))
    periods = {}
    for period in periods_:
        iDay_ = str2Date(period["iDay"])
        fDay = str2Date(period.pop("fDay", period["iDay"]))
        name = period.pop("name", None)
        if name == "":
            name = None
        _color = period.pop("color", "F00")
        color = get_color(_color)
        weekend = get_color(period.pop("weekend", _color))
        exceptions = set(map(str2Date, period.pop("exceptions", tuple())))
        for day in range(iDay_, fDay + 1):
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
    image = common.pg_surface(SIZE)
    image.fill(common.BLACK)
    HEIGHT, EXTRA_HEIGHT = divmod(SIZE[1] - HEADER_HEIGHT, weeks)
    for week in range(1, weeks):
        y = HEADER_HEIGHT + week * HEIGHT - 1
        image.fill(common.GRAY[200], rect=((0, y), (SIZE[0], 1)))
    # Paint header
    headerFont = common.fit_font(common.FONT_MONO, "0",
                                 (WIDTH // 4, HEADER_HEIGHT))
    for wDay in range(7):
        x = wDay * WIDTH
        width = WIDTH
        if wDay == 6:
            width += EXTRA_WIDTH
        color = common.GRAY[215 if wDay & 1 else 225]
        common.blit_text(image, headerFont, (x, 0), common.WEEK_DAYS[wDay],
                         common.WHITE, color,
                         size=(width, HEADER_HEIGHT), anchor="")
    # Blit every week
    for day in range(iDay, iDay + weeks * 7):
        paint_day(day)

    return common.save(image, path=path_)


if __name__ == "__main__":
    with open("cal.json") as f:
        kw = json.load(f)
    generate(**kw, path_="cal.png")
