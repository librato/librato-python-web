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


import logging
import unittest

from librato_python_web.instrumentor import telemetry
from librato_python_web.instrumentor.telemetry import TestTelemetryReporter
from librato_python_web.instrumentor.log.logging import LoggingInstrumentor
from librato_python_web.instrumentor.context import push_state, pop_state

LoggingInstrumentor().run()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class LoggingTest(unittest.TestCase):
    expected_counts = {
        'logging.exception.requests': 1,
        'logging.error.requests': 2,    # Exception counts as an error as well
        'logging.warning.requests': 1,
        'logging.critical.requests': 2,
    }

    def setUp(self):
        self.reporter = TestTelemetryReporter()
        telemetry.set_reporter(self.reporter)

    def tearDown(self):
        telemetry.set_reporter(None)

    def test_web_state(self):
        """
        Metrics should get reported in web state
        """
        try:
            push_state('web')

            logger.debug("This is a dummy debug message")

            logger.info("Logging test is running")
            logger.info("Here is another info message for the books")

            logger.warning("Ignore this dummy warning message")

            logger.error("Ignore this dummy error message as well")

            logger.critical("Ignore this dummy critical message")
            logger.critical("Ignore this dummy critical message as well")

            try:
                raise Exception("This is a dummy exception not a test failure")
            except:
                logger.exception("Dummy exception:")

            self.assertEqual(self.reporter.counts, self.expected_counts)
            self.assertFalse(self.reporter.records)
        except Exception as e:
            logger.exception("test_web_state")
        finally:
            pop_state('web')

    def test_nostate(self):
        """
        Metrics shouldn't get reported outside a web state
        """
        logger.info("This info message shouldn't get counted")

        self.assertFalse(self.reporter.counts)
        self.assertFalse(self.reporter.records)

if __name__ == '__main__':
    unittest.main()
