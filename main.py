#! python3
import telegram
import logging
from collections import deque
from time import time
from json import load, dump
from sys import stderr

FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
formatter = logging.Formatter(FORMAT)
logger = logging.getLogger("TeleManager")
logger.setLevel(logging.DEBUG)
errorHandler = logging.StreamHandler(stderr)
errorHandler.setFormatter(formatter)
errorHandler.setLevel(logging.INFO)
fileHandler = logging.FileHandler("secret/log.txt", delay=True)
fileHandler.setFormatter(formatter)
fileHandler.setLevel(logging.DEBUG)
logger.addHandler(errorHandler)
logger.addHandler(fileHandler)

DAY = 86400  # 60 * 60 * 24 // secs * mins * hours


def main():
    def update_json(user):
        with open("secret/%d.json" % user, "w") as f:
            dump(data[user], f)

    def handle(event):
        logger.debug(event)
        message = event["message"]
        if message is None:
            message = event["edited_message"]
        text = message["text"]
        chat = message["chat"]
        chatId = chat["id"]
        if chatId not in USERS:
            logger.info("%d was not in users so was ignored" % chatId)
            return

        isAdmin = "*" if chatId == ADMIN else ""
        logger.info("%s%s said %s" % (isAdmin, chat["first_name"], text))
        if text == "ping":
            delay = (time() - message["date"].timestamp()) * 1000
            bot.send_message(chat_id=chatId,
                             reply_to_message_id=message["message_id"],
                             text="%d ms" % delay)
        if text.startswith("/"):
            args = text[1:].split(" ")
            cmd = args.pop(0)
            if cmd == "add_birthday":
                if not args or len(args) > 3:
                    text = "Usage: /add_birthday <day/month-name>"
                    bot.send_message(chat_id=chatId, text=text)
                    return
                elif len(args) == 1:
                    aux, name = args[0].split("-")
                    day, month = aux.split("/")
                elif len(args) == 2:
                    day, month = args[0].split("/")
                    name = args[1]
                elif len(args) == 3:
                    day, month, name = args
                formatted = "%s/%s-%s" % (day, month, name)
                data[chatId]["dates"]["birthdays"].append(formatted)
                update_json(chatId)

                text = "Added %s to birthdays" % formatted
                bot.send_message(chat_id=chatId, text=text)
            elif cmd == "list_birthday":
                text = "\n".join(data[chatId]["dates"]["birthdays"])
                bot.send_message(chat_id=chatId, text=text)
    # Load data
    data = dict()
    for user in USERS:
        try:
            with open("secret/%d.json" % user) as f:
                data[user] = load(f)
        except FileNotFoundError:
            data[user] = {"dates": {"birthdays": []}}
    # Start loop
    bot = telegram.Bot(TOKEN)
    last = 0
    latency = 2.  # TODO: Change latency based on time & activity
    while True:
        try:
            updates = bot.get_updates(offset=last + 1, timeout=300,
                                      allowedUpdates=["message"],
                                      read_latency=latency)
        except telegram.error.TimedOut:
            logger.warn("Timed out")
            continue
        for event in updates:
            last = event["update_id"]
            print()
            try:
                handle(event)
            except Exception as e:
                logger.error(e)

if __name__ == "__main__":
    with open("secret/config.json") as f:
        CONFIG = load(f)
    TOKEN = CONFIG["TOKEN"]
    ADMIN = CONFIG["ADMIN"]
    USERS = CONFIG["USERS"]
    main()
