import os

import sqlite3

from telegram.ext import Updater
from telegram.ext import CommandHandler

TOKEN = os.environ['ALERT_BOT_TOKEN']
DB_PATH = '/var/lib/here_alert_bot/system.db'

def remember(bot, update):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users_in_chats VALUES (?, ?)', (update.message.chat_id, update.message.from_user.username))
        conn.commit()
    except sqlite3.IntegrityError:
        bot.send_message(chat_id=update.message.chat_id,
                         text='%s, already know you, like embarassing me?' % update.message.from_user.first_name)
        return
    finally:
        conn.close()
    bot.send_message(chat_id=update.message.chat_id,
                     text='%s, remembered you, college boy!' % update.message.from_user.first_name)

def forget(bot, update):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('DELETE FROM users_in_chats WHERE chat_id=? and username=?',
                  (update.message.chat_id, update.message.from_user.username))
        if c.rowcount:
            conn.commit()
            bot.send_message(chat_id=update.message.chat_id,
                             text='%s, forgot you, bye' % update.message.from_user.first_name)
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text='%s, I don\'t know you, I think you got the wrong door' % update.message.from_user.first_name)
    finally:
        conn.close()

def alert(bot, update):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('SELECT * FROM users_in_chats WHERE chat_id=?', (update.message.chat_id, ))
        users_with_at = []
        for chat_id, username in c:
            if username is None:
                continue
            users_with_at.append('@%s' % username)
        conn.commit()
    finally:
        conn.close()
    alert_message = ' '.join(users_with_at)
    original_message_parts = update.message.text.split(None, 1)
    if len(original_message_parts) > 1:
        original_message = original_message_parts[-1] + '\n\n'
    else:
        original_message = ''
    bot.send_message(chat_id=update.message.chat_id,
                     text='%s Atte-e-ention! %s' % (original_message, alert_message))


if __name__ == '__main__':
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher
    remember_handler = CommandHandler('remember', remember)
    alert_handler = CommandHandler('alert', alert)
    forget_handler = CommandHandler('forget', forget)
    dispatcher.add_handler(remember_handler)
    dispatcher.add_handler(alert_handler)
    dispatcher.add_handler(forget_handler)
    updater.start_polling()
