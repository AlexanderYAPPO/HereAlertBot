import os

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


if __name__ == '__main__':
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher
    remember_handler = CommandHandler('remember', remember)
    alert_handler = CommandHandler('alert', alert)
    dispatcher.add_handler(remember_handler)
    dispatcher.add_handler(alert_handler)
    updater.start_polling()
