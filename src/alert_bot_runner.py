from multiprocessing import Lock, Process
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
    /decline 14:15
If the variant is only one, maybe it's possible to type \'/suggest\' without parameters
'''

# Map of actual MealSuggestions containing info about accepted/declined users
current_suggestions = {}

def MealSuggestion():
    def __init__(self, time, bot, chat_id):
        self.time = time
        self.accepted = set()
        self.declined = set()
        self.bot = bot
        self.chat_id = chat_id
        self.lock = Lock()
        Process(target=informer, args=(self,)).start()

    def accept_user(self, user_id):
        self.lock.acquire()
        self.accepted.add(user_id)
        try:
            self.declined.remove(user_id)
        except KeyError:
            pass
        self.lock.release()

    def decline_user(self, user_id):
        self.lock.acquire()
        self.declined.add(user_id)
        try:
            self.accepted.remove(user_id)
        except KeyError:
            pass
        self.lock.release()

    def get_info(self):
        return self.accepted, self.declined

    def informer(self):
        # Time interval the reminder works
        notification_interval = 300
        try:
            wake_time = time.mktime(self.time) - notification_interval
            current_time = time.time()
            while current_time < wake_time:
                current_time = time.time()
                time.sleep(wake_time - current_time)
        except (OverflowError, ValueError) as error:
            # Something extreamly wrong is going now
            suggested_time_printed = time.strftime("%H:%M", self.time)
            self.bot.send_message(chat_id=self.chat_id,
                                  text="Error occured while notifying about the meal at %s, removing the suggestion" % suggested_time_printed)
            del current_suggestions[self.time]
            return

        self.lock.acquire()
        usernames_with_at = []
        for user in self.accepted:
            usernames_with_at.append('@%s' % user)
        self.lock.release()
        alert_message = ' '.join(usernames_with_at)
        self.bot.send_message(chat_id=self.chat_id,
                         text="Pals, be ready in a 5 minutes! %s" % alert_message)

        # It's guaranteed (logically) that the meal time has passed and we can delete it from the storage
        time.sleep(notification_interval)


def parse_time_HH_MM(text):
    parsed_time = time.strptime(text, " %H:%M")
    parsed_time_structure = time.localtime()
    parsed_time_structure.tm_hour = parsed_time.tm_hour
    parsed_time_structure.tm_minute = parsed_time.tm_minute
    return parsed_time_structure


def suggest(bot, update):
    try:
        suggested_time_structure = parse_time_HH_MM(update.message.text)
    except ValueError:
        bot.send_message(chat_id=update.message.chat_id,
                         text="@%s, wrong time format, write something like \'/suggest 14:59\'" % update.message.from_user.username)
        return

    try:
        if (time.mktime(suggested_time_structure) < time.time()):
            bot.send_message(chat_id=update.message.chat_id,
                             text="@%s, you cannot return the past back. Or it's just clock skew. Nevertheless, the suggestion is ignored." % update.message.from_user.username)
            return
    except (OverflowError, ValueError) as error:
        bot.send_message(chat_id=update.message.chat_id,
                         text="@%s, something totally went wrong with the time you suggested" % update.message.from_user.username)
        return


    current_suggestion = MealSuggestion(suggested_time_structure, bot, update.message.chat_id)
    current_user_id = update.message.from_user.username
    if suggested_time_structure in current_suggestions:
        bot.send_message(chat_id=update.message.chat_id,
                         text="@%s, you suggestion duplicates old one; added you as accepted." % current_user_id)
    else:
        current_suggestions[suggested_time_structure] = current_suggestion

    current_suggestions[suggested_time_structure].accept_user(current_user_id)

def accept(bot, update):
    try:
        accepted_time_structure = parse_time_HH_MM(update.message.text)
    except ValueError:
        bot.send_message(chat_id=update.message.chat_id,
                         text="@%s, wrong time format, write something like \'/accept 14:59\'" % update.message.from_user.username)
        return

    current_user_id = update.message.from_user.username
    if accepted_time_structure not in current_suggestions:
        bot.send_message(chat_id=update.message.chat_id,
                         text="@%s, you are trying to accept the time that was not suggested. Try \'/suggest\' command instead" % current_user_id)
        return
    current_suggestions[accepted_time_structure].accept_user(current_user_id)

def decline(bot, update):
    try:
        declined_time_structure = parse_time_HH_MM(update.message.text, " %H:%M")
    except ValueError:
        bot.send_message(chat_id=update.message.chat_id,
                         text="@%s, wrong time format, write something like \'/decline 14:59\'" % update.message.from_user.username)
        return

    current_user_id = update.message.from_user.username
    if declined_time_structure not in current_suggestions:
        bot.send_message(chat_id=update.message.chat_id,
                         text="@%s, you are trying to decline the time that was not suggested." % current_user_id)
        return
    current_suggestions[declined_time_structure].decline_user(current_user_id)

def show(bot, update):
    if not current_suggestions:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Now available suggestions.")
        return

    meal_info_list = []
    for time_struct, meal_suggestion in current_suggestions.items():
        time_printed = time.strftime("%H:%M", time_struct)
        (users_accepted, users_declined) = meal_suggestion.get_info()
        users_accepted_printed = ' '.join(users_accepted)
        users_declined_printed = ' '.join(users_declined)
        meal_info_list.append('%s:\n\taccepted: %s,\n\tdeclined: %s' % (time_printed, users_accepted_printed, users_declined_printed))
    message = '\n'.join(meal_info_list)
    bot.send_message(chat_id=update.message.chat_id, text=message)


if __name__ == '__main__':
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher
    remember_handler = CommandHandler('remember', remember)
    dispatcher.add_handler(remember_handler)
    alert_handler = CommandHandler('alert', alert)
    dispatcher.add_handler(alert_handler)
    suggest_handler = CommandHandler('suggest', suggest)
    dispatcher.add_handler(suggest_handler)
    accept_handler = CommandHandler('accept', accept)
    dispatcher.add_handler(accept_handler)
    decline_handler = CommandHandler('decline', decline)
    dispatcher.add_handler(decline_handler)
    show_handler = CommandHandler('show', show)
    dispatcher.add_handler(show_handler)
    updater.start_polling()
