import telegram
import psycopg2
import schedule
import secrets
import bcrypt
import time
from secret import group, bottoken, dbuser, dbpass, dbhost, dbport, dbdata, email

bot = telegram.Bot(token=bottoken)


def changepw():
    try:
        connection = psycopg2.connect(user=dbuser,
                                      password=dbpass,
                                      host=dbhost,
                                      port=dbport,
                                      database=dbdata)
        cursor = connection.cursor()
        bot.send_message(chat_id=group, text="_Changing password for guest account..._",
                         parse_mode=telegram.ParseMode.MARKDOWN)
        passwd = secrets.token_hex(4)
        pw = passwd.encode('UTF-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pw, salt)
        hashed = hashed.decode('UTF-8')
        sql_update_query = """UPDATE users SET password = %s WHERE email = %s"""
        cursor.execute(sql_update_query, (hashed, email))
        connection.commit()
        bot.send_message(chat_id=group, text="Password: *{}*".format(passwd),
                         parse_mode=telegram.ParseMode.MARKDOWN)

    except (Exception, psycopg2.Error) as error:
        print("Error", error)

    finally:
        if(connection):
            cursor.close()
            connection.close()


def release():
    try:
        connection = psycopg2.connect(user=dbuser,
                                      password=dbpass,
                                      host=dbhost,
                                      port=dbport,
                                      database=dbdata)
        cursor = connection.cursor()
        bot.send_message(chat_id=group, text="_Releasing Worship Service Recording..._",
                         parse_mode=telegram.ParseMode.MARKDOWN)
        sql_update_query = """UPDATE events SET category_id = %s WHERE category_id = %s"""
        cursor.execute(sql_update_query, ('57', '55'))
        connection.commit()
        bot.send_message(chat_id=group, text="*Updated*",
                         parse_mode=telegram.ParseMode.MARKDOWN)

    except (Exception, psycopg2.Error) as error:
        print("Error", error)

    finally:
        if(connection):
            cursor.close()
            connection.close()


schedule.every().sunday.at("07:45").do(release)
schedule.every().monday.at("00:00").do(changepw)

while True:
    schedule.run_pending()
    time.sleep(30)
