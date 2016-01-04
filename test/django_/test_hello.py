
import unittest
from test_case import DjangoTestCase


class HelloTests(DjangoTestCase):
    def test_once(self):
        r = self.client.get('/hello/')

        expected_gauge_metrics = ['app.response.latency', 'web.view.latency', 'web.response.latency']
        self.assertEqual(r.status_code, 200)
        self.assertItemsEqual(self.reporter.get_gauge_names(), expected_gauge_metrics)

        self.assertEqual(self.reporter.counts, {'web.status.2xx': 1, 'web.requests': 1})

    def test_twice(self):
        r = self.client.get('/hello/')
        self.assertEqual(r.status_code, 200)

        r = self.client.get('/hello/')
        self.assertEqual(r.status_code, 200)

        expected_gauge_metrics = ['app.response.latency', 'web.view.latency', 'web.response.latency']
        self.assertItemsEqual(self.reporter.get_gauge_names(), expected_gauge_metrics)
        self.assertEqual(self.reporter.counts, {'web.status.2xx': 2, 'web.requests': 2})

    def test_redirect(self):
        # Excluding the trailing will redirect
        r = self.client.get('/hello')

        self.assertEqual(r.status_code, 301)

        expected_gauge_metrics = ['app.response.latency', 'web.response.latency']
        self.assertItemsEqual(self.reporter.get_gauge_names(), expected_gauge_metrics)

        self.assertEqual(self.reporter.counts,
                         {'web.status.3xx': 1, 'web.requests': 1, 'logging.warning.requests': 1})

    def test_notfound(self):
        r = self.client.get('/hello/notfound/')

        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.content, "Verify this text!")

        expected_gauge_metrics = ['app.response.latency', 'web.view.latency', 'web.response.latency']
        self.assertItemsEqual(self.reporter.get_gauge_names(), expected_gauge_metrics)
        self.assertEqual(self.reporter.counts, {'web.status.4xx': 1, 'web.requests': 1})

    def test_error(self):
        r = self.client.get('/hello/error/')

        self.assertEqual(r.status_code, 500)

        expected_gauge_metrics = ['app.response.latency', 'web.view.latency', 'web.response.latency']
        self.assertItemsEqual(self.reporter.get_gauge_names(), expected_gauge_metrics)

        self.assertEqual(self.reporter.counts, {'web.status.5xx': 1, 'web.requests': 1})

    def test_exception(self):
        r = self.client.get('/hello/error/')

        self.assertEqual(r.status_code, 500)

        expected_gauge_metrics = ['app.response.latency', 'web.view.latency', 'web.response.latency']
        self.assertItemsEqual(self.reporter.get_gauge_names(), expected_gauge_metrics)

        self.assertEqual(self.reporter.counts, {'web.status.5xx': 1, 'web.requests': 1})


if __name__ == '__main__':
    unittest.main()
