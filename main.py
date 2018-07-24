#! python3
import telegram
import logging
from collections import deque
from time import time
from json import load, dump
from sys import stderr
from datetime import date

IKB = telegram.InlineKeyboardButton
IKM = telegram.InlineKeyboardMarkup

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
MONTH_DAYS = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def main():
    def update_json(user):
        with open("secret/%d.json" % user, "w") as f:
            dump(data[user], f)

    def handle_message(event):
        logger.debug(event)
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
        mText = message["text"]
        if mText is None:
            logger.warn("Received message is not text")
            return
        logger.info("%s said %s" % (identifier, mText))

        if mText == "ping":
            bot.send_message(chat_id=chatId, text="pong",
                             reply_to_message_id=message["message_id"])
        elif mText.startswith("/"):
            args = mText[1:].translate(SPLITTABLE).split(" ")
            cmd = args.pop(0)
            if cmd == "birthday":
                text = "-Birthday-\nWhat do you want to do?"
                buttons = [
                    [IKB("Add", callback_data="add"),
                     IKB("List", callback_data="list")]
                ]
                bot.send_message(chat_id=chatId, text=text,
                                 reply_markup=IKM(buttons))
        else:
            reply = message["reply_to_message"]
            if (reply and
                    reply["text"].startswith("-Birthday add (") and
                    "/" in reply["text"]):
                date = reply["text"].split("(")[1].split(")")[0]
                name = mText
                formatted = "%s-%s" % (date, name)
                data[chatId]["dates"]["birthdays"].append(formatted)
                update_json(chatId)

                text = "Added %s to birthdays" % formatted
                bot.send_message(chat_id=chatId, text=text)
            else:
                bot.send_message(chat_id=chatId, text="Received")

    def handle_callback_query(event):
        query = event["callback_query"]
        logger.debug(query)
        qData = query["data"]
        message = query["message"]
        tag = message["text"].split("\n")[0]
        chatId = message["chat"]["id"]
        logger.info("Query: %s %s" % (qData, tag))
        if tag == "-Birthday-":
            if qData == "list":
                text = ("-Birthday list-\n" +
                        "\n".join(data[chatId]["dates"]["birthdays"]))
                bot.edit_message_text(chat_id=chatId, text=text,
                                      message_id=message["message_id"])
            elif qData == "add":
                text = "-Birthday add-\nChoose a month"
                buttons = [
                    [IKB(MONTHS[i], callback_data=str(i))
                        for i in range(j, j + 4)]
                    for j in range(0, 12, 4)
                ]
                bot.edit_message_text(chat_id=chatId, text=text,
                                      message_id=message["message_id"],
                                      reply_markup=IKM(buttons))
        elif tag == "-Birthday add-":
            month = int(qData)
            md = MONTH_DAYS[month]
            text = "-Birthday add (%s)-\nChoose a day" % MONTHS[month]
            buttons = [
                [IKB(str(i) if i <= md else ".",
                     callback_data=str(i) if i <= md else ".")
                    for i in range(j, j + 7)]
                for j in range(1, 31, 7)
            ]
            bot.edit_message_text(chat_id=chatId, text=text,
                                  message_id=message["message_id"],
                                  reply_markup=IKM(buttons))
        elif tag.startswith("-Birthday add (") and qData != ".":
            monthName = tag.split("(")[1].split(")")[0]
            month = MONTHS.index(monthName) + 1
            day = int(qData)
            text = "-Birthday add (%d/%d)-\nReply with a name" % (day, month)
            bot.edit_message_text(chat_id=chatId, text=text,
                                  message_id=message["message_id"])
        bot.answer_callback_query(callback_query_id=query["id"])

    def handle(event):
        if event["message"]:
            handle_message(event)
        elif event["callback_query"]:
            handle_callback_query(event)
        else:
            logger.warn("Received an unwanted update type, ignoring it")

    # Load data
    logger.info("Started collecting data")
    with open("secret/config.json") as f:
        CONFIG = load(f)
    TOKEN = CONFIG["TOKEN"]
    ADMIN = CONFIG["ADMIN"]
    USERS = CONFIG["USERS"]

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
    logger.info("Started loop")
    while True:
        # Update poller
        try:
            updates = bot.get_updates(offset=last + 1, timeout=300,
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
                    logger.exception(e)
        # Reminder (18k seconds [5h] less let this happen at 6 am on utc +1)
        if lastReminder // DAY < (time() - 18000) // DAY:
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
    main()
