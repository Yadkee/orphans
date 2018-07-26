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
MONTH_DAYS = [31, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTHS = ["December", "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]
BLANK = "\u00A0"


def make_menu(l):
    return IKM([[IKB(a, callback_data=b) for a, b in row] for row in l])
MENU_BIRTHDAY = make_menu([[("ADD", "B/A"), ("LIST", "B/L")]])


def make_menu_calendar(tag, year, month):
    iDay = -date(year, month, 1).weekday() + 1
    tag = "%s/%d/%d/" % (tag, year, month)
    md = MONTH_DAYS[month]
    days = [[(str(i) if 0 < i <= md else ".",
              tag + str(i) if 0 < i <= md else ".")
            for i in range(j, j + 7)] for j in range(iDay, 31, 7)]
    _tag = ">" + tag
    days.append([("-", _tag + "-m"), (MONTHS[month], _tag + ".m"),
                 ("+", _tag + "+m")])
    days.append([("-", _tag + "-y"), (str(year), _tag + ".y"),
                 ("+", _tag + "+y")])
    return make_menu(days)


def menu(bot, kw, _qData):
    qData = _qData[1:]
    tags = qData.split("/")
    if qData.startswith("B/C/"):
        sign, option = tags[4]
        year = int(tags[2])
        month = int(tags[3])
        if sign == ".":
            if option == "m":
                tag = ">B/M/%d/%%d" % year
                l = [[(MONTHS[i], tag % i) for i in range(j, j + 4)]
                     for j in range(1, 12, 4)]
                markup = make_menu(l)
            else:
                tag = ">B/Y/%%d/%d" % month
                l = [[(str(i), tag % i) for i in range(j, j + 25, 5)]
                     for j in range(1900, 2020, 25)]
                markup = make_menu(l)
        else:
            if option == "m":
                if month == 12 and sign == "+":
                    month = 1
                    year += 1
                elif month == 1 and sign == "-":
                    month = 12
                    year -= 1
                else:
                    month += 1 if sign == "+" else -1
            else:
                year += 1 if sign == "+" else -1
            markup = make_menu_calendar("B/C", year, month)
        bot.edit_message_reply_markup(**kw, reply_markup=markup)
    elif qData.startswith(("B/M/", "B/Y/")):
        year = int(tags[2])
        month = int(tags[3])
        markup = make_menu_calendar("B/C", year, month)
        bot.edit_message_reply_markup(**kw, reply_markup=markup)


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
                text = "What do you want to do related to birthdays?"
                bot.send_message(chat_id=chatId, text=text,
                                 reply_markup=MENU_BIRTHDAY)
        elif data[chatId]["waiting"]:
            tags = data[chatId]["waiting"]
            if tags[0:2] == ["B", "C"]:
                date = int(tags[3]) * 50 + int(tags[4])
                try:
                    data[chatId]["birthdays"][date].append(mText)
                except KeyError:
                    data[chatId]["birthdays"][date] = [mText]
                update_json(chatId)
                text = "Added %s's birthday" % mText
                bot.send_message(chat_id=chatId, text=text)
            data[chatId]["waiting"] = 0

    def handle_callback_query(event):
        query = event["callback_query"]
        logger.debug(query)
        qData = query["data"]
        message = query["message"]
        messageId = message["message_id"] 
        chatId = message["chat"]["id"]
        logger.info("%s -> %s" % (chatId, qData))
        kw = {"chat_id": chatId, "message_id": messageId}
        if qData.startswith(">"):
            menu(bot, kw, qData)
            return
        tags = qData.split("/")
        if tags[0] == "B":
            option = tags[1]
            if option == "A":
                text = "When do you want to add it?"
                today = date.today()
                args = ("B/C", today.year, today.month)
                bot.edit_message_text(**kw, text=text,
                                      reply_markup=make_menu_calendar(*args))
            elif option == "L":
                text = ("Birthday list:\n" +
                        "\n".join(data[chatId]["dates"]["birthdays"]))
                bot.edit_message_text(**kw, text=text)
            elif option == "C":
                text = "Last but not least, what is his/her name?"
                bot.edit_message_text(**kw, text=text)
                data[chatId]["waiting"] = tags

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
            data[user] = {"birthdays": {}, "waiting": 0}
    try:
        with open("secret/lastReminder.txt") as f:
            lastReminder = int(f.read())
    except FileNotFoundError:
        lastReminder = 0
    # Start loop
    bot = telegram.Bot(TOKEN)
    last = 0
    latency = 1  # TODO: Change latency based on time & activity
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
            _today = date.today()
            logger.info("Started reminding today things")
            # Birthdays
            today = _today.month * 50 + _today.day
            for user in USERS:
                try:
                    birthdays = data[user]["birthdays"][today]
                except KeyError:
                    continue
                for name in birthdays:
                    text = "Today is %s's birthday" % name
                    bot.send_message(chat_id=user, text=text)
            lastReminder = int(time())
            with open("secret/lastReminder.txt", "w") as f:
                f.write(str(lastReminder))
            logger.info("Finished reminding today things")

if __name__ == "__main__":
    main()
