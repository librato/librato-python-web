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

import bootstrap    # Initialize instrumentaion

import six
import unittest
import cherrypy
from cherrypy.test import helper
from test_helper import TestCaseBase

from librato_python_web.instrumentor import telemetry
from librato_python_web.instrumentor.telemetry import TestTelemetryReporter

import hello_app


class HelloTestCase(TestCaseBase):
    def setup_server():
        cherrypy.tree.mount(hello_app.HelloWorld())
    setup_server = staticmethod(setup_server)

    def setUp(self):
        self.reporter = TestTelemetryReporter()
        telemetry.set_reporter(self.reporter)

    def tearDown(self):
        telemetry.set_reporter(None)

    def test_once(self):
        self.getPage('/')
        self.assertStatus(200)

        self.check_tags(self.reporter)

        expected_gauge_metrics = ['app.response.latency', 'wsgi.response.latency', 'web.response.latency']
        six.assertCountEqual(self, self.reporter.get_gauge_names(), expected_gauge_metrics)

        tags = {'handler': 'hello_app.HelloWorld.index', 'method': 'GET'}
        for tag in tags:
            tag_value = tags[tag]

            self.assertGreater(self.reporter.get_gauge('wsgi.response.latency', tag, tag_value),
                               self.reporter.get_gauge('web.response.latency', tag, tag_value))

            self.assertEqual(self.reporter.get_count('web.status.1xx', tag, tag_value), 0)
            self.assertEqual(self.reporter.get_count('web.status.2xx', tag, tag_value), 1)
            self.assertEqual(self.reporter.get_count('web.status.3xx', tag, tag_value), 0)
            self.assertEqual(self.reporter.get_count('web.status.4xx', tag, tag_value), 0)
            self.assertEqual(self.reporter.get_count('web.status.5xx', tag, tag_value), 0)
            self.assertEqual(self.reporter.get_count('web.requests', tag, tag_value), 1)

        self.assertGreater(self.reporter.get_gauge('wsgi.response.latency', 'status', '200'), 0)

    def test_twice(self):
        self.getPage('/')
        self.getPage('/')
        self.assertStatus(200)

        self.check_tags(self.reporter)

        expected_gauge_metrics = ['app.response.latency', 'wsgi.response.latency', 'web.response.latency']
        six.assertCountEqual(self, self.reporter.get_gauge_names(), expected_gauge_metrics)

        tags = {'handler': 'hello_app.HelloWorld.index', 'method': 'GET'}
        for tag in tags:
            tag_value = tags[tag]
            self.assertEqual(self.reporter.get_count('web.status.1xx', tag, tag_value), 0)
            self.assertEqual(self.reporter.get_count('web.status.2xx', tag, tag_value), 2)
            self.assertEqual(self.reporter.get_count('web.status.3xx', tag, tag_value), 0)
            self.assertEqual(self.reporter.get_count('web.status.4xx', tag, tag_value), 0)
            self.assertEqual(self.reporter.get_count('web.status.5xx', tag, tag_value), 0)
            self.assertEqual(self.reporter.get_count('web.requests', tag, tag_value), 2)

        self.assertGreater(self.reporter.get_gauge('wsgi.response.latency', 'status', '200'), 0)

    def test_redirect(self):
        self.getPage('/redirect')
        self.assertStatus(303)

        expected_gauge_metrics = ['app.response.latency', 'wsgi.response.latency', 'web.response.latency']
        six.assertCountEqual(self, self.reporter.get_gauge_names(), expected_gauge_metrics)

        tags = {'handler': 'hello_app.HelloWorld.redirect', 'method': 'GET'}
        for tag in tags:
            tag_value = tags[tag]

            self.assertEqual(self.reporter.get_count('web.status.1xx', tag, tag_value), 0)
            self.assertEqual(self.reporter.get_count('web.status.2xx', tag, tag_value), 0)
            self.assertEqual(self.reporter.get_count('web.status.3xx', tag, tag_value), 1)
            self.assertEqual(self.reporter.get_count('web.status.4xx', tag, tag_value), 0)
            self.assertEqual(self.reporter.get_count('web.status.5xx', tag, tag_value), 0)
            self.assertEqual(self.reporter.get_count('web.requests', tag, tag_value), 1)

        self.assertGreater(self.reporter.get_gauge('wsgi.response.latency', 'status', '303'), 0)

    def test_notfound(self):
        self.getPage('/notfound')
        self.assertStatus(404)

        self.check_tags(self.reporter)

        expected_gauge_metrics = ['app.response.latency', 'wsgi.response.latency', 'web.response.latency']
        six.assertCountEqual(self, self.reporter.get_gauge_names(), expected_gauge_metrics)

        tags = {'handler': 'hello_app.HelloWorld.notfound', 'method': 'GET'}
        for tag in tags:
            tag_value = tags[tag]

            self.assertEqual(self.reporter.get_count('web.status.1xx', tag, tag_value), 0)
            self.assertEqual(self.reporter.get_count('web.status.2xx', tag, tag_value), 0)
            self.assertEqual(self.reporter.get_count('web.status.3xx', tag, tag_value), 0)
            self.assertEqual(self.reporter.get_count('web.status.4xx', tag, tag_value), 1)
            self.assertEqual(self.reporter.get_count('web.status.5xx', tag, tag_value), 0)
            self.assertEqual(self.reporter.get_count('web.requests', tag, tag_value), 1)

        self.assertGreater(self.reporter.get_gauge('wsgi.response.latency', 'status', '404'), 0)

    def test_error(self):
        self.getPage('/error')
        self.assertStatus(505)

        expected_gauge_metrics = ['app.response.latency', 'wsgi.response.latency', 'web.response.latency']
        six.assertCountEqual(self, self.reporter.get_gauge_names(), expected_gauge_metrics)

        self.check_tags(self.reporter)

        tags = {'handler': 'hello_app.HelloWorld.error', 'method': 'GET'}
        for tag in tags:
            tag_value = tags[tag]

            self.assertEqual(self.reporter.get_count('web.status.1xx', tag, tag_value), 0)
            self.assertEqual(self.reporter.get_count('web.status.2xx', tag, tag_value), 0)
            self.assertEqual(self.reporter.get_count('web.status.3xx', tag, tag_value), 0)
            self.assertEqual(self.reporter.get_count('web.status.4xx', tag, tag_value), 0)
            self.assertEqual(self.reporter.get_count('web.status.5xx', tag, tag_value), 1)
            self.assertEqual(self.reporter.get_count('web.requests', tag, tag_value), 1)

        self.assertGreater(self.reporter.get_gauge('wsgi.response.latency', 'status', '505'), 0)


if __name__ == '__main__':
    unittest.main()
