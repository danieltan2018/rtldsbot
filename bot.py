# Dependency: pip install python-telegram-bot --upgrade
import telegram.bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Updater, CommandHandler,
                          Filters, CallbackQueryHandler)
from telegram.ext.dispatcher import run_async
# Dependency: pip install flask requests
from flask import Flask, request, jsonify
import subprocess
import re
from collections import OrderedDict
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

    with open('/var/log/nginx/access.log', 'r') as logfile:
        for line in logfile:
            if logsearch in line:
                line = line.strip()
                timestamp = timestamp_regex.search(line).group()
                timestamp = timestamp.strip('[+')
                timestamp = timestamp[12:17]
                if timestamp not in logstore:
                    logstore[timestamp] = set()
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
    finallog += '\n=== {} CURRENTLY VIEWING ===\n'.format(viewercount)
    if viewercount > 0:
        for item in viewers:
            finallog += item + '\n'
    finallog += '\n'
    finallog += '=== RATE WARNINGS ===\nThe following users may be watching on multiple devices:\n'
    for item in ratewarnings:
        finallog += item + '\n'
    finallog += '\n'
    finallog += '=== IP WARNINGS ===\nMultiple IP addresses detected for the following users:\n'
    for item in ipwarnings:
        finallog += item + '\n'
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
