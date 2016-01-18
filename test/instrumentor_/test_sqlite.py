# Copyright (c) 2015. Librato, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Librato, Inc. nor the names of project contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL LIBRATO, INC. BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from datatest_base import BaseDataTest
import unittest
import sqlite3

from librato_python_web.instrumentor.data.sqlite import SqliteInstrumentor

SqliteInstrumentor().run()


class SqliteTest(BaseDataTest, unittest.TestCase):
    expected_web_state_counts = {
        'data.sqlite.executemany.requests': 1,
        'data.sqlite.fetchone.requests': 1,
        'data.sqlite.execute.requests': 4
    }
    expected_web_state_gauges = [
        'data.sqlite.executemany.latency',
        'data.sqlite.fetchone.latency',
        'data.sqlite.execute.latency',
    ]

    def run_queries(self):
        # connect to in-memory
        conn = sqlite3.connect(":memory:")

        cur = conn.cursor()
        cur.execute("SELECT 1")

        # from Python docs (https://docs.python.org/2/library/sqlite3.html)
        # Create table
        cur.execute('''CREATE TABLE stocks
                     (date TEXT, trans TEXT, symbol TEXT, qty REAL, price REAL)''')

        # Insert a row of data
        cur.execute("INSERT INTO stocks VALUES ('2006-01-05','BUY','RHAT',100,35.14)")

        # Save (commit) the changes
        conn.commit()

        t = ('RHAT',)
        cur.execute('SELECT * FROM stocks WHERE symbol=?', t)
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEquals(('2006-01-05', 'BUY', 'RHAT', 100, 35.14), row)

        # Larger example that inserts many records at a time
        purchases = [('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
                     ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
                     ('2006-04-06', 'SELL', 'IBM', 500, 53.00),
                     ]
        cur.executemany('INSERT INTO stocks VALUES (?,?,?,?,?)', purchases)
        # Save (commit) the changes
        conn.commit()

        last_price = 0
        for row in conn.execute('SELECT * FROM stocks ORDER BY price'):
            self.assertIsNotNone(row)
            self.assertLessEqual(last_price, row[-1])
            last_price = row[-1]

        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
        conn.close()


if __name__ == '__main__':
    unittest.main()
