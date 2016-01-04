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


from abc import abstractmethod

from librato_python_web.instrumentor import telemetry
from librato_python_web.instrumentor.context import push_state, pop_state
from librato_python_web.instrumentor.telemetry import TestTelemetryReporter


class BaseExternalTest(object):
    def setUp(self):
        self.reporter = TestTelemetryReporter()
        telemetry.set_reporter(self.reporter)

    def tearDown(self):
        telemetry.set_reporter(None)

    def iterate_lines(self, src, min_lines, min_chars):
        t_len = 0
        t_lines = 0
        for l in src:
            t_lines += 1
            t_len += len(l)

        self.assertGreaterEqual(t_len, min_chars)
        self.assertGreaterEqual(t_lines, min_lines)

    @abstractmethod
    def make_requests(self):
        """
        Override this
        """
        pass

    def test_web_state(self):
        """
        Metrics should be reported in web state
        """
        try:
            push_state('web')
            self.make_requests()
        finally:
            pop_state('web')

        self.assertEqual(self.reporter.counts, self.expected_web_state_counts)
        self.assertItemsEqual(self.reporter.records.keys(), self.expected_web_state_gauges)

    def test_model_state(self):
        """
        Metrics shouldn't get reported in web state if also in model state
        """
        try:
            push_state('web')
            push_state('model')
            self.make_requests()
        finally:
            pop_state('model')
            pop_state('web')

        self.assertFalse(self.reporter.counts)
        self.assertFalse(self.reporter.records)

    def test_requests_nostate(self):
        """
        Metrics shouldn't get reported with no state
        """
        self.make_requests()

        self.assertFalse(self.reporter.counts)
        self.assertFalse(self.reporter.records)
