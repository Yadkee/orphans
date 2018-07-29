#! python3
import telegram
import logging
from collections import deque
from time import time, localtime, strftime
from json import load, dump
from sys import stderr
from datetime import date
from mysql.connector import connect

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

DAY = 60 * 60 * 24
DAY_IN_MINUTES = 60 * 24
SPLITTABLE = str.maketrans(":.-/\\", " " * 5)
MONTH_DAYS = [31, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTHS = ["December", "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def make_menu(l):
    return IKM([[IKB(a, callback_data=b) for a, b in row] for row in l])
MENU_BIRTHDAY = make_menu([[("ADD", "B/A"), ("LIST", "B/L")]])
MENU_REMIND = make_menu([[("ADD", "R/A"), ("LIST", "R/L")]])
MENU_REMIND_ADD = make_menu([[("HOURS FROM NOW", ">R/A/D"),
                              ("FIXED HOUR", ">R/A/F")]])
MENU_EVENT = make_menu([[("ADD", "E/A"), ("LIST", "E/L")]])


def make_menu_calendar(tag, year, month):
    iDay = -date(year, month, 1).weekday() + 1
    tag = "%s/%d/%d/" % (tag, year, month)
    md = MONTH_DAYS[month]
    days = [[(str(i) if 0 < i <= md else " ",
              tag + str(i) if 0 < i <= md else " ")
            for i in range(j, j + 7)] for j in range(iDay, 31, 7)]
    _tag = ">" + tag
    days.append([("-", _tag + "-m"), (MONTHS[month], _tag + ".m"),
                 ("+", _tag + "+m")])
    days.append([("-", _tag + "-y"), (str(year), _tag + ".y"),
                 ("+", _tag + "+y")])
    return make_menu(days)


def make_menu_hour(tag, hour, minute):
    tag = "%s/%d/%d/" % (tag, hour, minute)
    string = "%02d:%02d" % (hour, minute)
    _tag = ">" + tag
    return make_menu([
        [("-", _tag + "-60"), ("1h", " "), ("+", _tag + "+60")],
        [("-", _tag + "-30"), ("30m", " "), ("+", _tag + "+30")],
        [("-", _tag + "-5"), ("5m", " "), ("+", _tag + "+5")],
        [(string, " "), ("DONE", tag[:-1])]])


def make_menu_yesno(tag):
    return make_menu([[("YES", tag + "Y"), ("NO", tag + "N")]])


def menu(bot, kw, _qData):
    qData = _qData[1:]
    tags = qData.split("/")
    if qData.startswith("C/"):
        name = tags[1]
        year = int(tags[2])
        month = int(tags[3])
        sign, option = tags[4]
        if sign == ".":
            if option == "m":
                tag = ">M/%s/%d/%%d" % (name, year)
                l = [[(MONTHS[i], tag % i) for i in range(j, j + 4)]
                     for j in range(1, 12, 4)]
                markup = make_menu(l)
            else:
                tag = ">Y/%s/%d/%%d" % (name, month)
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
            markup = make_menu_calendar("C/" + name, year, month)
        bot.edit_message_reply_markup(**kw, reply_markup=markup)
    elif qData.startswith(("M/", "Y/")):
        name = tags[1]
        year = int(tags[2])
        month = int(tags[3])
        markup = make_menu_calendar("C/" + name, year, month)
        bot.edit_message_reply_markup(**kw, reply_markup=markup)
    elif qData.startswith("R/A/"):
        if len(tags) == 3:
            if tags[2] == "F":
                text = "Fixed time:"
                _time = localtime()
                hour, minute = _time.tm_hour, _time.tm_min
            elif tags[2] == "D":
                text = "Time from now:"
                hour, minute = 0, 30
                minute -= minute % 5
            markup = make_menu_hour(qData, hour, minute)
            bot.edit_message_text(**kw, text=text, reply_markup=markup)
        else:
            hour, minute, value = map(int, tags[3:])
            total = (hour * 60 + minute + value) % DAY_IN_MINUTES
            hour, minute = divmod(total, 60)
            markup = make_menu_hour("/".join(tags[:3]), hour, minute)
            bot.edit_message_reply_markup(**kw, reply_markup=markup)


def main():
    def update_json():
        with open("secret/general.json", "w") as f:
            dump(general, f)

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
        kw = {"chat_id": chatId, "message_id": message["message_id"]}

        if mText == "ping":
            bot.send_message(**kw, text="pong")
        elif mText.startswith("/"):
            args = mText[1:].translate(SPLITTABLE).split(" ")
            cmd = args.pop(0)
            if cmd == "birthday":
                text = "What do you want to do related to birthdays?"
                bot.send_message(chat_id=chatId, text=text,
                                 reply_markup=MENU_BIRTHDAY)
            elif cmd == "remind":
                text = "What do you want to do related to reminders?"
                bot.send_message(chat_id=chatId, text=text,
                                 reply_markup=MENU_REMIND)
            elif cmd == "event":
                text = "What do you want to do related to events?"
                bot.send_message(chat_id=chatId, text=text,
                                 reply_markup=MENU_EVENT)
            elif cmd == "cancel":
                waiting = general["waiting"].pop(chatId, False)
                if waiting:
                    text = "%s has been canceled" % waiting
                    update_json()
                else:
                    text = "No active command to cancel"
                bot.send_message(chat_id=chatId, text=text)
        elif chatId in general["waiting"]:
            waiting = general["waiting"].pop(chatId)
            tags = waiting.split("/")
            if waiting.startswith("B/C/"):
                text = ("So you want to add %s's birthday on %s?" %
                        (mText, "/".join(tags[3:1:-1])))
                markup = make_menu_yesno("B/N/%s/%s/" % (waiting[4:], mText))
                bot.send_message(chat_id=chatId, text=text,
                                 reply_markup=markup)
            elif waiting.startswith("R/A/"):
                total = int(tags[3]) * 60 + int(tags[4])
                if tags[2] == "F":
                    _time = localtime()
                    total -= _time.tm_hour * 60 + _time.tm_min
                    total %= DAY_IN_MINUTES
                if total == 0:
                    total = 24 * 60
                text = ("So you want to set a reminder in %02d:%02d?" %
                        divmod(total, 60))
                markup = make_menu_yesno("R/N/%d/%s/" % (total, mText))
                bot.send_message(chat_id=chatId, text=text,
                                 reply_markup=markup)
            elif waiting.startswith("E/C/"):
                text = ("So you want to add an event on %s?" %
                        "/".join(tags[4:1:-1]))
                markup = make_menu_yesno("E/N/%s/%s/" % (waiting[4:], mText))
                bot.send_message(chat_id=chatId, text=text,
                                 reply_markup=markup)
            update_json()

    def handle_callback_query(event):
        query = event["callback_query"]
        logger.debug(query)
        bot.answer_callback_query(callback_query_id=query["id"])
        qData = query["data"]
        if qData == " ":
            return
        message = query["message"]
        chatId = message["chat"]["id"]
        logger.info("%s -> %s" % (chatId, qData))
        kw = {"chat_id": chatId, "message_id": message["message_id"]}
        if qData.startswith(">"):
            menu(bot, kw, qData)
            return
        tags = qData.split("/")
        cmd, option = tags[:2]
        if cmd == "C":
            tags.insert(0, tags.pop(1))
            if option == "B":
                text = "Last but not least, what is his/her name?"
                bot.edit_message_text(**kw, text=text)
                tags.pop(2)  # We will not use the year
                general["waiting"][chatId] = "/".join(tags)
            elif option == "E":
                text = "Last but not least, describe your event"
                bot.edit_message_text(**kw, text=text)
                general["waiting"][chatId] = "/".join(tags)
        elif cmd == "B":
            if option == "A":
                text = "When do you want to add it?"
                today = date.today()
                args = ("C/B", today.year, today.month)
                bot.edit_message_text(**kw, text=text,
                                      reply_markup=make_menu_calendar(*args))
            elif option == "L":
                cur.execute("select date, text from birthday where user=%d "
                            "order by date;" % chatId)
                text = ["Listing birthdays:"]
                for (_date, name) in cur.fetchall():
                    month, day = divmod(_date, 100)
                    text.append("%d/%d %s" % (day, month, name))
                bot.edit_message_text(**kw, text="\n".join(text))
            elif option == "N":
                if tags[5] == "Y":
                    month, day, name = int(tags[2]), int(tags[3]), tags[4]
                    _date = month * 100 + day
                    cur.execute('insert into birthday values ('
                                '%d, %d, "%s");' % (chatId, _date, name[:32]))
                    text = "Added %s's birthday on %d/%d" % (name, day, month)
                    bot.edit_message_text(**kw, text=text)
                else:
                    event["callback_query"].data = "B/A"
                    handle_callback_query(event)
        elif cmd == "R":
            if option == "A":
                if len(tags) == 2:
                    text = "When do you want to add it?"
                    bot.edit_message_text(**kw, text=text,
                                          reply_markup=MENU_REMIND_ADD)
                else:
                    text = ("Last but not least, "
                            "give the reminder's description")
                    bot.edit_message_text(**kw, text=text)
                    general["waiting"][chatId] = "/".join(tags)
            elif option == "L":
                cur.execute("select date, text from reminder where user=%d "
                            "order by date;" % chatId)
                text = ["Listing reminders:"]
                for (_date, description) in cur.fetchall():
                    timeStr = strftime("%H:%M:%S - %d%m%Y",
                                       localtime(_date * 60))
                    text.append("%s: %s" % (timeStr, description))
                bot.edit_message_text(**kw, text="\n".join(text))
            elif option == "N":
                if tags[4] == "Y":
                    total, description = int(tags[2]), tags[3]
                    _date = (time() - 30) // 60 + total
                    cur.execute('insert into reminder values ('
                                '%d, %d, "%s");' % (chatId, _date,
                                                    description[:140]))
                    text = "Added a reminder in %02d:%02d" % divmod(total, 60)
                    bot.edit_message_text(**kw, text=text)
                else:
                    event["callback_query"].data = "R/A"
                    handle_callback_query(event)
        elif cmd == "E":
            if option == "A":
                text = "When do you want to add it?"
                today = date.today()
                args = ("C/E", today.year, today.month)
                bot.edit_message_text(**kw, text=text,
                                      reply_markup=make_menu_calendar(*args))
            elif option == "L":
                cur.execute("select date, text from event where user=%d "
                            "order by date;" % chatId)
                text = ["Listing events:"]
                for (_date, description) in cur.fetchall():
                    text.append("%s: %s" % (_date, description))
                bot.edit_message_text(**kw, text="\n".join(text))
            elif option == "N":
                if tags[6] == "Y":
                    _date = "%04d-%02d-%02d" % tuple(map(int, tags[2:5]))
                    description = tags[5]
                    cur.execute('insert into event values ('
                                '%d, "%s", "%s");' % (chatId, _date,
                                                      description[:140]))
                    text = ("Added an event at %02d/%02d/%04d" %
                            tuple(map(int, tags[4:1:-1])))
                    bot.edit_message_text(**kw, text=text)
                else:
                    event["callback_query"].data = "E/A"
                    handle_callback_query(event)

    def handle(event):
        if event["message"]:
            handle_message(event)
        elif event["callback_query"]:
            handle_callback_query(event)
        else:
            logger.warn("Received an unwanted update type, ignoring it")

    # Load data
    logger.info("Collecting data")
    with open("secret/config.json") as f:
        CONFIG = load(f)
    ADMIN = CONFIG["ADMIN"]
    USERS = CONFIG["USERS"]
    try:
        with open("secret/general.json") as f:
            general = load(f)
    except FileNotFoundError:
        general = {"lastReminder": 0, "waiting": {}}
    # Connect to database
    logger.info("Connecting to database")
    cnx = connect(**CONFIG["DB_ARGS"])
    cnx.autocommit = True
    cur = cnx.cursor()
    cur.execute("use telemanager;")
    # Start loop
    logger.info("Starting loop")
    bot = telegram.Bot(CONFIG["TOKEN"])
    lastUpdate = 0
    latency = .5  # TODO: Change latency based on time & activity
    while True:
        _time = time()
        _localtime = localtime(_time)
        day = _time // DAY
        # Daily Reminder
        if _localtime.tm_hour >= 6 and general["lastReminder"] < day:
            # Birthdays
            logger.info("Reminding birthdays")
            birthdayDay = _localtime.tm_month * 100 + _localtime.tm_day
            cur.execute("select user, text from birthday where date=%d;" %
                        birthdayDay)
            for (user, name) in cur.fetchall():
                text = "Today is %s's birthday" % name
                bot.send_message(chat_id=user, text=text)
            # Events
            logger.info("Reminding events")
            eventDay = "%04d-%02d-%02d" % (_localtime.tm_year,
                                           _localtime.tm_month,
                                           _localtime.tm_day)
            cur.execute('select user, text from event where date="%d";' %
                        eventDay)
            for (user, description) in cur.fetchall():
                text = "Today you have to do: %s" % description
                bot.send_message(chat_id=user, text=text)
            # Update lastReminder
            general["lastReminder"] = day
            update_json()
            logger.info("Finished reminding today things")
        # Minute reminder
        reminderDate = _time // 60
        cur.execute("select user, text from reminder where date<=%d;" %
                    reminderDate)
        reminders = cur.fetchall()
        if reminders:
            logger.info("Reminding [%d]" % len(reminders))
            for (user, description) in reminders:
                text = "Remember: %s" % description
                bot.send_message(chat_id=user, text=text)
            cur.execute("delete from reminder where date<=%d;" % reminderDate)
        # Update poller
        try:
            updates = bot.get_updates(offset=lastUpdate + 1, timeout=300,
                                      read_latency=latency)
        except telegram.error.TimedOut:
            logger.warn("Timed out")
        else:
            for event in updates:
                lastUpdate = event["update_id"]
                try:
                    handle(event)
                except Exception as e:
                    logger.exception(e)
    cur.close()
    cnx.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(e)
