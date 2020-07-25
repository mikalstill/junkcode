#!/usr/bin/python3

# Write random strings with delays to a file so we can test non-blocking
# reads over in read.py

import random
import string
import time


f = open('file.txt', 'w')
while True:
    l = random.randint(1, 20)
    s = ''.join(random.choice(string.ascii_lowercase) for i in range(l))
    print(s)
    f.write(s)
    f.flush()
    time.sleep(random.randint(0, 1000) / 500.0)
