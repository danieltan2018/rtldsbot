# Dependency: pip install python-telegram-bot --upgrade
import telegram.bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Updater, CommandHandler,
                          Filters, CallbackQueryHandler)
from telegram.ext.dispatcher import run_async
# Dependency: pip install flask requests
from flask import Flask, request
import subprocess
import re
from collections import OrderedDict
from datetime import datetime
# Ensure secrets.py exists
from secrets import rtsp_address, rtmp_address, group, bottoken

bot = telegram.Bot(token=bottoken)


def admin(update, context):
    msg = '*LIVE STREAMING*\nAdmin Control Panel'
    keyboard = [
        [InlineKeyboardButton(
            "Start Stream", callback_data='stream')],
        [InlineKeyboardButton(
            "Stop Stream", callback_data='kill')],
        [InlineKeyboardButton(
            "View Today's Log", callback_data='log')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(
        chat_id=group, reply_markup=reply_markup, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)


@run_async
def stream(context):
    global process
    bot.send_message(chat_id=group,
                     text='_Starting RTSP stream..._', parse_mode=telegram.ParseMode.MARKDOWN)
    process = subprocess.Popen(['ffmpeg', '-i', rtsp_address, '-vcodec', 'copy', '-acodec', 'copy', '-f', 'flv', rtmp_address],
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
    for output in process.stdout.readlines():
        print(output.strip())
    bot.send_message(chat_id=group, text='*RTSP Stream Disconnected*',
                     parse_mode=telegram.ParseMode.MARKDOWN)
    return


@run_async
def kill(context):
    process.kill()
    process.wait()
    bot.send_message(chat_id=group,
                     text='*RTSP Stream Killed*', parse_mode=telegram.ParseMode.MARKDOWN)
    return


@run_async
def log(context):
    timestamp_regex = re.compile('\[.*\+')
    email_regex = re.compile('\?.*\sH')
    logstore = OrderedDict()

    with open('/var/log/nginx/access.log', 'r') as logfile:
        for line in logfile:
            if 'GET /live.m3u8?' in line:
                line = line.strip()
                timestamp = timestamp_regex.search(line).group()
                timestamp = timestamp.strip('[+')
                timestamp = timestamp[12:17]
                if timestamp not in logstore:
                    logstore[timestamp] = set()
                email = email_regex.search(line).group()
                email = email.strip('?H ')
                if ' 404 ' in line:
                    email += ' ERROR'
                logstore[timestamp].add(email)

    finallog = ''
    viewers = set()
    allviewers = set()
    for timestamp, emailset in logstore.items():
        for email in emailset:
            if email not in viewers:
                viewers.add(email)
                if 'ERROR' not in email:
                    finallog += timestamp + ' ' + email + ' PLAY\n'
                    allviewers.add(email)

        currentviewers = viewers.copy()
        for email in currentviewers:
            if email not in emailset:
                viewers.remove(email)
                finallog += timestamp + ' ' + email + ' EXIT\n'

    viewercount = len(viewers)
    allviewercount = len(allviewers)
    finallog = '=== {} TOTAL VIEWERS ===\n\n'.format(allviewercount) + finallog
    finallog += '\n=== {} CURRENTLY VIEWING: ===\n'.format(viewercount)
    if viewercount > 0:
        for item in viewers:
            finallog += item + '\n'
    finallog += '\nLog generated at ' + str(datetime.now()).split('.')[0]

    logsender = finallog.split('\n')
    linecounter = 0
    compose = ''
    for line in logsender:
        compose += line + '\n'
        linecounter += 1
        if linecounter == 50:
            bot.send_message(
                chat_id=group, text=compose)
            linecounter = 0
            compose = ''
    bot.send_message(chat_id=group, text=compose)


def callbackquery(update, context):
    query = update.callback_query
    data = query.data
    if data == 'stream':
        stream(context)
    if data == 'kill':
        kill(context)
    if data == 'log':
        log(context)
    context.bot.answer_callback_query(query.id)


@run_async
def webserver():
    app.run(host='0.0.0.0', port=8000, threaded=True)


app = Flask(__name__)


@app.route('/', methods=['POST'])
def index():
    if request.method == 'POST':
        x = request.get_json(force=True)
        print(json.dumps(x, indent=4))
        compose = ''
        compose += '<u>AWS Simple Email Service</u>\n'
        compose += '<b>Notification Type: </b>' + \
            x['notificationType'] + '\n\n'
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
    updater = Updater(
        token=bottoken, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("admin", admin))
    dp.add_handler(CallbackQueryHandler(callbackquery))

    webserver()
    updater.start_polling(1)

    print("Bot is running. Press Ctrl+C to stop.")
    updater.idle()
    print("Bot stopped successfully.")


if __name__ == '__main__':
    main()
