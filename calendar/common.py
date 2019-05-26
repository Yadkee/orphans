#! python3
import os

import pygame as pg

A4 = {
    75: (595, 842),
    96: (794, 1123),
    150: (1240, 1754),
    300: (2480, 3508)
}
WEEK_DAYS = ("L", "M", "X", "J", "V", "S", "D")  # Spanish weekday first letter
GRAY = [(i, i, i) for i in range(256)]
WHITE = GRAY[255]
BLACK = GRAY[0]
FONT1 = "dejavuserif"
FONT2 = "dejavusans"
FONT_MONO = "dejavusansmono"

pg.font.init()
pg_sys_font = pg.font.SysFont
pg_surface = pg.Surface
pg_save = pg.image.save
pg_load = pg.image.load
pg_scale = pg.transform.scale


def save(surface, path=None):
    """
    Save a surface to a path and return the data if necessary

    :param surface: Surface to be saved
    :type surface: pygame.Surface

    :param str path: File path

    :return: Either the data or None
    :rtype: bytes or None
    """
    path_ = path or os.urandom(32).hex() + ".png"
    pg_save(surface, path_)

    if not path:
        with open(path_, "rb") as f:
            data = f.read()
        os.remove(path_)
        return data
    return None


def fit_font(font, text, size, mn=1, mx=50, precision=1):
    """
    Returns a font (of type name) that fits size with text

    :param str font: Text font
    :param str text: Text content
    :param size: Text size
    :type size: tuple(int, int)

    :param int mn: Minimum value
    :param int mx: Maximum value
    :param int precision: Difference between maximum and minimum

    :return: Font of the desired size
    :rtype: pygame.font.Font
    """
    target_width, target_height = size
    while mx - mn > precision:
        mean = (mx + mn) // 2
        width, height = pg_sys_font(font, mean).size(text)

        if width > target_width or height > target_height:
            mx = mean
        else:
            mn = mean
    return pg_sys_font(font, (mx + mn) // 2)


def blit_text(surface, font, position, text, font_color,
              background_color=None, size=None, anchor="NW", fill=True):
    """
    Blits text into a pygame Surface following the parameters described below

    :param surface: Destination surface
    :type surface: pygame.Surface
    :param font: Text font
    :type font: pygame.font.Font
    :param position: Text position inside the surface
    :type position: tuple(int, int)
    :param str text: Text content
    :param font_color: Font foreground color
    :type font_color: tuple(int, int, int)

    :param background_color: Font background color
    :type background_color: tuple(int, int, int)
    :param size: Text size
    :type size: tuple(int, int)
    :param str anchor: position of the text inside its rect (N, S, W or E)
    :param bool fill: Whether to fill the background or not

    :return: None
    """
    antialiasing = True
    rendered = font.render(text, antialiasing, font_color, background_color)

    if size is None:
        surface.blit(rendered, position)
        return None

    if background_color is not None and fill:
        surface.fill(background_color, (position, size))

    text_rect = rendered.get_rect()
    # North, South and Center
    if "N" in anchor:
        text_rect.top = position[1]
    elif "S" in anchor:
        text_rect.bottom = position[1] + size[1]
    else:
        text_rect.centery = position[1] + size[1] // 2
    # West, East and Center
    if "W" in anchor:
        text_rect.left = position[0]
    elif "E" in anchor:
        text_rect.right = position[0] + size[0]
    else:
        text_rect.centerx = position[0] + size[0] // 2

    surface.blit(rendered, text_rect)
    return None
