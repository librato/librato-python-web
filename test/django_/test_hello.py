
import os
import unittest
import django
from django.test import SimpleTestCase as TestCase

os.environ['DJANGO_SETTINGS_MODULE'] = 'test_site.settings'
django.setup()


class HelloTests(TestCase):
    def test_state(self):
        r = self.client.get('/hello/')

        self.assertEqual(r.status_code, 200)

if __name__ == '__main__':
    unittest.main()
