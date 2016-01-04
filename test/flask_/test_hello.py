import unittest

from librato_python_web.instrumentor import telemetry
from librato_python_web.instrumentor.telemetry import TestTelemetryReporter

import hello_app


class HelloTestCase(unittest.TestCase):
    def setUp(self):
        hello_app.app.config['TESTING'] = True
        self.app = hello_app.app.test_client()

        self.reporter = TestTelemetryReporter()
        telemetry.set_reporter(self.reporter)

    def tearDown(self):
        telemetry.set_reporter(None)

    def test_simple(self):
        r = self.app.get('/')

        self.assertEqual(r.status_code, 200)
        self.assertTrue(self.reporter.counts)
        self.assertTrue(self.reporter.records)

        print self.reporter.counts
        print self.reporter.records

if __name__ == '__main__':
    unittest.main()
