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


from os import environ
import psycopg2
import unittest

from librato_python_web.instrumentor.data.psycopg2 import Psycopg2Instrumentor
from datatest_base import BaseDataTest

Psycopg2Instrumentor().run()


class Psycopg2Test(BaseDataTest, unittest.TestCase):
    expected_web_state_counts = {'data.psycopg2.execute.requests': 5, 'data.psycopg2.callproc.requests': 2}
    expected_web_state_gauges = ['data.psycopg2.callproc.latency', 'data.psycopg2.execute.latency']

    def run_queries(self):
        # connect (params impl dependent) dsn data source name, host hostname, database db name
        dbname = environ.get('POSTGRES_TEST_DB', 'test')
        dbuser = environ.get('POSTGRES_TEST_USER', 'postgres')
        conn = psycopg2.connect(host="localhost", dbname=dbname, user=dbuser)

        #
        # apilevel
        # paramstyle?
        # Exception logging (see types: https://www.python.org/dev/peps/pep-0249/#exceptions)

        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.execute("select * from pg_catalog.pg_user")
        cur.execute("select * from pg_catalog.pg_roles")

        try:
            cur.execute("drop function usercount()")
        except:
            # proc might not exist
            conn.rollback()

        cur.execute('''create function usercount() returns integer as $$
                    declare
                       result integer;
                    begin
                    select count(*) from pg_catalog.pg_user into result;
                    return result;
                    end;
                    $$ LANGUAGE plpgsql''')
        cur.callproc("usercount", ())

        cur.close()		# To avert an out of sync error
        cur = conn.cursor()

        cur.callproc("usercount", ())

        cur.close()
        conn.commit()

if __name__ == '__main__':
    unittest.main()
