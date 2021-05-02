import telegram.bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Updater, CommandHandler,
                          Filters, CallbackQueryHandler)
from telegram.ext.dispatcher import run_async
from flask import Flask, request, jsonify
import subprocess
import re
from collections import OrderedDict
import time
from datetime import datetime
import psycopg2
from secret import rtmp1, svcfile, group, bottoken, dbuser, dbpass, dbhost, dbport, dbdata
import gsheetsync
import ipwarn

bot = telegram.Bot(token=bottoken)


def admin(update, context):
    msg = '*LIVE STREAMING*\nAdmin Control Panel'
    keyboard = [
        [InlineKeyboardButton(
            "View Log", callback_data='log')],
        [InlineKeyboardButton(
            "Recording Viewer Count", callback_data='latestcount')],
        [InlineKeyboardButton(
            "Login IP Report", callback_data='doipwarn')],
        [InlineKeyboardButton(
            "Sync Loty Database", callback_data='syncloty')],
        [InlineKeyboardButton(
            "Sync Life Database", callback_data='synclife')],
        [InlineKeyboardButton(
            "Finalise Stream", callback_data='endstream')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(
        chat_id=group, reply_markup=reply_markup, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)


def endstream():
    bot.send_message(chat_id=group, text='_Finalising Stream..._',
                     parse_mode=telegram.ParseMode.MARKDOWN)
    with open("/stream/live/live.m3u8", "a") as f:
        f.write("#EXT-X-ENDLIST")
    bot.send_message(chat_id=group, text='*Stream Finalised*',
                     parse_mode=telegram.ParseMode.MARKDOWN)


def sender(finallog):
    logsender = finallog.split('\n')
    linecounter = 0
    compose = ''
    for line in logsender:
        compose += line + '\n'
        linecounter += 1
        if linecounter == 50:
            bot.send_message(
                chat_id=group, text=compose)
            time.sleep(1)
            linecounter = 0
            compose = ''
    bot.send_message(chat_id=group, text=compose)


def log():
    logname = 'English Service'
    logsearch = 'live/live.m3u8?'
    timestamp_regex = re.compile('\[.*\+')
    email_regex = re.compile('\?.*\sHTTP/')
    logstore = OrderedDict()
    ipstore = {}
    ipwarnings = {}
    currtime = ''
    ratecounter = {}
    ratewarnings = set()
    firstseen = {}
    lastseen = {}

    with open('/var/log/nginx/access.log', 'r') as logfile:
        for line in logfile:
            # if '9a@lifertl.com' in line:
            #     continue
            line = line.strip()
            timestamp = timestamp_regex.search(line).group()
            timestamp = timestamp.strip('[+')
            timestamp = timestamp[12:17]
            if timestamp not in logstore:
                logstore[timestamp] = set()
            if logsearch in line:
                email = email_regex.search(line).group()
                email = email.strip('? ')
                email = email.replace(' HTTP/', '')
                if ' 404 ' in line or ' 215 ' in line:
                    email += ' ERROR'
                logstore[timestamp].add(email)
                lineparts = line.split('"')
                finder = lineparts.index('Amazon CloudFront')
                ip = lineparts[finder+2]
                if email not in ipstore:
                    ipstore[email] = [ip]
                else:
                    if ip not in ipstore[email]:
                        ipstore[email].append(ip)
                        if email not in ipwarnings:
                            ipwarnings[email] = 2
                        else:
                            ipwarnings[email] = ipwarnings[email] + 1
                if timestamp != currtime:
                    currtime = timestamp
                    for email in ratecounter:
                        if ratecounter[email] > 30:
                            ratewarnings.add(email)
                    ratecounter = {}
                else:
                    if email not in ratecounter:
                        ratecounter[email] = 0
                    else:
                        ratecounter[email] = ratecounter[email] + 1

    finallog = ''
    viewers = set()
    for timestamp, emailset in logstore.items():
        for email in emailset:
            if email not in viewers:
                viewers.add(email)
                if 'ERROR' not in email:
                    finallog += timestamp + ' ' + email + ' PLAY\n'
                    if email not in firstseen:
                        firstseen[email] = timestamp

        currentviewers = viewers.copy()
        for email in currentviewers:
            if email not in emailset:
                viewers.remove(email)
                finallog += timestamp + ' ' + email + ' EXIT\n'
                lastseen[email] = timestamp

    prelog = '=== {} TOTAL VIEWERS ===\n'.format(len(firstseen))
    for item in firstseen:
        if item in viewers:
            prelog += item + ' '
            prelog += firstseen[item] + ' - ' + 'now' + '\n'
        elif item in lastseen:
            prelog += item + ' '
            prelog += firstseen[item] + ' - ' + lastseen[item] + '\n'
    prelog += '\n=== {} CURRENTLY VIEWING ===\n'.format(len(viewers))
    if len(viewers) > 0:
        for item in viewers:
            prelog += item + '\n'
    prelog += '\n'
    prelog += '=== RATE WARNINGS ===\nThe following users may be watching on multiple devices:\n'
    for item in ratewarnings:
        if 'ERROR' not in item:
            prelog += item + '\n'
    prelog += '\n'
    prelog += '=== IP WARNINGS ===\nMultiple IP addresses detected for the following users:\n'
    for key, value in ipwarnings.items():
        prelog += key + ': ' + str(value) + ' IPs\n'
        # for ipaddr in ipstore[key]:
        #     prelog += ipaddr + '\n'
    prelog += '\n' + '=== FULL LOG DISABLED ===\n'
    # finallog = prelog + finallog
    finallog = prelog
    finallog += '\nLast log entry at ' + timestamp
    sender(finallog)
    # log9a()


def log9a():
    logsearch = 'live/live.m3u8?'
    timestamp_regex = re.compile('\[.*\+')
    email_regex = re.compile('\?.*\sHTTP/')
    logstore = OrderedDict()
    firstseen = {}
    lastseen = {}
    ipmap = {}
    ipcount = 0

    with open('/var/log/nginx/access.log', 'r') as logfile:
        for line in logfile:
            line = line.strip()
            timestamp = timestamp_regex.search(line).group()
            timestamp = timestamp.strip('[+')
            timestamp = timestamp[12:17]
            if timestamp not in logstore:
                logstore[timestamp] = set()
            if logsearch in line:
                email = email_regex.search(line).group()
                email = email.strip('? ')
                email = email.replace(' HTTP/', '')
                if email == '9a@lifertl.com':
                    lineparts = line.split('"')
                    finder = lineparts.index('Amazon CloudFront')
                    ip = lineparts[finder+2]
                    if ip not in ipmap:
                        ipcount += 1
                        ipmap[ip] = 'User_' + str(ipcount)
                    email = ipmap[ip]
                    logstore[timestamp].add(email)

    finallog = ''
    viewers = set()
    for timestamp, emailset in logstore.items():
        for email in emailset:
            if email not in viewers:
                viewers.add(email)
                finallog += timestamp + ' ' + email + ' PLAY\n'
                if email not in firstseen:
                    firstseen[email] = timestamp

        currentviewers = viewers.copy()
        for email in currentviewers:
            if email not in emailset:
                viewers.remove(email)
                finallog += timestamp + ' ' + email + ' EXIT\n'
                lastseen[email] = timestamp

    prelog = '=== {} TOTAL 9A USERS ===\n'.format(ipcount)
    for item in firstseen:
        if item in viewers:
            prelog += item + ' '
            prelog += firstseen[item] + ' - ' + 'now' + '\n'
        elif item in lastseen:
            prelog += item + ' '
            prelog += firstseen[item] + ' - ' + lastseen[item] + '\n'

    prelog += '\n'

    holdingarea = []

    try:
        connection = psycopg2.connect(user=dbuser,
                                      password=dbpass,
                                      host=dbhost,
                                      port=dbport,
                                      database=dbdata)
        cursor = connection.cursor()
        for ip in ipmap:
            cursor.execute(
                "SELECT DISTINCT email FROM users u, user_activities ua WHERE ua.user_id = u.id AND ip_address = %s", (ip,))
            assoc = cursor.fetchall()
            if assoc:
                prelog += ipmap[ip] + ' accounts:\n'
                for item in assoc:
                    prelog += item[0] + '\n'
            else:
                holdingarea.append(ipmap[ip])
        prelog += '\nNo associated accounts:\n'
        for item in holdingarea:
            prelog += item + '\n'
    except (Exception, psycopg2.Error) as error:
        print("Error", error)

    sender(prelog)


def latestcount():
    viewcounter(91, "WORSHIP SERVICES")
    viewcounter(92, "ADULT SUNDAY SCHOOL")


def viewcounter(id, name):
    try:
        connection = psycopg2.connect(user=dbuser,
                                      password=dbpass,
                                      host=dbhost,
                                      port=dbport,
                                      database=dbdata)
        cursor = connection.cursor()
        cursor.execute(
            f"SELECT id, name, date FROM events WHERE category_id={id}")
        services = cursor.fetchall()
        compose = f'{name}\n\n'
        for data in services:
            i = data[0]
            name = data[1]
            if name == "Sunday Worship Service":
                name = data[2].strftime('%d %b')
            cursor.execute(
                "SELECT COUNT(*) FROM(SELECT DISTINCT user_id FROM user_activities WHERE path='/api/content/event/%s/mediaentrylist') AS x", (i,))
            eventclicks = cursor.fetchone()[0]
            cursor.execute(
                "SELECT COUNT(*) FROM(SELECT user_id FROM user_activities WHERE path='/api/content/event/%s/mediaentrylist') AS x", (i,))
            eventviews = cursor.fetchone()[0]
            compose += "{}: *{} views ({} users)*\n".format(name,
                                                            eventviews, eventclicks)
        bot.send_message(chat_id=group, text=compose,
                         parse_mode=telegram.ParseMode.MARKDOWN)

    except (Exception, psycopg2.Error) as error:
        print("Error", error)

    finally:
        if(connection):
            cursor.close()
            connection.close()


def callbackquery(update, context):
    query = update.callback_query
    data = query.data
    first_name = query.from_user.first_name
    last_name = query.from_user.last_name
    full_name = (str(first_name or '') + ' ' + str(last_name or '')).strip()
    bot.send_message(chat_id=group, text='`Bot is responding to command by {}`'.format(
        full_name), parse_mode=telegram.ParseMode.MARKDOWN)
    if data == 'log':
        log()
    elif data == 'latestcount':
        latestcount()
    elif data == 'doipwarn':
        ipwarn.generate()
    elif data == 'endstream':
        endstream()
    elif data == 'syncloty':
        bot.send_message(chat_id=group, text='_Syncing Loty Database..._',
                         parse_mode=telegram.ParseMode.MARKDOWN)
        try:
            gsheetsync.sync('lotydb')
            bot.send_message(chat_id=group, text='*Sync Completed*',
                             parse_mode=telegram.ParseMode.MARKDOWN)
        except Exception as e:
            bot.send_message(chat_id=group, text='*Failed with error: *{}'.format(e),
                             parse_mode=telegram.ParseMode.MARKDOWN)
    elif data == 'synclife':
        bot.send_message(chat_id=group, text='_Syncing Life Database..._',
                         parse_mode=telegram.ParseMode.MARKDOWN)
        try:
            gsheetsync.sync('lifedb')
            bot.send_message(chat_id=group, text='*Sync Completed*',
                             parse_mode=telegram.ParseMode.MARKDOWN)
        except Exception as e:
            bot.send_message(chat_id=group, text='*Failed with error: *{}'.format(e),
                             parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.send_message(chat_id=group, text='`That is an invalid command!`',
                         parse_mode=telegram.ParseMode.MARKDOWN)
    context.bot.answer_callback_query(query.id)


@run_async
def webserver():
    app.run(host='0.0.0.0', port=8000, threaded=True)


app = Flask(__name__)


@app.route('/', methods=['POST'])
def index():
    if request.method == 'POST':
        x = request.get_json(force=True)
        compose = ''
        compose += '<u>AWS Simple Email Service</u>\n'
        try:
            compose += '<b>Notification Type: </b>' + \
                x['notificationType'] + '\n'
        except:
            print(x)
            return '{"success":"true"}', 200
        for y in x['mail']['commonHeaders']['to']:
            compose += '<b>To: </b>' + y + '\n'
        compose += '<b>Subject: </b>' + x['mail']['commonHeaders']['subject']
        try:
            x = x['bounce']
            compose += '\n\n'
            compose += '<b>Bounce Type: </b>' + \
                x['bounceType'] + ' (' + x['bounceSubType'] + ')\n'
            for y in x['bouncedRecipients']:
                compose += y['status'] + ' ' + y['action'].upper() + '\n'
                compose += y['diagnosticCode']
        except:
            pass
        try:
            x = x['complaint']
            compose += '\n\n'
            compose += '<b>Complaint: </b>' + \
                x['complaintFeedbackType'] + ' - ' + x['userAgent'] + '\n'
        except:
            pass
        bot.send_message(chat_id=group, text=compose,
                         parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
        return '{"success":"true"}', 200


def main():
    updater = Updater(token=bottoken, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("admin", admin))
    dp.add_handler(CallbackQueryHandler(callbackquery))

    updater.start_polling(1)
    print("Bot is running. Press Ctrl+C to stop.")
    webserver()
    updater.idle()
    print("Bot stopped successfully.")


if __name__ == '__main__':
    main()
