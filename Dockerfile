FROM python:2.7-slim
RUN pip install python-telegram-bot --upgrade
COPY src/alert_bot_runner.py /usr/bin/alert_bot_runner.py
RUN chmod +x /usr/bin/alert_bot_runner.py

RUN apt-get update
RUN apt-get install -y sqlite3 libsqlite3-dev screen

RUN screen -d -m python here_alert_bot.py