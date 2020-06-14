import telegram.bot
import psycopg2
import requests
import time
import re
from secret import bottoken, group, dbuser, dbpass, dbhost, dbport, dbdata, apikey, whitelist

bot = telegram.Bot(token=bottoken)

compose = 'LIFERTL LOGIN REPORT\n'
connection = psycopg2.connect(user=dbuser,
                              password=dbpass,
                              host=dbhost,
                              port=dbport,
                              database=dbdata)
cursor = connection.cursor()
cursor.execute("SELECT DISTINCT user_id, preferred_name, ip_address, user_agent FROM user_activities ua, users WHERE ua.created_at > NOW() - '1 week'::INTERVAL AND path = '/api/user/login' AND users.id = user_id ORDER BY user_id;")
rows = cursor.fetchall()
cursor.close()
connection.close()

iplist = {}
devicelist = {}
namelist = {}
for row in rows:
    id = row[0]
    name = row[1]
    ip = row[2]
    device = row[3]
    namelist[id] = name
    if id not in iplist:
        iplist[id] = set()
    if ip not in whitelist:
        iplist[id].add(ip)
    if id not in devicelist:
        devicelist[id] = set()
    if device:
        device = re.search(r'\(([^)]+)\)', device).group(1)
        devicelist[id].add(device)
for id in iplist:
    ipcount = len(iplist[id])
    if ipcount > 1:
        compose += '\n{} {}\n'.format(str(id), namelist[id])
        for device in devicelist[id]:
            compose += '{}\n'.format(device)
        for addr in iplist[id]:
            data = requests.get(
                url='https://api.ipgeolocation.io/ipgeo?apiKey={}&ip={}'.format(apikey, addr)).json()
            isp = data['isp']
            conn = data['connection_type']
            isp = isp.replace('Mobile-Broadband', 'M1')
            isp = isp.replace('MOBILEONELTD', 'M1')
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

for id in devicelist:
    if id not in iplist:
        devicecount = len(devicelist[id])
        if devicecount > 1:
            compose += '\n{} {}\n'.format(str(id), namelist[id])
            compose += '{} devices on 1 IP\n'.format(str(devicecount))
            for device in devicelist[id]:
                compose += '{}\n'.format(device)

compose = compose.replace(
    'Singapore Telecommunications Ltd, Magix Services', 'SingTel Fibre')
compose = compose.replace(
    'Singapore Telecommunications Ltd SingTel Mobile', 'SingTel')
compose = compose.replace(
    'Singapore Telecom Mobile Pte Ltd', 'SingTel')
compose = compose.replace('SGCABLEVISION', 'Starhub')
compose = compose.replace('Starhub Internet Pte Ltd', 'Starhub Mobile')
compose = compose.replace('StarHub-Ltd-NGNBN-Services', 'Starhub Fibre')

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
if len(message.strip()) > 0:
    bot.send_message(chat_id=group, text=message)
