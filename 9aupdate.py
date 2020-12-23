import telegram
import schedule
import secrets
import time
from secret import group, bottoken, link
import os

bot = telegram.Bot(token=bottoken)


def changecode():
    bot.send_message(chat_id=group, text="_Changing code for 9a..._",
                     parse_mode=telegram.ParseMode.MARKDOWN)
    code = '0'
    while '0' in code or '1' in code:
        code = secrets.token_hex(4).upper()
    p = os.listdir("/var/www/html")
    for i in p:
        if os.path.isdir(i):
            olddir = "/var/www/html/" + i
            break
    newdir = "/var/www/html/" + code
    os.rename(olddir, newdir)
    bot.send_message(chat_id=group, text=f"{link}{code}/")


schedule.every().wednesday.at("00:00").do(changecode)

while True:
    schedule.run_pending()
    time.sleep(30)