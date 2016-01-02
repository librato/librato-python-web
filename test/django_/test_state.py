
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

    def test_state(self):
        r = self.client.get('/state/')

        self.assertEqual(r.status_code, 200)
        states = r.json()

        self.assertEqual(len(states), 1)
        self.assertIn('web', states)
        self.assertEquals(states['web'], 1)

if __name__ == '__main__':
    unittest.main()
