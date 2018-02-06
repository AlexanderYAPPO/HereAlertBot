import os
import time

import sqlite3

from telegram.ext import Updater
from telegram.ext import CommandHandler


TOKEN = os.environ['ALERT_BOT_TOKEN']

def remember(bot, update):
    print(update.message.from_user.username)
    conn = sqlite3.connect('/var/lib/here_alert_bot/system.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users_in_chats VALUES (?, ?)", (update.message.chat_id, update.message.from_user.username))
        conn.commit()
    except sqlite3.IntegrityError:
        bot.send_message(chat_id=update.message.chat_id,
                         text="%s, already know you, like embarassing me?" % update.message.from_user.first_name)
        return
    finally:
        conn.close()
    bot.send_message(chat_id=update.message.chat_id,
                     text="%s, remembered you, college boy!" % update.message.from_user.first_name)

def alert(bot, update):
    conn = sqlite3.connect('/var/lib/here_alert_bot/system.db')
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM users_in_chats WHERE chat_id=?", (update.message.chat_id, ))
        users_with_at = []
        for chat_id, username in c:
            if username is None:
                continue
            users_with_at.append('@%s' % username)
        conn.commit()
    finally:
        conn.close()
    alert_message = ' '.join(users_with_at)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Atte-e-ention! %s" % alert_message)

'''
Mechanics for suggestions.
One user creates a suggestion typing something like this:
    /suggest 14:15
Then others accept or decline variant typing:
    /accept 14:15
If the variant is only one, maybe it's possible to type \'/suggest\' without parameters
'''

def MealSuggestion():
    def __init__(self, time):
        self.time = time
        self.accepted = set()
        self.declined = set()

    def accept(self, user_id):
        self.accepted.add(user_id)
        try:
            self.declined.remove(user_id)
        except KeyError:
            pass

    def decline(self, user_id):
        self.declined.add(user_id)
        try:
            self.accepted.remove(user_id)
        except KeyError:
            pass

current_suggestions = set()

def suggest(bot, update):
    try:
        suggested_time = time.strptime(update.message.text, " %H:%M")
    except ValueError:
        bot.send_message(chat_id=update.message.chat_id,
                         text="@%s, wrong time format, write something like \'/suggest 14:59\'" % update.message.from_user.username)
        return

    suggested_time_structure = time.localtime()
    suggested_time_structure.tm_hour = suggested_time.tm_hour
    suggested_time_structure.tm_minute = suggested_time.tm_minute
    if (time.mktime(suggested_time_structure) < time.time()):
        bot.send_message(chat_id=update.message.chat_id,
                         text="@%s, you cannot return the past back. Or it's just clock skew." % update.message.from_user.username)
        return

    current_suggestion = MealSuggestion(suggested_time_structure)
    if current_suggestion in current_suggestions:
        current_user_id = update.message.from_user.username
        current_suggestion.accept(current_user_id)
        bot.send_message(chat_id=update.message.chat_id,
                         text="@%s, you suggestion duplicates old one; added you as accepted." % current_user_id)
    else:
        current_suggestions.add(current_suggestion)


if __name__ == '__main__':
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher
    remember_handler = CommandHandler('remember', remember)
    dispatcher.add_handler(remember_handler)
    alert_handler = CommandHandler('alert', alert)
    dispatcher.add_handler(alert_handler)
    #suggest_handler = CommandHandler('suggest', suggest)
    #dispatcher.add_handler(suggest_handler)
    updater.start_polling()
