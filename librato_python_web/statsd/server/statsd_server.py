# Based on https://github.com/sivy/pystatsd
#
# Copyright (c) 2014, Steve Ivy
# All rights reserved.
#
# Copyright (c) 2015. Librato, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Librato, Inc. nor the names of project contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL LIBRATO, INC. BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import re
import os
import signal
import sys
import socket
import threading
import time
import math
import logging

from .daemon import Daemon

import librato
import librato_python_web.tools.agent_config as config

LIBRATO_HOSTNAME = "metrics-api.librato.com"

logger = logging.getLogger(__name__)

try:
    from setproctitle import setproctitle
except ImportError:
    setproctitle = None

__all__ = ['Server']


def _clean_key(k):
    return re.sub(r'[^a-zA-Z_\-0-9\.]', '',
                  re.sub(r'\s+', '_', k.replace('/', '-').replace(' ', '_')))


def kill_process(proc_name):
    for line in os.popen("ps ax | grep " + proc_name + " | grep -v grep"):
        fields = line.split()
        pid = fields[0]
        os.kill(int(pid), signal.SIGKILL)


class Server(object):

    def __init__(self, librato_user, librato_api_token,
                 pct_threshold=90, debug=False, flush_interval=60000,
                 no_aggregate_counters=False, expire=0, source_prefix='',
                 librato_hostname=LIBRATO_HOSTNAME, prefix=None):
        self.buf = 8192
        self.flush_interval = float(flush_interval/1000)
        self.pct_threshold = pct_threshold

        self.no_aggregate_counters = no_aggregate_counters
        self.debug = debug
        self.expire = expire
        self.hostname = socket.gethostname()

        parts = librato_hostname.split("://")
        if len(parts) > 2:
            raise ValueError("Malformed hostname: {}".format(librato_hostname))
        elif len(parts) == 2:
            protocol, librato_hostname = parts
            if protocol not in ["http", "https"]:
                raise ValueError("Unsupported protocol: {}".format(protocol))
        else:
            protocol = "https"

        self.api = librato.connect(librato_user, librato_api_token,
                                   hostname=librato_hostname,
                                   protocol=protocol,
                                   sanitizer=librato.sanitize_metric_name)

        self.counters = {}
        self.timers = {}
        self.gauges = {}
        self.aliases = {}
        self._sock = None
        self.prefix = prefix
        if source_prefix:
            self.source = '{}-{}'.format(source_prefix, self.hostname)
        else:
            self.source = self.hostname

    def process(self, data):
        # the data is a sequence of newline-delimited metrics
        # a metric is in the form "name:value|rest"  (rest may have more pipes)
        # <name>:<value>|<metric_type>|@<sample_rate>|#<tag1_name>:<tag1_value>,<tag2_name>:<tag2_value>:<value>
        data.rstrip('\n')
        metric_lines = data.split('\n')

        for metric in metric_lines:
            match = re.match('\A([^:]+):([^|]+)\|(.+)', metric)

            if match is None:
                logger.warning("Skipping malformed metric: <%s>", metric)
                continue

            key = _clean_key(match.group(1))
            value = match.group(2)
            rest = match.group(3).split('|')
            m_type = rest.pop(0)

            if key == '_a':
                self.__record_alias(value, m_type)
                return

            tags = None
            if rest and rest[-1][0] == '#':
                tag_string = rest[-1][1:].lower()
                tags = tuple(sorted([tuple(x.split(':')) for x in tag_string.split(',')]))
                rest.pop()

            if m_type == 'ms':
                self.__record_timer(key, value, rest, tags)
            elif m_type == 'g':
                self.__record_gauge(key, value, rest, tags)
            elif m_type == 'c':
                self.__record_counter(key, value, rest, tags)
            else:
                logger.warning("Encountered unknown metric type in <%s>", metric)

    def __record_timer(self, key, value, rest, tags):
        ts = int(time.time())
        timer = self.timers.setdefault(self.__make_context(key, tags), [[], ts])
        timer[0].append(float(value or 0))
        timer[1] = ts

    def __record_gauge(self, key, value, rest, tags):
        ts = int(time.time())
        self.gauges[self.__make_context(key, tags)] = [float(value), ts]

    def __record_counter(self, key, value, rest, tags):
        ts = int(time.time())
        sample_rate = 1.0
        if len(rest) == 1:
            sample_rate = float(re.match('^@([\d\.]+)', rest[0]).group(1))
            if sample_rate == 0:
                logger.warning("Ignoring counter with sample rate of zero: <%s>", key)
                return

        counter = self.counters.setdefault(self.__make_context(key, tags), [0, ts])
        counter[0] += float(value or 1) * (1 / sample_rate)
        counter[1] = ts

    def __record_alias(self, alias, value):
        unescaped_value = value.replace('\\n', '\n')
        self.aliases[alias] = unescaped_value

    def __make_context(self, key, tags):
        if tags is None:
            return key, tuple()

        return key, tuple(tags)

    def on_timer(self):
        """Executes flush(). Ignores any errors to make sure one exception
        doesn't halt the whole flushing process.
        """
        try:
            self.flush()
        except Exception as e:
            logger.exception('Error while flushing: %s', e)
        self._set_timer()

    def flush(self):
        ts = int(math.floor(time.time()/self.flush_interval) * self.flush_interval)
        stats = 0

        with self.api.new_queue() as queue:
            stats += self._process_counters(queue, ts)
            stats += self._process_gauges(queue, ts)
            stats += self._process_timers(queue, ts)

            if stats > 0:
                self._add_to_queue(queue, "statsd.numStats", stats, ts)

        if stats > 0:
            logger.debug("\n====Flush completed. Waiting until next flush. Sent out %d metrics ====", stats)

    def _process_counters(self, queue, ts):
        stats = 0

        # Make a copy of keys since dict can change
        for context in list(self.counters):
            (v, t) = self.counters[context]

            # default to counter, no_aggregate_counters defaults to false
            metric_type = "gauge" if self.no_aggregate_counters else "counter"
            logger.debug("Sending %s => count=%s", context, v)

            self._add_to_queue(queue, context[0] + ".count", v, ts, metric_type, tags=context[1])

            # Clear the counter once the data is sent, if this is a counter as a gauge
            if self.no_aggregate_counters:
                del (self.counters[context])
            stats += 1

        return stats

    def _process_gauges(self, queue, ts):
        stats = 0

        # Make a copy of keys since dict can change
        for context in list(self.gauges):
            (v, t) = self.gauges[context]

            if self.expire > 0 and t + self.expire < ts:
                logger.debug("Expiring gauge %s (age: %s)", context, ts - t)
                del(self.gauges[context])
                continue

            v = float(v)
            logger.debug("Sending %s => value=%s", context, v)

            self._add_to_queue(queue, context[0], v, ts, tags=context[1])
            del(self.gauges[context])
            stats += 1

        return stats

    def _process_timers(self, queue, ts):
        stats = 0

        # Create a copy of keys since the loop modifies the timers dict
        for context in list(self.timers):
            (v, t) = self.timers[context]
            if self.expire > 0 and t + self.expire < ts:
                logger.debug("Expiring timer %s (age: %s)", context, ts - t)
                del(self.timers[context])
                continue

            if len(v) > 0:
                # Sort all the received values. We need it to extract percentiles
                v.sort()
                count = len(v)
                min_ = v[0]
                max_ = v[-1]

                if count == 1:
                    mean = min_
                    max_threshold = max_
                    median = min_
                    total = min_
                    sum_squares = min_ * min_
                else:
                    index = int(math.floor(count/2))
                    if count % 2 == 0:
                        median = (v[index] + v[index-1]) / 2
                    else:
                        median = v[index]
                    index = int((self.pct_threshold / 100.0) * count)
                    max_threshold = v[index - 1]
                    total = sum(v)
                    sum_squares = sum([i**2 for i in v])
                    mean = total / count

                del(self.timers[context])

                logger.debug("Sending %s ====> lower=%s, mean=%s, upper=%s, %dpct=%s, count=%s",
                             context, min_, mean, max_, self.pct_threshold, max_threshold, count)

                prefix = context[0] + "."
                self._add_to_queue(queue, prefix + "median", median, ts, tags=context[1])
                self._add_to_queue(queue, prefix + "upper_" + str(self.pct_threshold), max_threshold, ts,
                                   tags=context[1])
                self._add_to_queue(queue, prefix + "count", count, ts, tags=context[1])
                self._add_gauge_to_queue(queue, prefix + "mean", mean, ts, count=count,
                                         min_=min_, max_=max_, sum_=total, sum_squares=sum_squares, tags=context[1])
                # we only count this timer as a single stat even though we generated multiple measurements
                stats += 1

        return stats

    def _add_to_queue(self, queue, key, value, timestamp, metric_type='gauge', tags=None):
        tags_dict = dict(tags) if tags else {}
        if 'source' not in tags_dict:
            tags_dict['source'] = self.source
        metric = '{}.{}'.format(self.prefix, key) if self.prefix else key
        queue.add(metric, value, metric_type, measure_time=timestamp, source=self.source)
        logger.debug("%s %s => %s", metric_type, metric, value)

    def _add_gauge_to_queue(self, queue, key, value, timestamp, min_=None, max_=None, count=1,
                            sum_=None, sum_squares=None, tags=None):
        tags_dict = dict(tags) if tags else {}
        if 'source' not in tags_dict:
            tags_dict['source'] = self.source
        metric = '{}.{}'.format(self.prefix, key) if self.prefix else key
        queue.add(metric, None, 'gauge', measure_time=timestamp,
                  source=self.source, count=count, sum=sum_, max=max_, min=min_, sum_squares=sum_squares)
        logger.debug("gauge %s => %s", metric, value)

    def _set_timer(self):
        self._timer = threading.Timer(self.flush_interval, self.on_timer)
        self._timer.daemon = True
        self._timer.start()

    def serve(self, hostname='localhost', port=8142):
        assert type(port) is int, 'port is not an integer: %s' % port
        addr = (hostname, port)
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.bind(addr)
        except socket.error as e:
            # kill my alter ego
            if e.errno == socket.errno.EADDRINUSE:  # port in use
                logger.info("%s: attempt to kill, hanging librato-statsd-server", e.strerror)
                kill_process('librato-statsd-server')
            # cause the launcher to restart me
            raise

        logger.debug("StatsD Server listening on '%s' UDP port %d", hostname, port)

        def signal_handler(signal, frame):
            logger.debug("Stopping server...")
            self.stop()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        self._set_timer()

        try:
            while True:
                data, addr = self._sock.recvfrom(self.buf)
                try:
                    self.process(data.decode('UTF-8'))
                except Exception as error:
                    logger.exception("Bad data from %s: %s", addr, error)
        except socket.error as e:
            # Ignore interrupted system calls from sigterm.
            if e.errno != socket.errno.EINTR:
                raise

    def stop(self):
        self._timer.cancel()
        self._sock.close()


