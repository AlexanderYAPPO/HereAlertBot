FROM python:2.7-slim
RUN pip install python-telegram-bot --upgrade
COPY src/alert_bot_runner.py /usr/bin/alert_bot_runner.py
RUN chmod +x /usr/bin/alert_bot_runner.py
RUN mkdir /var/log/here_alert_bot
RUN chmod -R u+rw,g+rw,o+rw /var/log/here_alert_bot

RUN apt-get update
RUN apt-get install -y sqlite3 libsqlite3-dev screen

CMD ["python", "/usr/bin/alert_bot_runner.py"]