#!/usr/bin/python3

# Read a file in a non-blocking manner

import fcntl
import os


fd = os.open('file.txt', os.O_RDONLY | os.O_NONBLOCK)

fl = fcntl.fcntl(fd, fcntl.F_GETFL)
if (fl & os.O_NONBLOCK) == os.O_NONBLOCK:
    print('non-blocking\n')
else:
    print('blocking\n')

while True:
    d = os.read(fd, 1024).decode('utf-8')
    if d:
        print(d)
