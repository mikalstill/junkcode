#!/usr/bin/python

# Based heavily on https://github.com/AICoE/prometheus-api-client-python/blob/master/examples/MetricsList_example.ipynb

import datetime
import statistics

import dailysummary


def day_stamp(dt):
    return '%04d%02d%02d' % (dt.year, dt.month, dt.day)


prom = dailysummary.PromSummarizer('http://crankee:9090', disable_ssl=True)

# Work out power use and if we have complete data for a day
print('Fetch power usage data')
previous_time = None
previous_val = None

day_power = {}
day_seconds = {}

for ts, val in prom.fetch('watts{exported_instance="all"}', 365):
    if previous_time:
        duration = ts - previous_time
        kw = previous_val / 1000.0
        ph = 3600 / duration.seconds
        kwh = kw / ph

        day = day_stamp(previous_time)
        day_power.setdefault(day, 0)
        day_seconds.setdefault(day, 0)
        day_power[day] += kwh
        day_seconds[day] += duration.seconds

    previous_time = ts
    previous_val = val

# Work out the maximum temperatures
print('Fetch outdoor temperature data')

day_max_temperature = {}
for ts, val in prom.fetch('temp_c{exported_job="sonoff1"}', 365):
    day = day_stamp(ts)
    day_max_temperature.setdefault(day, 0)
    day_max_temperature[day] = max(day_max_temperature[day], val)

# Pivot data by temperature
seconds_in_a_day = 24 * 3600

power_use_by_temperature = {}
for day in day_power:
    if day_seconds.get(day, 0) < seconds_in_a_day * 0.99:
        continue
    elif day_seconds.get(day, 0) > seconds_in_a_day * 1.01:
        continue

    max_temp = int(day_max_temperature.get(day, 0))
    for t in range(max_temp - 2, max_temp + 2):
        power_use_by_temperature.setdefault(t, [])
        power_use_by_temperature[t].append((day, day_power[day]))

# Now compare yesterday with historical data
yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
day = day_stamp(yesterday)
max_temp = int(day_max_temperature[day])

usages = []
print('Power usage for comparable days...')
for compday, power in power_use_by_temperature[max_temp]:
    usages.append(power)

print('Yesterday had a maximum temperature of %d and we used %.02f kwh. '
      'The average for similar days is %.02f kwh.'
      % (max_temp, day_power[day], statistics.mean(usages)))
