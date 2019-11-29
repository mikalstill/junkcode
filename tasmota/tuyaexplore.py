#!/usr/bin/python

import colorama
import json
import re
import sys
import time
from urllib.request import urlopen

# Tuya dpId status
# 06:07:15 {"TuyaReceived":{"Data":"55AA030700086C0200040000009619","Cmnd":7,
# "CmndData":"6C02000400000096","DpId":108,"DpIdType":2,"DpIdData":"00000096"}}
status_re = re.compile(
    '.*"DpId":([0-9]+),"DpIdType":([0-9]+),"DpIdData":(.*)}}')


def readDpIds_inner(fromline):
    time.sleep(0.1)
    linecount = 1
    dpIds = {}
    for line in urlopen('http://sonoff14/cs?c2=%d' % fromline).readlines():
        line = line.rstrip()
        m = status_re.match(line.decode('utf-8'))
        if m:
            dpIds['%s, type %s' % (m.group(1), m.group(2))] = m.group(
                3).strip('"').rstrip('"')
        linecount += 1

    return linecount, dpIds


def readDpIds(fromline):
    dpIds = {}
    while len(dpIds) == 0:
        readlines, dpIds = readDpIds_inner(fromline)
        time.sleep(0.5)
    return readlines, dpIds


linecount = 0
urlopen('http://sonoff14/cs?c2=65&c1=SerialSend5%2055aa0001000000')
readlines, previousDpIds = readDpIds(linecount)
linecount += readlines

# Header
for key in sorted(previousDpIds.keys()):
    sys.stdout.write('%15s' % key)
sys.stdout.write('\n')

# First set of values
for key in sorted(previousDpIds.keys()):
    sys.stdout.write('%15s' % previousDpIds[key])
sys.stdout.write('\n')

while True:
    readlines, dpIds = readDpIds(linecount)
    linecount += readlines

    if previousDpIds != dpIds:
        for key in sorted(dpIds.keys()):
            if previousDpIds[key] == dpIds[key]:
                sys.stdout.write(colorama.Fore.GREEN)
            else:
                sys.stdout.write(colorama.Fore.RED)
            sys.stdout.write('%15s' % dpIds[key])
        sys.stdout.write('\n')
        previousDpIds = dpIds

    urlopen('http://sonoff14/cs?c2=65&c1=SerialSend5%2055aa0001000000')
    time.sleep(0.5)
