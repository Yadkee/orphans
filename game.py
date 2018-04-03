#! python3
from logging import (
    basicConfig,
    getLogger,
    DEBUG)
from json import load
from PIL import Image

basicConfig(format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = getLogger("game")
logger.setLevel(DEBUG)

PIECES = ("bishop", "king", "night", "pawn", "queen", "rook")
NAMES = [i + j for i in ("b", "w") for j in PIECES]


def start_game():
    with open("config.json") as f:
        loaded = load(f)
        imageSize = int(loaded["imageSize"])
        print(imageSize)


if __name__ == "__main__":
    start_game()
