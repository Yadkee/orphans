#! python3
from logging import (
    basicConfig,
    getLogger,
    DEBUG)
from os.path import (
    join,
    exists)
from json import load
from os import mkdir

basicConfig(format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = getLogger("main")
logger.setLevel(DEBUG)


def show_error(msg):
    logger.error(msg)
    input("Press enter to exit . . .\n")
    raise Exception(msg)


def prepare():
    if not exists("media"):
        show_error("There is no media folder!")
    with open("config.json") as f:
        loaded = load(f)
        imageSize = int(loaded["imageSize"])
    if not exists("cache"):
        mkdir("cache")
        logger.info("Created cache folder")
    # Create cache for this factor
    folderPath = join("cache", str(imageSize))
    if not exists(folderPath):
        if imageSize != 256:
            # Check if Pillow is installed (this may also recognise PIL but I
            #  trust users and think that they've correctly read dependencies)
            try:
                from PIL import Image
            except ImportError:
                logger.warning("You chose a different size but Pillow is "
                                "not installed. Default size is going to "
                                "be used instead")
                imageSize = 256
                folderPath = join("cache", str(imageSize))
            else:  # Generate images
                mkdir(folderPath)
                from generate_images import generate_images
                generate_images(imageSize)
                logger.info("Cached images with a size of %d" % imageSize)
        # Copying from default
        if imageSize == 256 and not exists(folderPath):
            mkdir(folderPath)
            from generate_images import NAMES as names
            from shutil import copyfile
            sourcePath = join("media", "default", "")
            destPath = join(folderPath, "")
            for name in names:
                copyfile(sourcePath + name + ".gif", destPath + name + ".gif")
            menuPath = join("media", "menu.gif")
            copyfile(menuPath, destPath + "menu.gif")
            logger.info("Cached images from default")
    return imageSize

if __name__ == "__main__":
    prepare()
