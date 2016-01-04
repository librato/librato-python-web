
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
