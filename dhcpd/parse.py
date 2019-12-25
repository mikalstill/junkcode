#!/usr/bin/python

# A simple example use of iscconf to parse DHCP configuration files

import iscconf

with open('dhcpd.conf') as f:
    conf = iscconf.parse(f.read())

print(conf)
