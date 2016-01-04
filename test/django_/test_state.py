
import unittest
from test_case import DjangoTestCase


class StateTests(DjangoTestCase):
    def test_state(self):
        r = self.client.get('/state/')

        self.assertEqual(r.status_code, 200)
        states = r.json()

        self.assertEqual(len(states), 1)
        self.assertIn('web', states)
        self.assertEquals(states['web'], 1)

if __name__ == '__main__':
    unittest.main()
