#! python3
import datetime
import json

import common

SIZE = common.A4[150]
# Width
WIDTH, EXTRA_WIDTH = divmod(SIZE[0], 7)
# Height
HEADER_HEIGHT = SIZE[1] // 35
PREFOOTER_HEIGHT = SIZE[1] // 20
FOOTER_HEIGHT = PREFOOTER_HEIGHT
# Background
BLUE_VALUE = 80
BACKGROUND_COLOR = (200 - BLUE_VALUE // 2, 200 - BLUE_VALUE // 2, 255)


def get_color(value, average, step):
    """
    Get a color based on a value and the average

    :param int value: Specific value
    :param int average:
    :param int step:

    :return: Color
    :rtype: tuple(int, int, int)
    """
    substract = abs(value - average) * step

    if value > average:
        return 255 - substract, 255, BLUE_VALUE
    else:
        return 255, 255 - substract, BLUE_VALUE


def generate(weeks_, data_, path_=None):
    """
    Generate and optionally save the image

    :param int weeks_: Number of weeks to paint
    :param list data_: List of tuples (day, amount)

    :param str path_: Image file path

    :return: Either the data or None
    :rtype: bytes or None
    """
    # Process arguments
    weeks = min(max(weeks_, 1), 52)
    data = {}
    weekly_values = [[], [], [], [], [], [], []]
    today = (datetime.date.today().toordinal() - 1) // 7 * 7
    starting_day = today - (weeks - 1) * 7
    for date, _amount in data_:
        if date < starting_day:
            continue
        amount = _amount / 10 if _amount % 10 else _amount // 10
        data[date] = amount
        weekly_values[date % 7].append(amount)
    non_empty_weeks = set(i // 7 for i in data)
    total_average = sum(data.values()) / len(data)
    try:
        color_step = 255 / max(abs(i - total_average) for i in data.values())
    except ZeroDivisionError:
        color_step = 0
    # Create image
    image = common.pg_surface(SIZE)
    image.fill(BACKGROUND_COLOR)
    HEIGHT = ((SIZE[1] - HEADER_HEIGHT - PREFOOTER_HEIGHT -
               FOOTER_HEIGHT) // len(non_empty_weeks))
    WEEK_HEADER_HEIGHT = HEIGHT // 4
    HEIGHT -= WEEK_HEADER_HEIGHT
    # Paint header
    header_font = common.fit_font(common.FONT_MONO, "0",
                                  (WIDTH // 4, HEADER_HEIGHT))
    for wDay in range(7):
        x = wDay * WIDTH
        width = WIDTH
        if wDay == 6:
            width += EXTRA_WIDTH
        color = common.GRAY[215 if wDay & 1 else 225]
        common.blit_text(image, header_font, (x, 0), common.WEEK_DAYS[wDay],
                         common.WHITE, color,
                         size=(width, HEADER_HEIGHT), anchor="")
    # Blit every day
    non_empty_week = -1
    iterator = iter(range(starting_day, starting_day + weeks * 7))
    for day in iterator:
        if not day % 7:
            # Check for empty weeks
            if day // 7 in non_empty_weeks:
                non_empty_week += 1
            else:
                for _ in range(6):
                    next(iterator)
                continue
        width = WIDTH
        height = HEIGHT
        x = WIDTH * (day % 7)
        y = (HEIGHT + WEEK_HEADER_HEIGHT) * non_empty_week + HEADER_HEIGHT
        if not x:
            # Print week header
            image.fill(BACKGROUND_COLOR, ((x, y),
                                          (SIZE[0], WEEK_HEADER_HEIGHT)))
            monday = datetime.date.fromordinal(day + 1).strftime("%d/%m")
            sunday = datetime.date.fromordinal(day + 7).strftime("%d/%m")
            text = "%s - %s" % (monday, sunday)
            font = common.fit_font(common.FONT1, text,
                                   (SIZE[0], int(WEEK_HEADER_HEIGHT * 0.9)))
            common.blit_text(image, font, (x, y), text, common.GRAY[100],
                             BACKGROUND_COLOR,
                             size=(SIZE[0], WEEK_HEADER_HEIGHT), anchor="")
        y += WEEK_HEADER_HEIGHT
        if day % 7 == 6:
            width += EXTRA_WIDTH
        try:
            value = data[day]
        except KeyError:
            continue
        color = get_color(value, total_average, color_step)
        if type(value) is int:
            text = "%s %d" % ("▲" if value > total_average else "▼", value)
        else:
            text = "%s %.2f" % ("▲" if value > total_average else "▼", value)
        size = (width - 4, height - 4)
        text_size = (int(width * 0.8), int(height * 0.8))
        pos = (x + 2, y + 2)
        font = common.fit_font(common.FONT_MONO, text, text_size)
        image.fill(color, (pos, size))
        common.blit_text(image, font, pos, text, common.BLACK,
                         color, size=size, anchor="")
    y = SIZE[1] - PREFOOTER_HEIGHT - FOOTER_HEIGHT
    # Paint prefooter
    prefooter_font = common.fit_font(common.FONT1, "Average:0.00",
                                     (SIZE[0], PREFOOTER_HEIGHT))
    color = get_color(total_average, total_average, color_step)
    common.blit_text(image, prefooter_font, (0, y),
                     "Average: %.2f" % total_average,
                     common.BLACK, color,
                     size=(SIZE[0], PREFOOTER_HEIGHT), anchor="")
    y += PREFOOTER_HEIGHT
    # Paint footer
    footer_font = common.fit_font(common.FONT1, "▲ 00.00",
                                  (WIDTH, FOOTER_HEIGHT))
    for wDay, i in enumerate(weekly_values):
        try:
            average = sum(i) / len(i)
        except ZeroDivisionError:
            continue
        x = wDay * WIDTH
        width = WIDTH
        if wDay == 6:
            width += EXTRA_WIDTH
        color = get_color(average, total_average, color_step)
        text = "%s %.2f" % ("▲" if average > total_average else "▼", average)
        common.blit_text(image, footer_font, (x, y), text, common.BLACK, color,
                         size=(width, FOOTER_HEIGHT), anchor="")

    return common.save(image, path=path_)


if __name__ == "__main__":
    with open("sleep.json") as f:
        kw = json.load(f)
    generate(**kw, path_="sleep.png")
