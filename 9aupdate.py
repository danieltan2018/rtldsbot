import telegram
import schedule
import secrets
import time
from secret import group, bottoken, link
import os

bot = telegram.Bot(token=bottoken)


def changecode():
    bot.send_message(chat_id=group, text="_Changing password for 9a..._",
                     parse_mode=telegram.ParseMode.MARKDOWN)
    code = secrets.token_hex(3).upper()
    olddir = "/var/www/html/" + os.listdir("/var/www/html")[0]
    newdir = "/var/www/html/" + code
    os.rename(olddir, newdir)
    bot.send_message(chat_id=group, text=f"{link}{code}/")


schedule.every().friday.at("00:00").do(changecode)

while True:
    schedule.run_pending()
    time.sleep(30)
