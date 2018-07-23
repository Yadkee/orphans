#! python3
import telegram
import logging
from collections import deque
from time import time
from json import load, dump
from sys import stderr, exc_info
from datetime import date

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
SPLITTABLE = str.maketrans(":.-/\\", " " * 5)


def main():
    def update_json(user):
        with open("secret/%d.json" % user, "w") as f:
            dump(data[user], f)

    def handle(event):
        logger.debug(event)
        if "edited_message" in event:
            text = "I do not support edited messages"
            chatId = event["edited_message"]["chat"]["id"]
            bot.send_message(chat_id=chatId, text=text)
            logger.info("%d edited a message I refuse to read" % chatId)
            return
        message = event["message"]
        chat = message["chat"]
        chatId = chat["id"]
        chatName = chat["first_name"]
        isAdmin = "*" if chatId == ADMIN else ""
        identifier = "%s%s (%d)" % (isAdmin, chatName, chatId)
        if chatId not in USERS:
            text = "You are not a trusted user!\nContact the person running me"
            bot.send_message(chat_id=chatId, text=text)
            logger.info("%s was not in users so was ignored" % identifier)
            return
        mtext = message["text"]
        logger.info("%s said %s" % (identifier, text))
        if mtext == "ping":
            delay = (time() - message["date"].timestamp()) * 1000
            bot.send_message(chat_id=chatId,
                             reply_to_message_id=message["message_id"],
                             text="%d ms" % delay)
        if mtext.startswith("/"):
            args = mtext[1:].translate(SPLITTABLE).split(" ")
            cmd = args.pop(0)
            if cmd == "birthday_add":
                if not args or len(args) < 3:
                    text = "Usage: /birthday_add <day/month-name>"
                    bot.send_message(chat_id=chatId, text=text)
                    return
                elif len(args) > 3:
                    args[2] = " ".join(args[2:])
                formatted = "%s/%s-%s" % tuple(args)
                data[chatId]["dates"]["birthdays"].append(formatted)
                update_json(chatId)

                text = "Added %s to birthdays" % formatted
                bot.send_message(chat_id=chatId, text=text)
            elif cmd == "birthday_list":
                text = "\n".join(data[chatId]["dates"]["birthdays"])
                bot.send_message(chat_id=chatId, text=text)
            elif cmd == "sleep_add":
                if not args or len(args) != 4:
                    text = "Usage: /sleep_add HH:MM-HH:MM"
                    bot.send_message(chat_id=chatId, text=text)
                    return
                # Not implemented yet
    logger.info("running main")
    # Load data
    data = dict()
    for user in USERS:
        try:
            with open("secret/%d.json" % user) as f:
                data[user] = load(f)
        except FileNotFoundError:
            data[user] = {"dates": {"birthdays": []}}
    try:
        with open("secret/lastReminder.txt") as f:
            lastReminder = int(f.read())
    except FileNotFoundError:
        lastReminder = 0
    # Start loop
    bot = telegram.Bot(TOKEN)
    last = 0
    latency = 2  # TODO: Change latency based on time & activity
    logger.info("Starting loop")
    while True:
        try:
            updates = bot.get_updates(offset=last + 1, timeout=300,
                                      allowedUpdates=["message"],
                                      read_latency=latency)
        except telegram.error.TimedOut:
            logger.warn("Timed out")
        else:
            for event in updates:
                last = event["update_id"]
                print()
                try:
                    handle(event)
                except Exception as e:
                    exc_type, _, exc_tb = exc_info()
                    logger.error("Line %d: (%s)%s" %
                                 (exc_tb.tb_lineno, exc_type, e))
        if lastReminder // DAY < time() // DAY:
            def _date(s):
                args = [int(i) for i in s.split("/")]
                if len(args) == 2:  # 1/1 to 1/1/{user year}
                    args.append(year)
                if args[2] < 1000:  # 1/1/18 to 1/1/2018
                    args[2] += 2000
                return date(*args[::-1])
            today = date.today()
            year = today.year
            logger.info("Started reminding today things")
            # Birthdays
            for user in USERS:
                for birthday in data[user]["dates"]["birthdays"]:
                    day, name = birthday.split("-")
                    if _date(day) == today:
                        text = "Today is %s's birthday" % name
                        bot.send_message(chat_id=user, text=text)
            lastReminder = int(time())
            with open("secret/lastReminder.txt", "w") as f:
                f.write(str(lastReminder))
            logger.info("Finished reminding today things")


if __name__ == "__main__":
    logger.info("Started")
    with open("secret/config.json") as f:
        CONFIG = load(f)
    TOKEN = CONFIG["TOKEN"]
    ADMIN = CONFIG["ADMIN"]
    USERS = CONFIG["USERS"]
    main()
