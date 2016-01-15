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

from librato_python_web.instrumentor import telemetry
from librato_python_web.instrumentor.telemetry import TestTelemetryReporter

import bootstrap        # Initialize the instrumentation
import hello_app


class HelloTestCase(unittest.TestCase):
    def setUp(self):
        hello_app.app.config['TESTING'] = True
        self.app = hello_app.app.test_client()

        self.reporter = TestTelemetryReporter()
        telemetry.set_reporter(self.reporter)

    def tearDown(self):
        telemetry.set_reporter(None)

    def test_once(self):
        r = self.app.get('/')

        expected_gauge_metrics = ['app.response.latency', 'wsgi.response.latency', 'web.response.latency']
        self.assertEqual(r.status_code, 200)
        self.assertItemsEqual(self.reporter.get_gauge_names(), expected_gauge_metrics)
        self.assertGreater(self.reporter.get_gauge_value('wsgi.response.latency'),
                           self.reporter.get_gauge_value('web.response.latency'))

        self.assertEqual(self.reporter.counts, {'web.status.2xx': 1, 'web.requests': 1})

    def test_twice(self):
        r = self.app.get('/')
        r = self.app.get('/')

        expected_gauge_metrics = ['app.response.latency', 'wsgi.response.latency', 'web.response.latency']
        self.assertEqual(r.status_code, 200)
        self.assertItemsEqual(self.reporter.get_gauge_names(), expected_gauge_metrics)

        self.assertEqual(self.reporter.counts, {'web.status.2xx': 2, 'web.requests': 2})

    def test_redirect(self):
        # Excluding the trailing will redirect
        r = self.app.get('/dir')

        self.assertEqual(r.status_code, 301)

        expected_gauge_metrics = ['app.response.latency', 'wsgi.response.latency', 'web.response.latency']
        self.assertItemsEqual(self.reporter.get_gauge_names(), expected_gauge_metrics)
        self.assertEqual(self.reporter.counts, {'web.status.3xx': 1, 'web.requests': 1})

    def test_notfound(self):
        r = self.app.get('/notfound/')

        self.assertEqual(r.status_code, 404)
        self.assertIn("Verify this text!", r.data)

        expected_gauge_metrics = ['app.response.latency', 'wsgi.response.latency', 'web.response.latency']
        self.assertItemsEqual(self.reporter.get_gauge_names(), expected_gauge_metrics)
        self.assertEqual(self.reporter.counts, {'web.status.4xx': 1, 'web.requests': 1})

    def test_error(self):
        r = self.app.get('/error/')

        self.assertEqual(r.status_code, 505)

        expected_gauge_metrics = ['app.response.latency', 'wsgi.response.latency', 'web.response.latency']
        self.assertItemsEqual(self.reporter.get_gauge_names(), expected_gauge_metrics)

        self.assertEqual(self.reporter.counts, {'web.status.5xx': 1, 'web.requests': 1})


if __name__ == '__main__':
    unittest.main()
