import re
email_regex = re.compile('"args":".*","http')

allusers = set()
counter = {}
logs = ['log1.txt', 'log2.txt', 'log3.txt', 'log4.txt', 'log5.txt']

for log in logs:
    with open(log, 'r') as logfile:
        for line in logfile:
            try:
                if '.m3u8' in line:
                    email = email_regex.search(line).group()
                    email = email.split(',')[0]
                    email = email.replace('"args":"', '')
                    email = email.strip('"')
                    email = email.split('&')[0]
                    allusers.add(email)
                    if email in counter:
                        counter[email] += 1
                    else:
                        counter[email] = 1
            except:
                pass

print(len(allusers))
for user in allusers:
    print(user, counter[user]/10)
