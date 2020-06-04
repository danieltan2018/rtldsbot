import telegram.bot
import psycopg2
import requests
import time
from secret import bottoken, group, dbuser, dbpass, dbhost, dbport, dbdata, apikey, whitelist

bot = telegram.Bot(token=bottoken)

compose = 'LIFERTL LOGIN REPORT\n'
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
    if ip not in whitelist:
        iplist[id].add(ip)
for id in iplist:
    ipcount = len(iplist[id])
    if ipcount > 1:
        compose += '\n{} {}\n'.format(str(id), namelist[id])
        for addr in iplist[id]:
            data = requests.get(
                url='https://api.ipgeolocation.io/ipgeo?apiKey={}&ip={}'.format(apikey, addr)).json()
            isp = data['isp']
            conn = data['connection_type']
            isp = isp.replace('Mobile-Broadband', 'M1')
            if 'M1' in isp:
                isp = 'M1'
            if conn == 'wireless':
                if isp == 'M1':
                    isp += ' Fibre'
                else:
                    isp += ' Mobile'
            if conn == 'cable':
                isp += ' Cable'
            if isp == 'M1':
                isp += ' Mobile'
            compose += addr + ' ({})\n'.format(isp)

compose = compose.replace(
    'Singapore Telecommunications Ltd, Magix Services', 'SingTel Fibre')
compose = compose.replace(
    'Singapore Telecommunications Ltd SingTel Mobile', 'SingTel')
compose = compose.replace('SGCABLEVISION', 'Starhub')

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
