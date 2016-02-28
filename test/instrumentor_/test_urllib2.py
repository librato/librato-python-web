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


import unittest
import six

from externaltest_base import BaseExternalTest
from librato_python_web.instrumentor.external.urllib2_ import Urllib2Instrumentor
from librato_python_web.instrumentor.external.py3_urllib import UrllibInstrumentor

UrllibInstrumentor().run()
Urllib2Instrumentor().run()


class Urllib2Test(BaseExternalTest, unittest.TestCase):
    expected_web_state_counts = {
        'external.http.requests': 1,
        'external.http.status.2xx': 1,
        'external.file.requests': 1,
        'external.ftp.requests': 1,
    }
    expected_web_state_gauges = [
        'external.http.response.latency',
        'external.file.response.latency',
        'external.ftp.response.latency',
    ]

    def make_requests(self):
        # HTTP
        r = six.moves.urllib.request.urlopen("http://www.python.org")

        self.assertEqual(r.getcode(), 200)

        data = r.read(100)
        self.assertEqual(len(data), 100)

        data = r.readline()
        self.assertGreater(len(data), 1)

        self.iterate_lines(r, 1000, 10000)

        # File
        r = six.moves.urllib.request.urlopen("file:///etc/hosts")
        self.iterate_lines(r, 1, 10)

        # FTP
        r = six.moves.urllib.request.urlopen("ftp://speedtest.tele2.net/")
        self.iterate_lines(r, 10, 100)


if __name__ == '__main__':
    unittest.main()
