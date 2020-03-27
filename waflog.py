import re
email_regex = re.compile('"args":".*@[a-zA-Z0-9]*.[a-zA-Z0-9]*"')

allusers = set()
logs = ['log1.txt', 'log2.txt', 'log3.txt', 'log4.txt', 'log5.txt']

for log in logs:
    with open(log, 'r') as logfile:
        for line in logfile:
            try:
                email = email_regex.search(line).group()
                email = email.replace('"args":"', '')
                email = email.strip('"')
                allusers.add(email)
            except:
                pass

print(len(allusers))

for user in allusers:
    print(user)
