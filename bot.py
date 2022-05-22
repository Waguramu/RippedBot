#!/usr/bin/env python
import sys
import json
import logging

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

import sqlite3


def help(update: Update, context: CallbackContext) -> None:
    """Sends explanation on how to use the bot."""
    update.message.reply_text("Hi! Use:\n"
                              "/challenge - to start ypur gym challenge\n"
                              "/help - to show help message\n"
                              "/set_weekly x - to set the amount of workouts per week\n"
                              "/post - to upload your weekly photo\n"
                              "/my_stat - to show your statistics\n"
                              "/stop - to suspend your challenge\n"
                              "/delete_data - to remove your user data\n"
                              "/show_privacy - to show the privacy policy message")


def stop(update: Update, context: CallbackContext) -> None:
    id = str(update.message.from_user["id"])
    if check_active(id):
        stop_user(id)
        update.message.reply_text("You have stopped your challenge!\n"
                                  "Very disappointing! Use /set_weekly to restart.")
    else:
        update.message.reply_text("You do not have active challenges to stop!")


def privacy_policy(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Privacy policy")


def start_challenge(update: Update, context: CallbackContext) -> None:
    id = str(update.message.from_user["id"])
    if create_user(f"{id}"):
        update.message.reply_text("Hello there! You have challenged the club to show who is the boss of the gym! \n"
                                  "Use /set_weekly <number> to register a number of days per week you'd commit.")
    else:
        update.message.reply_text("Sorry, a big bad error stopped you from challenging! Try again.")


def set_days(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("You have selected the number of days you will commit starting next week."
                              "Use /post <your gym photo> to submit your evidence.")
    id = str(update.message.from_user["id"])
    days = 0
    update_user_days(id, days)


def post_photo(update: Update, context: CallbackContext) -> None:
    id = str(update.message.from_user["id"])
    if check_active(id):
        # TODO: Check if the photo is uploaded
        # Run local face recognition
        # TODO: Check for the stats
        # Update the database
        # TODO: Check for the streak
        # Check for achievements
        pass
    else:
        update.message.reply_text("You currently do not have active challenges!\n"
                                  "To start a challenge, use /set_weekly <number> to register a number of days per "
                                  "week you'd commit.")


def check_stats(update: Update, context: CallbackContext) -> None:
    id = str(update.message.from_user["id"])
    update.message.reply_text(get_user_stats())


def delete_user_data(update: Update, context: CallbackContext) -> None:
    id = str(update.message.from_user["id"])
    if check_active(id):
        if delete_user(id):
            update.message.reply_text("Your user data was deleted")
        else:
            update.message.reply_text("Couldn't delete your data. Try again.")
    else:
        update.message.reply_text("Before deleting your data you need to stop your challenge."
                                  "Use /stop and try again afterwards.")


def create_table():
    try:
        conn = sqlite3.connect('gymbros.db')
        cursor = conn.cursor()
        cursor.execute(
            '''CREATE table IF NOT EXISTS bros(
                id TEXT PRIMARY KEY NOT NULL,
                started TEXT,
                days TEXT,
                hits INT,
                streak INT,
                long_streak INT,
                active INT);''')
        conn.close()
    except Exception as e:
        logger.error(e)


def create_user(id: str) -> bool:
    try:
        conn = sqlite3.connect('gymbros.db')
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO bros VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (id, "timestamp", 0, 0, 0, 0, 0))
        conn.close()
        return True
    except Exception as e:
        logger.error(e)
    return False


def delete_user(id: str) -> bool:
    try:
        conn = sqlite3.connect('gymbros.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bros WHERE id = ?",
                       (id,))
        conn.close()
        return True
    except Exception as e:
        logger.error(e)
    return False


def stop_user(id: str):
    try:
        conn = sqlite3.connect('gymbros.db')
        cursor = conn.cursor()
        cursor.execute(f"UPDATE bros SET started = ?, hits = ?, streak = ?, active = ? WHERE id = ?",
                       ("timestamp", 0, 0, 0, id))
        conn.close()
    except Exception as e:
        logger.error(e)


def update_user_days(id: str,  days: int):
    try:
        conn = sqlite3.connect('gymbros.db')
        cursor = conn.cursor()
        cursor.execute(f"UPDATE bros SET days = ?, active = ? WHERE id = ?",
                       (days, 1, id))
        conn.close()
    except Exception as e:
        logger.error(e)


def update_user_hits(id: str):
    try:
        conn = sqlite3.connect("gymbros.db")
        cursor = conn.cursor()
        result = cursor.execute(f"SELECT hits FROM bros WHERE id = ?",
                                (id,)).fetchone()
        if result:
            if result[0] != "":
                hits = json.loads(result[0])
            else:
                streak = cursor.execute(f"SELECT streak FROM bros WHERE id = ?",
                                        (id,)).fetchone()
                cursor.execute(f"UPDATE bros SET hits = ?, streak = ? WHERE id = ?",
                               (f"[[1, {123456789}]]", streak + 1, id))

                long_streak = cursor.execute(f"SELECT long_streak FROM bros WHERE id = ?",
                                               (id,)).fetchone()
                if long_streak < streak:
                    cursor.execute(f"UPDATE bros SET long_streak = ? WHERE id = ?",
                                   (streak, id))
        conn.close()
    except Exception as e:
        logger.error(e)


def check_active(id: str) -> bool:
    active = False
    try:
        conn = sqlite3.connect('gymbros.db')
        cursor = conn.cursor()
        result = cursor.execute(f"SELECT active FROM bros WHERE id = ?",
                                (id,)).fetchone()
        if result:
            active = result[0]
        conn.close()
    except Exception as e:
        logger.error(e)

    return active


def get_user_stats(id: str) -> str:
    stats = "There are no stats for your user"
    try:
        conn = sqlite3.connect('gymbros.db')
        cursor = conn.cursor()
        result = cursor.execute(f"SELECT hits, streak, long_streak FROM bros WHERE id = ?",
                                  (id,)).fetchone()
        if result:
            hits = json.loads(result[0])
            streak = result[1]
            long_streak = result[2]
            return f"You have done {len(hits)} workouts this week.\n" \
                   f"Your current streak is {streak} workouts.\n" \
                   f"Your longest streak is {long_streak} workouts."
        conn.close()
    except Exception as e:
        logger.error(e)
    return stats


def main(token: str) -> None:
    """Run bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("challenge", start_challenge))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("show_privacy", privacy_policy))
    dispatcher.add_handler(CommandHandler("stop", stop))
    dispatcher.add_handler(CommandHandler("delete_data", delete_user_data))
    dispatcher.add_handler(CommandHandler("set_weekly", set_days))
    dispatcher.add_handler(CommandHandler("post", post_photo))
    dispatcher.add_handler(CommandHandler("my_stat", check_stats))

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main(sys.argv[1])
