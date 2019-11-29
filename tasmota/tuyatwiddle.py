#!/usr/bin/python

import time
from urllib.request import urlopen


for i in range(0, 99):
    url = 'http://sonoff14/cs?c2=65&c1=TuyaSend4+107,00%d' % i
    print(url)
    urlopen(url)
