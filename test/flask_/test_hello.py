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

    def test_once(self):
        r = self.app.get('/')

        expected_gauge_metrics = ['app.response.latency', 'wsgi.response.latency', 'web.response.latency']
        self.assertEqual(r.status_code, 200)
        self.assertItemsEqual(self.reporter.get_gauge_names(), expected_gauge_metrics)
        self.assertGreater(self.reporter.get_gauge_value('wsgi.response.latency'),
                           self.reporter.get_gauge_value('web.response.latency'))

        self.assertEqual(self.reporter.counts, {'web.status.2xx': 1, 'web.requests': 1})

    def test_twice(self):
        r = self.app.get('/')
        r = self.app.get('/')

        expected_gauge_metrics = ['app.response.latency', 'wsgi.response.latency', 'web.response.latency']
        self.assertEqual(r.status_code, 200)
        self.assertItemsEqual(self.reporter.get_gauge_names(), expected_gauge_metrics)

        self.assertEqual(self.reporter.counts, {'web.status.2xx': 2, 'web.requests': 2})

    def test_redirect(self):
        # Excluding the trailing will redirect
        r = self.app.get('/dir')

        self.assertEqual(r.status_code, 301)

        expected_gauge_metrics = ['app.response.latency', 'wsgi.response.latency', 'web.response.latency']
        self.assertItemsEqual(self.reporter.get_gauge_names(), expected_gauge_metrics)
        self.assertEqual(self.reporter.counts, {'web.status.3xx': 1, 'web.requests': 1})

    def test_notfound(self):
        r = self.app.get('/notfound/')

        self.assertEqual(r.status_code, 404)
        self.assertIn("Verify this text!", r.data)

        expected_gauge_metrics = ['app.response.latency', 'wsgi.response.latency', 'web.response.latency']
        self.assertItemsEqual(self.reporter.get_gauge_names(), expected_gauge_metrics)
        self.assertEqual(self.reporter.counts, {'web.status.4xx': 1, 'web.requests': 1})

    def test_error(self):
        r = self.app.get('/error/')

        self.assertEqual(r.status_code, 505)

        expected_gauge_metrics = ['app.response.latency', 'wsgi.response.latency', 'web.response.latency']
        self.assertItemsEqual(self.reporter.get_gauge_names(), expected_gauge_metrics)

        self.assertEqual(self.reporter.counts, {'web.status.5xx': 1, 'web.requests': 1})


if __name__ == '__main__':
    unittest.main()
