import re
email_regex = re.compile('"args":".*","http')

allusers = set()
logs = ['log1.txt', 'log2.txt', 'log3.txt', 'log4.txt', 'log5.txt']

for log in logs:
    with open(log, 'r') as logfile:
        for line in logfile:
            try:
                email = email_regex.search(line).group()
                email = email.split(',')[0]
                email = email.replace('"args":"', '')
                email = email.strip('"')
                email = email.split('&')[0]
                allusers.add(email)
            except:
                pass

print(len(allusers))

for user in allusers:
    print(user)
