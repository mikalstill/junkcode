#!/usr/bin/python

# Based heavily on https://github.com/AICoE/prometheus-api-client-python/blob/master/examples/MetricsList_example.ipynb

from dateutil import tz

from prometheus_api_client import Metric, MetricsList, PrometheusConnect
from prometheus_api_client.utils import parse_datetime, parse_timedelta


class PromSummarizer(object):
    def __init__(self, url, disable_ssl=False):
        self.prom = PrometheusConnect(url=url, disable_ssl=disable_ssl)

    def fetch(self, expression, number_of_days):
        start_time = parse_datetime('%dd' % number_of_days)
        end_time = parse_datetime('now')
        chunk_size = parse_timedelta('now', '1d')

        metric_data = self.prom.get_metric_range_data(
            expression,
            start_time=start_time,
            end_time=end_time,
            chunk_size=chunk_size,
        )

        # MetricsList combines the chunks into a single metric
        metric = MetricsList(metric_data)[0]

        # Yield tuples of timestamp, value
        for value in metric.metric_values.values:
            ts, val = value.tolist()

            # The timestamp is delivered in UTC, convert to local
            ts = ts.to_pydatetime().replace(tzinfo=tz.tzutc())
            ts = ts.astimezone(tz.tzlocal())

            yield ts, val
