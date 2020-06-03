import telegram.bot
import psycopg2
import requests
import time
from secret import bottoken, group, dbuser, dbpass, dbhost, dbport, dbdata

bot = telegram.Bot(token=bottoken)

compose = 'LOGIN REPORT\n\n'
connection = psycopg2.connect(user=dbuser,
                              password=dbpass,
                              host=dbhost,
                              port=dbport,
                              database=dbdata)
cursor = connection.cursor()
cursor.execute("SELECT DISTINCT user_id, preferred_name, ip_address FROM user_activities ua, users WHERE ua.created_at > NOW() - '1 week'::INTERVAL AND path = '/api/user/login' AND users.id = user_id ORDER BY user_id;")
rows = cursor.fetchall()
cursor.close()
connection.close()

iplist = {}
namelist = {}
for row in rows:
    id = row[0]
    name = row[1]
    ip = row[2]
    namelist[id] = name
    if id not in iplist:
        iplist[id] = set()
    iplist[id].add(ip)
for id in iplist:
    ipcount = len(iplist[id])
    if ipcount > 1:
        compose += str(id) + ' ' + namelist[id] + '\n'
        for addr in iplist[id]:
            isp = requests.get(
                url='http://ip-api.com/json/{}?fields=512'.format(addr)).json()['isp']
            compose += addr + ' ({})\n'.format(isp)
            time.sleep(2)

compose = compose.replace(
    'Singapore Telecommunications Ltd, Magix Services', 'SingTel Fibre')
compose = compose.replace(
    'Singapore Telecommunications Ltd SingTel Mobile', 'SingTel Mobile')


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