class ServerDaemon(Daemon):
    def run(self, options):
        if setproctitle:
            setproctitle('solarwinds-python-statsd')

        logger.debug('Solarwinds StatsD Server for Librato account: "%s"', options.user)

        server = Server(librato_user=options.user,
                        librato_api_token=options.api_token,
                        pct_threshold=options.pct,
                        debug=options.debug,
                        flush_interval=options.flush_interval,
                        no_aggregate_counters=options.no_aggregate_counters,
                        expire=options.expire,
                        source_prefix=options.app_id,
                        librato_hostname=options.metrics_hostname)

        server.serve(options.hostname, options.port)


def run_server():
    options = config.load_config()

    log_level = logging.DEBUG if options.debug else logging.WARNING
    logging.basicConfig(level=log_level, format='%(asctime)s [%(levelname)s] %(message)s')

    (isvalid, errors) = config.validate_config(options)
    if not isvalid:
        logger.error("Invalid Configuration:\n  %s", "\n  ".join(errors))
        return 2

    daemon = ServerDaemon(options.pidfile)
    if options.daemonize:
        daemon.start(options)
    elif options.restart:
        daemon.restart(options)
    elif options.stop:
        daemon.stop()
    else:
        daemon.run(options)
    return 0

if __name__ == '__main__':
    sys.exit(run_server())
