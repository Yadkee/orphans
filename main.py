#! python3
import os
import PIL.Image
import PIL.ImageEnhance
import PIL.ImageOps
import PIL.ImageChops

EXTENSIONS = {"jpg", "jpeg", "png"}


def diff(h):
    out = 0
    for i in range(256):
        out += h[i] * i ** 10
    return out


def intensive(path=".", constant=23, flipped=False):
    filenames = {i for i in os.listdir(path) if i.split(".")[-1] in EXTENSIONS}
    images = list()
    for filename in filenames:
        im = PIL.Image.open(filename).convert("L")
        im.thumbnail((300, 300))
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


if __name__ == "__main__":
    intensive()