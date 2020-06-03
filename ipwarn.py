import telegram.bot
from bs4 import BeautifulSoup
import psycopg2
import requests
import time
from secret import bottoken, group, dbuser, dbpass, dbhost, dbport, dbdata

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
    iplist[id].add(ip)
for id in iplist:
    ipcount = len(iplist[id])
    if ipcount > 1:
        compose += '\n{} {}\n'.format(str(id), namelist[id])
        for addr in iplist[id]:
            url = 'https://whatismyipaddress.com/ip/111.65.68.185'
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"}
            resp = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(resp.content, "html.parser")
            table = soup.find("table")
            data = {}
            rows = table.find_all('tr')
            for row in rows:
                k = row.find('th').get_text()
                v = row.find('td').get_text()
                data[k] = v
            x_isp = data['ISP:']
            x_type = data['Type:']
            if x_type == 'Wireless Broadband':
                if 'mobile' in x_isp.lower():
                    x_type = ''
                else:
                    x_type = 'Mobile'
            x_full = '{} - {}'.format(x_isp, x_type).strip(' -')
            compose += addr + ' ({})\n'.format(x_full)

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
