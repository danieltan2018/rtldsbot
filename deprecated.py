# Dependency: pip install python-telegram-bot --upgrade
import telegram.bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Updater, CommandHandler,
                          Filters, CallbackQueryHandler)
from telegram.ext.dispatcher import run_async
# Dependency: pip install flask requests
from flask import Flask, request, jsonify
# Dependency: pip install schedule
import schedule
import subprocess
import re
from collections import OrderedDict
import time
from datetime import datetime
# Ensure secrets.py exists
from secrets import rtsp1, rtsp2, rtmp1, rtmp2, group, bottoken

bot = telegram.Bot(token=bottoken)


def admin(update, context):
    msg = '*LIVE STREAMING*\nAdmin Control Panel'
    keyboard = [
        [InlineKeyboardButton(
            "Start Stream (Sanctuary)", callback_data='stream1')],
        [InlineKeyboardButton(
            "Stop Stream (Sanctuary)", callback_data='kill1')],
        [InlineKeyboardButton(
            "Start Stream (MPH)", callback_data='stream2')],
        [InlineKeyboardButton(
            "Stop Stream (MPH)", callback_data='kill2')],
        [InlineKeyboardButton(
            "View Log (English Svc)", callback_data='englog')],
        [InlineKeyboardButton(
            "View Log (Chinese Svc)", callback_data='chilog')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(
        chat_id=group, reply_markup=reply_markup, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)


@run_async
def stream1():
    global process1
    bot.send_message(chat_id=group,
                     text='_Starting stream from Sanctuary..._', parse_mode=telegram.ParseMode.MARKDOWN)
    process1 = subprocess.Popen(['ffmpeg', '-i', rtsp1, '-vcodec', 'copy', '-acodec', 'copy', '-f', 'flv', rtmp1],
                                stderr=subprocess.PIPE, universal_newlines=True)
    monitor = True
    while True:
        output = process1.stderr.readline()
        if output == '' and process1.poll() is not None:
            break
        if output:
            if monitor and 'speed=' in output:
                bot.send_message(chat_id=group, text='*Sanctuary stream connected*',
                                 parse_mode=telegram.ParseMode.MARKDOWN)
                monitor = False
            elif 'failed' in output or 'error' in output:
                bot.send_message(chat_id=group, text='*Sanctuary stream connection failure*',
                                 parse_mode=telegram.ParseMode.MARKDOWN)
                return
    bot.send_message(chat_id=group, text='*Sanctuary stream disconnected*',
                     parse_mode=telegram.ParseMode.MARKDOWN)
    return


@run_async
def kill1():
    global process1
    bot.send_message(chat_id=group,
                     text='_Stopping stream from Sanctuary..._', parse_mode=telegram.ParseMode.MARKDOWN)
    process1.kill()
    process1.wait()
    return


@run_async
def stream2():
    global process2
    bot.send_message(chat_id=group,
                     text='_Starting stream from MPH..._', parse_mode=telegram.ParseMode.MARKDOWN)
    process2 = subprocess.Popen(['ffmpeg', '-i', rtsp2, '-vcodec', 'copy', '-acodec', 'copy', '-f', 'flv', rtmp2],
                                stderr=subprocess.PIPE, universal_newlines=True)
    monitor = True
    while True:
        output = process2.stderr.readline()
        if output == '' and process2.poll() is not None:
            break
        if output:
            if monitor and 'speed=' in output:
                bot.send_message(chat_id=group, text='*MPH stream connected*',
                                 parse_mode=telegram.ParseMode.MARKDOWN)
                monitor = False
            elif 'failed' in output or 'error' in output:
                bot.send_message(chat_id=group, text='*MPH stream connection failure*',
                                 parse_mode=telegram.ParseMode.MARKDOWN)
                return
    bot.send_message(chat_id=group, text='*MPH stream disconnected*',
                     parse_mode=telegram.ParseMode.MARKDOWN)
    return


@run_async
def kill2():
    global process2
    bot.send_message(chat_id=group,
                     text='_Stopping stream from MPH..._', parse_mode=telegram.ParseMode.MARKDOWN)
    process2.kill()
    process2.wait()
    return


@run_async
def log(logname, logsearch):
    timestamp_regex = re.compile('\[.*\+')
    email_regex = re.compile('\?.*\sHTTP/')
    logstore = OrderedDict()
    ipstore = {}
    ipwarnings = set()
    currtime = ''
    ratecounter = {}
    ratewarnings = set()
    firstseen = {}
    lastseen = {}

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
                if ' 404 ' in line:
                    email += ' ERROR'
                logstore[timestamp].add(email)
                ip = line[:15]
                if email not in ipstore:
                    ipstore[email] = ip
                else:
                    if ipstore[email] != ip:
                        ipwarnings.add(email)
                if timestamp != currtime:
                    currtime = timestamp
                    for email in ratecounter:
                        if ratecounter[email] > 31:
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
        if item in lastseen:
            prelog += item + ' '
            prelog += firstseen[item] + ' - ' + lastseen[item] + '\n'
    prelog += '\n=== {} CURRENTLY VIEWING ===\n'.format(len(viewers))
    if len(viewers) > 0:
        for item in viewers:
            finallog += item + '\n'
    prelog += '\n'
    prelog += '=== RATE WARNINGS ===\nThe following users may be watching on multiple devices:\n'
    for item in ratewarnings:
        prelog += item + '\n'
    prelog += '\n'
    prelog += '=== IP WARNINGS ===\nMultiple IP addresses detected for the following users:\n'
    for item in ipwarnings:
        prelog += item + '\n'
    prelog += '\n' + '=== FULL LOG ===\n'
    finallog = prelog + finallog
    finallog += '\n{} Log generated at '.format(
        logname) + str(datetime.now()).split('.')[0]

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


def callbackquery(update, context):
    query = update.callback_query
    data = query.data
    first_name = query.from_user.first_name
    last_name = query.from_user.last_name
    full_name = (str(first_name or '') + ' ' + str(last_name or '')).strip()
    bot.send_message(chat_id=group, text='`Bot is responding to command by {}`'.format(
        full_name), parse_mode=telegram.ParseMode.MARKDOWN)
    if data == 'stream1':
        stream1()
    elif data == 'kill1':
        kill1()
    elif data == 'stream2':
        stream2()
    elif data == 'kill2':
        kill2()
    elif data == 'englog':
        log('English Service', 'GET /live.m3u8?')
    elif data == 'chilog':
        bot.send_message(
            chat_id=group, text='This feature is not implemented yet!')
    context.bot.answer_callback_query(query.id)


@run_async
def liveon():
    process = subprocess.Popen(['aws', 'medialive', 'start-channel', '--channel-id', '9981981'],
                               stdout=subprocess.PIPE, universal_newlines=True)
    bot.send_message(chat_id=group, text='_Starting MediaLive channel..._',
                     parse_mode=telegram.ParseMode.MARKDOWN)
    while True:
        testprocess = subprocess.Popen(['aws', 'medialive', 'list-channels'],
                                       stdout=subprocess.PIPE, universal_newlines=True)
        for output in testprocess.stdout.readlines():
            if '"State": "RUNNING"' in output:
                bot.send_message(chat_id=group, text='*MediaLive ON*',
                                 parse_mode=telegram.ParseMode.MARKDOWN)
                return
        time.sleep(10)
    return


@run_async
def liveoff():
    process = subprocess.Popen(['aws', 'medialive', 'stop-channel', '--channel-id', '9981981'],
                               stdout=subprocess.PIPE, universal_newlines=True)
    bot.send_message(chat_id=group, text='_Stopping MediaLive channel..._',
                     parse_mode=telegram.ParseMode.MARKDOWN)
    while True:
        testprocess = subprocess.Popen(['aws', 'medialive', 'list-channels'],
                                       stdout=subprocess.PIPE, universal_newlines=True)
        for output in testprocess.stdout.readlines():
            if '"State": "IDLE"' in output:
                bot.send_message(chat_id=group, text='*MediaLive OFF*',
                                 parse_mode=telegram.ParseMode.MARKDOWN)
                return
        time.sleep(10)
    return


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
        compose += '<b>Notification Type: </b>' + \
            x['notificationType'] + '\n'
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


@run_async
def bsmcount():
    try:
        connection = psycopg2.connect(user=dbuser,
                                      password=dbpass,
                                      host=dbhost,
                                      port=dbport,
                                      database=dbdata)
        cursor = connection.cursor()
        compose = 'BIBLE SEMINAR\n\n'
        for i in range(740, 761):
            try:
                cursor.execute(
                    "SELECT COUNT(*) FROM(SELECT DISTINCT user_id FROM user_activities WHERE path='/api/content/event/%s/mediaentrylist') AS x", (i,))
                eventclicks = cursor.fetchone()[0]
                cursor.execute(
                    "SELECT COUNT(*) FROM(SELECT user_id FROM user_activities WHERE path='/api/content/event/%s/mediaentrylist') AS x", (i,))
                eventviews = cursor.fetchone()[0]
                cursor.execute("SELECT name FROM events WHERE id = %s", (i,))
                eventname = cursor.fetchone()[0]
                compose += "{}: *{} views ({} users)*\n".format(
                    eventname, eventviews, eventclicks)
            except:
                pass
        bot.send_message(chat_id=group, text=compose,
                         parse_mode=telegram.ParseMode.MARKDOWN)

    except (Exception, psycopg2.Error) as error:
        print("Error", error)

    finally:
        if(connection):
            cursor.close()
            connection.close()


@run_async
def bsmwarning():
    bsmlogs('MESSAGES', 75)
    bsmlogs('VIDEOS', 76)


def bsmlogs(logname, category):
    try:
        connection = psycopg2.connect(user=dbuser,
                                      password=dbpass,
                                      host=dbhost,
                                      port=dbport,
                                      database=dbdata)
        cursor = connection.cursor()
        cursor.execute("SELECT user_activities.created_at, preferred_name, ip_address FROM users, user_activities WHERE users.id = user_id AND path = '/api/content/category/%s'", (category,))
        rows = cursor.fetchall()
        iplist = {}
        date1 = '2020-05-25'
        date2 = '2020-05-25'
        for row in rows:
            fulldate = str(row[0])
            date = fulldate.split()[0]
            name = row[1]
            ip = row[2]
            if date not in iplist:
                date1 = date2
                date2 = date
                iplist[date] = {}
            if name not in iplist[date]:
                iplist[date][name] = set()
            iplist[date][name].add(ip)
        compose = '=== BIBLE SEMINAR LOG ({}) ==='.format(logname)
        compose += '\nNote: Day starts at 8AM SGT'
        includedate = [date1, date2]
        for date in includedate:
            compose += '\n\n' + date
            for name in iplist[date]:
                compose += '\n' + name
                ipcount = len(iplist[date][name])
                if ipcount > 1:
                    compose += ' ({} IPs)'.format(ipcount)

        sender = compose.split('\n')
        linecounter = 0
        message = ''
        for line in sender:
            message += line + '\n'
            linecounter += 1
            if linecounter == 50:
                bot.send_message(
                    chat_id=group, text=message)
                time.sleep(1)
                linecounter = 0
                message = ''
        bot.send_message(chat_id=group, text=message)

    except (Exception, psycopg2.Error) as error:
        print("Error", error)

    finally:
        if(connection):
            cursor.close()
            connection.close()


@run_async
def stream1():
    global kill1confirm
    kill1confirm = 0
    global process1
    bot.send_message(chat_id=group,
                     text='_Starting stream from file..._', parse_mode=telegram.ParseMode.MARKDOWN)
    process1 = subprocess.Popen(['ffmpeg', '-re', '-i', 'svc.mp4', '-c', 'copy', '-f', 'flv', rtmp1],
                                stderr=subprocess.PIPE, universal_newlines=True)
    monitor = True
    while True:
        output = process1.stderr.readline()
        if output == '' and process1.poll() is not None:
            break
        if output:
            if monitor and 'speed=' in output:
                bot.send_message(chat_id=group, text='*Playback Started*',
                                 parse_mode=telegram.ParseMode.MARKDOWN)
                monitor = False
    bot.send_message(chat_id=group, text='*Playback Stopped*',
                     parse_mode=telegram.ParseMode.MARKDOWN)
    del kill1confirm
    return


@run_async
def kill1():
    try:
        global kill1confirm
        kill1confirm += 1
    except:
        bot.send_message(chat_id=group, text='_Unable to stop: stream is not running._',
                         parse_mode=telegram.ParseMode.MARKDOWN)
        return
    if kill1confirm % 2 == 0:
        global process1
        bot.send_message(chat_id=group, text='_Stopping stream..._',
                         parse_mode=telegram.ParseMode.MARKDOWN)
        process1.kill()
        process1.wait()
    else:
        bot.send_message(chat_id=group,
                         text='_Please press Stop Stream again to confirm._', parse_mode=telegram.ParseMode.MARKDOWN)
    return


@run_async
def download():
    process = subprocess.Popen(
        ['aws', 's3', 'cp', svcfile, './'], stdout=subprocess.PIPE, universal_newlines=True)
    bot.send_message(chat_id=group, text='_Downloading svc file..._',
                     parse_mode=telegram.ParseMode.MARKDOWN)
    for output in process.stdout.readlines():
        if 'download:' in output:
            bot.send_message(chat_id=group, text='*Download Complete*',
                             parse_mode=telegram.ParseMode.MARKDOWN)
    return


@run_async
def scheduler():
    schedule.every().saturday.at("20:00").do(download)
    schedule.every().sunday.at("07:47:30").do(stream1)
    schedule.every().sunday.at("10:47:30").do(stream1)
    print("Tasks scheduled.")
    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    updater = Updater(
        token=bottoken, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("admin", admin))
    dp.add_handler(CallbackQueryHandler(callbackquery))
    scheduler()
    webserver()
    updater.start_polling(1)

    print("Bot is running. Press Ctrl+C to stop.")
    updater.idle()
    print("Bot stopped successfully.")


if __name__ == '__main__':
    main()
