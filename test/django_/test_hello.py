
import os
import unittest
import django
from django.test import SimpleTestCase as TestCase

from librato_python_web.instrumentor import telemetry
from test_reporter import TestTelemetryReporter

os.environ['DJANGO_SETTINGS_MODULE'] = 'test_site.settings'
django.setup()


class HelloTests(TestCase):
    def setUp(self):
        self.reporter = TestTelemetryReporter()
        telemetry.set_reporter(self.reporter)

    def tearDown(self):
        telemetry.set_reporter(None)

    def test_metrics_reported(self):
        r = self.client.get('/hello/')

        self.assertEqual(r.status_code, 200)
        self.assertTrue(self.reporter.counts)
        self.assertTrue(self.reporter.records)

        print self.reporter.counts
        print self.reporter.records

if __name__ == '__main__':
    unittest.main()
