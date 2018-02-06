# HereAlertBot

Bot that suppose to alert all participants of the group chat. First of all, you add your bot to your group. Then all people that want to get alert messages type `/remember`. After that command `/alert` directs all users in this group.

## Installation (For Amazon Linux and CentOS)
```bash
git clone https://github.com/AlexanderYAPPO/HereAlertBot.git
sudo yum install -y yum-utils device-mapper-persistent-data lvm2
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install --setopt=obsoletes=0 docker-ce-17.03.2.ce-1.el7.centos.x86_64 docker-ce-selinux-17.03.2.ce-1.el7.centos.noarch # For Amazon Linux
OR 
sudo yum install docker-ce # for CentOS
cd HereAlertBot
sudo docker build -t here_alert_bot .
```

## Setting up database
```bash
mkdir /var/lib/here_alert_bot/
sudo chmod -R u+rw,g+rw,o+rw /var/lib/here_alert_bot/
sqlite3 /var/lib/here_alert_bot/system.db "CREATE TABLE users_in_chats (chat_id integer, username text, primary key (chat_id, username));"
```

##Run the bot
```bash
docker run -t -d -i -e ALERT_BOT_TOKEN=<TOKEN> -p 80:80 -v /var/lib/here_alert_bot:/var/lib/here_alert_bot here_alert_bot
```