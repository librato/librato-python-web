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

import bootstrap    # Initialize instrumentation

import os
import django
from django.test import LiveServerTestCase as TestCase

from librato_python_web.instrumentor import telemetry
from librato_python_web.instrumentor.telemetry import TestTelemetryReporter

os.environ['DJANGO_SETTINGS_MODULE'] = 'test_site.settings'
django.setup()


class DjangoTestCase(TestCase):
    def setUp(self):
        self.reporter = TestTelemetryReporter()
        telemetry.set_reporter(self.reporter)

    def tearDown(self):
        telemetry.set_reporter(None)

    def check_tags(self, reporter, check_handler=True):
        """ Do some generic tag validation """
        gauge_names = reporter.get_gauge_names()

        for dict_ in [reporter.md_gauges, reporter.md_counters]:
            for metric in dict_:
                # All metrics should include the 'method' tag names
                self.assertIn('method', dict_[metric].keys())

                if check_handler:
                    self.assertIn('handler', dict_[metric].keys())

                # Only wsgi metrics should include the 'status' tag
                if metric.startswith('wsgi.'):
                    self.assertIn('status', dict_[metric].keys())
                else:
                    self.assertNotIn('status', dict_[metric].keys())

        for metric in ['app.response.latency', 'wsgi.response.latency', 'web.response.latency']:
            # All latencies should be positive
            for tag in self.reporter.md_gauges[metric].keys():
                for tag_value in self.reporter.md_gauges[metric][tag].keys():
                    self.assertGreater(self.reporter.md_gauges[metric][tag][tag_value], 0)
