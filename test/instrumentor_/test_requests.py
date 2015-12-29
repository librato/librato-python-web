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

import requests
from librato_python_web.instrumentor import telemetry
from librato_python_web.instrumentor.context import push_state, pop_state

from test_reporter import TestTelemetryReporter


class RequestsTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def call_requests(self):
        requests.get('http://www.solarwinds.com')

    def test_requests(self):
        reporter = TestTelemetryReporter()
        telemetry.set_reporter(reporter)

        try:
            push_state('web')
            self.call_requests()
        finally:
            pop_state('web')

        self.assertTrue(reporter.counts)
        self.assertTrue(reporter.records)

        print reporter.counts
        print reporter.records

    def test_requests_nostate(self):
        reporter = TestTelemetryReporter()
        telemetry.set_reporter(reporter)

        self.call_requests()

        self.assertFalse(reporter.counts)
        self.assertFalse(reporter.records)
        print reporter.counts
        print reporter.records

if __name__ == '__main__':
    unittest.main()
