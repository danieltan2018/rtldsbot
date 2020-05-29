import psycopg2
from secret import dbuser, dbpass, dbhost, dbport, dbdata

connection = psycopg2.connect(user=dbuser,
                              password=dbpass,
                              host=dbhost,
                              port=dbport,
                              database=dbdata)
cursor = connection.cursor()
cursor.execute(
    "SELECT user_id, ip_address FROM user_activities WHERE path = '/api/user/login'")
rows = cursor.fetchall()
iplist = {}
for row in rows:
    id = row[0]
    ip = row[1]
    if id not in iplist:
        iplist[id] = set()
    iplist[id].add(ip)
for id in iplist:
    ipcount = len(iplist[id])
    if ipcount > 1:
        print(id, ipcount)

cursor.close()
connection.close()
