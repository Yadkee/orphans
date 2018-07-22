#! python3
import telegram
import logging
from collections import deque
from time import time
from json import load
from sys import stderr

FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
formatter = logging.Formatter(FORMAT)
logger = logging.getLogger("TeleManager")
logger.setLevel(logging.INFO)
errorHandler = logging.StreamHandler(stderr)
errorHandler.setFormatter(formatter)
fileHandler = logging.FileHandler("secret/log.txt", delay=True)
fileHandler.setFormatter(formatter)
logger.addHandler(errorHandler)
logger.addHandler(fileHandler)

DAY = 86400  # 60 * 60 * 24 // secs * mins * hours


def main():
    def handle(event):
        logger.debug(event)
        message = event["message"]
        if message is None:
            message = event["edited_message"]
        text = message["text"]
        chat = message["chat"]
        chatId = chat["id"]

        isAdmin = "*" if chatId == ADMIN else ""
        logger.info("%s%s said %s" % (isAdmin, chat["first_name"], text))
        if text == "ping":
            delay = (time() - message["date"].timestamp()) * 1000
            bot.send_message(chat_id=chatId,
                             reply_to_message_id=message["message_id"],
                             text="%d ms" % delay)

        return event["update_id"]

    bot = telegram.Bot(TOKEN)
    last = 0
    latency = 2.  # TODO: Change latency based on time & activity
    while True:
        try:
            for event in bot.get_updates(offset=last + 1, timeout=300,
                                         allowedUpdates=["message"],
                                         read_latency=latency):
                print()
                last = handle(event)
        except telegram.error.TimedOut:
            logger.warn("Timed out")
            continue

if __name__ == "__main__":
    with open("secret/config.json") as f:
        CONFIG = load(f)
    TOKEN = CONFIG["TOKEN"]
    ADMIN = CONFIG["ADMIN"]
    USERS = CONFIG["USERS"]
    main()
