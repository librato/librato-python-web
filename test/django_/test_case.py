
import os
import django
from django.test import SimpleTestCase as TestCase

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

    def verify_counters(self, expected_counters):
        self.assertItemsEqual(self.reporter.get_counter_names(), expected_counters.keys())
        for k, v in expected_counters.iteritems():
            self.assertEqual(self.reporter.get_counter_value(k), v)
