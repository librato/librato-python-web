import json
import unittest

from librato_python_web.instrumentor import telemetry
from librato_python_web.instrumentor.telemetry import TestTelemetryReporter

import state_app


class HelloTestCase(unittest.TestCase):
    def setUp(self):
        state_app.app.config['TESTING'] = True
        self.app = state_app.app.test_client()

        self.reporter = TestTelemetryReporter()
        telemetry.set_reporter(self.reporter)

    def tearDown(self):
        telemetry.set_reporter(None)

    def test_state(self):
        r = self.app.get('/')

        self.assertEqual(r.status_code, 200)

        states = json.loads(r.data)

        self.assertEqual(len(states), 2)
        self.assertIn('web', states)
        self.assertIn('wsgi', states)
        self.assertEquals(states['web'], 1)
        self.assertEquals(states['wsgi'], 1)

if __name__ == '__main__':
    unittest.main()
