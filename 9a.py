import re
from collections import OrderedDict

logname = 'English Service'
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
                    ipmap[ip] = ipcount
                email = 'User_' + str(ipmap[ip])
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
        prelog += firstseen[item] + '-' + 'now' + '\n'
    elif item in lastseen:
        prelog += item + ' '
        prelog += firstseen[item] + '-' + lastseen[item] + '\n'

print(prelog)
