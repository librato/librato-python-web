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

# Modified to be used to post metrics to Librato-StatsD style collector
# Support 'tags' and multi-dimensional metrics interface

import socket
import random
import sys
import time
import traceback as tb

from six import print_


# Sends statistics to the stats daemon over UDP
class Client(object):

    def __init__(self, host='localhost', port=8142, prefix=None):
        """
        Create a new StatsD client.
        * host: the host where statsd is listening, defaults to localhost
        * port: the port where statsd is listening, defaults to 8142
        >>> import ./statsd_client
        >>> client = statsd_client.Client(host, port)
        """
        self.host = host
        self.port = int(port)
        self.addr = (socket.gethostbyname(self.host), self.port)
        self.prefix = prefix
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def timing_since(self, stat, start, sample_rate=1, tags=None):
        """
        Log timing information as the number of microseconds since the provided time float
        >>> start = time.time()
        >>> # do stuff
        >>> client.timing_since('some.time', start)
        """
        self.timing(stat, int((time.time() - start) * 1000000), sample_rate, tags)

    def timing(self, stat, time, sample_rate=1, tags=None):
        """
        Log timing information for a single stat
        >>> client.timing('some.time',500)
        """
        stats = {stat: "%f|ms" % time}
        self.send(stats, sample_rate, tags)

    def gauge(self, stat, value, sample_rate=1, tags=None):
        """
        Log gauge information for a single stat
        >>> client.gauge('some.gauge',42)
        """
        stats = {stat: "%f|g" % value}
        self.send(stats, sample_rate, tags)

    def increment(self, stats, sample_rate=1, tags=None):
        """
        Increments one or more stats counters
        >>> client.increment('some.int')
        >>> client.increment('some.int',0.5)
        """
        self.update_stats(stats, 1, sample_rate=sample_rate, tags=tags)

    # alias
    incr = increment

    def decrement(self, stats, sample_rate=1, tags=None):
        """
        Decrements one or more stats counters
        >>> client.decrement('some.int')
        """
        self.update_stats(stats, -1, sample_rate=sample_rate, tags=tags)

    # alias
    decr = decrement

    def update_stats(self, stats, delta, sample_rate=1, tags=None):
        """
        Updates one or more stats counters by arbitrary amounts
        >>> client.update_stats('some.int',10)
        """
        if not isinstance(stats, list):
            stats = [stats]

        data = dict((stat, "%s|c" % delta) for stat in stats)
        self.send(data, sample_rate, tags)

    def send(self, data, sample_rate=1, tags=None):
        """
        Squirt the metrics over UDP
        <name>:<value>|<metric_type>|@<sample_rate>|#<tag1_name>:<tag1_value>,
                            <tag2_name>:<tag2_value>:<value>|<metric_type>...
        """

        if self.prefix:
            data = dict((".".join((self.prefix, stat)), value) for stat, value in data.items())

        if sample_rate < 1:
            if random.random() > sample_rate:
                return
            sampled_data = dict((stat, "%s|@%s" % (value, sample_rate))
                                for stat, value in data.items())
        else:
            sampled_data = data

        if tags:
            tags_string = ",".join(("%s:%s" % key_val for key_val in tags.items()))
            sampled_data = dict((stat, "%s|#%s" % (value, tags_string))
                                for stat, value in sampled_data.items())

        [self._send_packet("%s:%s" % (stat, value))
         for stat, value in sampled_data.items()]

    def _send_packet(self, packet):
        try:
            self.udp_sock.sendto(bytes(bytearray(packet, "utf-8")), self.addr)
        except:
            print_("Error reporting metrics", file=sys.stderr)
            tb.print_exc()

    def __repr__(self):
        return "<pystatsd.statsd.Client addr=%s prefix=%s>" % (self.addr, self.prefix)

    def define_alias(self, alias, value):
        """
            Send an alias definition to the StatsD server. An alias line looks like this:
            _a:<alias_name>|<actual_value>
        """
        escapped_value = value.replace('\n', '\\n')
        packet = "_a:%s|%s" % (alias, escapped_value)
        self._send_packet(packet)


if __name__ == '__main__':
    host = "127.0.0.1"
    port = 8142
    print("Sending statsd packets to %s:%d" % (host, port))

    client = Client(host, port)

    tags = {
        "name": "bob",
        "type": "foo"
    }

    tags2 = {
        "name": "TIM",
        "type": "FOO"
    }

    client.gauge("my.gauge", 12, tags=tags)
    client.gauge("my.sampled.gauge", 10, 0.9999, tags)
    client.gauge("my.sampled.gauge", 30, 0.9999, tags2)
    client.gauge("my.sampled.gauge", 44, 0.9999, tags2)
    client.gauge("my.tag.free.gauge", 20)
    client.gauge("my.tag.free.gauge.sampled", 20, 0.9999)

    client.increment("my.counter", tags=tags)

    client.define_alias('abc123', 'My long text goes here')
    client.define_alias('abc124', """This line as a new line
    right above me!""")
