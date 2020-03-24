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
import time
from datetime import datetime
# Ensure secrets.py exists
from secrets import rtsp1, rtsp2, rtmp1, rtmp2, group, bottoken

bot = telegram.Bot(token=bottoken)


def admin(update, context):
    msg = '*LIVE STREAMING*\nAdmin Control Panel'
    keyboard = [
        [InlineKeyboardButton(
            "Start MediaLive", callback_data='liveon')],
        [InlineKeyboardButton(
            "Stop MediaLive", callback_data='liveoff')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(
        chat_id=group, reply_markup=reply_markup, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)


@run_async
def liveon():
    process = subprocess.Popen(['aws', 'medialive', 'start-channel', '--channel-id', '9981981'],
                               stdout=subprocess.PIPE, universal_newlines=True)
    for output in process.stdout.readlines():
        print(output.strip())
    bot.send_message(chat_id=group, text='*MediaLive Channel is starting*',
                     parse_mode=telegram.ParseMode.MARKDOWN)
    return


@run_async
def liveoff():
    process = subprocess.Popen(['aws', 'medialive', 'stop-channel', '--channel-id', '9981981'],
                               stdout=subprocess.PIPE, universal_newlines=True)
    for output in process.stdout.readlines():
        print(output.strip())
    bot.send_message(chat_id=group, text='*MediaLive Channel is stopping*',
                     parse_mode=telegram.ParseMode.MARKDOWN)
    return


def callbackquery(update, context):
    query = update.callback_query
    data = query.data
    first_name = query.from_user.first_name
    last_name = query.from_user.last_name
    full_name = (str(first_name or '') + ' ' + str(last_name or '')).strip()
    bot.send_message(chat_id=group, text='`Bot is responding to command by {}`'.format(
        full_name), parse_mode=telegram.ParseMode.MARKDOWN)
    if data == 'liveon':
        liveon()
    elif data == 'liveoff':
        liveoff()
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


def main():
    updater = Updater(
        token=bottoken, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("admin", admin))
    dp.add_handler(CallbackQueryHandler(callbackquery))

    webserver()
    updater.start_polling(1)

    print("Bot is running. Press Ctrl+C to stop.")
    liveoff() # TEST ONLY
    updater.idle()
    print("Bot stopped successfully.")


if __name__ == '__main__':
    main()
