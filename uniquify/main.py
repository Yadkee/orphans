#! python3
import argparse
import os
import time

import numpy as np
import PIL.Image
import PIL.ImageChops
import PIL.ImageEnhance
import PIL.ImageOps

EXTENSIONS = {"jpg", "jpeg", "png"}
K = 10
Ks = [(i % 256) ** K for i in range(768)]
DIFFERENCE = PIL.ImageChops.difference
N = 100


def diff(i1, i2):
    h = DIFFERENCE(i1, i2).histogram()
    return sum(h[i] * Ks[i]
               for i in range(768))


def diff2(i1, i2):
    h1 = i1.histogram()
    h2 = i2.histogram()
    l1, l2 = sum(h1), sum(h2)
    return sum(abs(h1[i] / l1 - h2[i] / l2) * 100
               for i in range(768))


def diff3(i1, i2):
    h1 = i1.histogram()
    h2 = i2.histogram()
    l1, l2 = sum(h1), sum(h2)
    return int(sum(abs(sum(h1[b + i:b + i + N]) / l1 - sum(h2[b + i:b + i + N]) / l2) * 10 ** K
               for b in range(0, 256 * 3, 256) for i in range(257 - N)))


def xdiff(h):
    out = 0
    for i in range(256):
        out += h[i] * i ** 10
    return out


def intensive(path=".", constant=23, flipped=False):
    filenames = {i for i in os.listdir(path) if i.split(".")[-1] in EXTENSIONS}
    images = list()
    for filename in filenames:
        im = PIL.Image.open(filename).convert("L")
        # im.thumbnail((300, 300))
        if flipped:
            flip = im.transpose(PIL.Image.FLIP_LEFT_RIGHT)
        for name, i in images:
            h1 = diff(PIL.ImageChops.difference(im, i).histogram())
            if flipped:
                h2 = diff(PIL.ImageChops.difference(flip, i).histogram())
                lm = len(str(min(h1, h2)))
            else:
                lm = len(str(h1))
            if lm < constant:
                print("!1", lm, filename, name)

        images.append((filename, im))


def rgb(filenames, resolution, flipped, rleft, rright):
    images = []
    constant = 10
    print("Const: %d" % constant)
    res = (resolution, resolution)

    for filename in filenames:
        im = PIL.Image.open(filename)
        if im.mode != "RGB":
            print("Invalid mode '%s' >%s" % (im.mode, filename))
            continue
        im.thumbnail(res)
        for f, i in images:
            d = diff3(im, i)
            length = len(str(d)) - 1
            if length < constant:
                print("! [%2d] %s - %s" % (length, filename, f))
        images.append((filename, im))


def main(path, resolution, color, flipped, rleft, rright):
    t0 = time.time() * 1000
    filenames = {i for i in os.listdir(path) if i.split(".")[-1] in EXTENSIONS}
    if color:
        rgb(filenames, resolution, flipped, rleft, rright)
    else:
        print("Not yet")
    print("Took %d ms to complete" % (time.time() * 1000 - t0))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Uniquify")
    parser.add_argument("--path", dest="path", type=str, default=".",
                        help="Images path (default='.')")
    parser.add_argument(
        "--resolution", dest="resolution", type=int, default=300,
        help="Maximum width or height value (resolution) (default=300)")
    parser.add_argument("-c", "--color", dest="color", action="store_true",
                        help="Use RGB instead of grayscale")
    parser.add_argument("-f", "--flipped", dest="flipped", action="store_true",
                        help="Test for flipped version of the image")
    parser.add_argument("-l", "--rleft", dest="rleft", action="store_true",
                        help="Test for anti-clockwise rotated image")
    parser.add_argument("-r", "--rright", dest="rright", action="store_true",
                        help="Test for clockwise rotated image")
    args = parser.parse_args()
    main(args.path, args.resolution, args.color,
         args.flipped, args.rleft, args.rright)
