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


from datetime import datetime
import unittest

from librato_python_web.instrumentor.data.elasticsearch import ElasticsearchInstrumentor
from datatest_base import BaseDataTest

from elasticsearch import Elasticsearch

ElasticsearchInstrumentor().run()
es = Elasticsearch()


class ElasticsearchTest(BaseDataTest, unittest.TestCase):
    expected_web_state_counts = {'data.es.get.requests': 1,
                                 'data.es.index.requests': 1,
                                 'data.es.search.requests': 1}
    expected_web_state_gauges = ['data.es.get.latency', 'data.es.index.latency', 'data.es.search.latency']

    def run_queries(self):
        """
        Elasticsearch queries
        """

        doc = {
            'author': 'kimchy',
            'text': 'Elasticsearch: cool. bonsai cool.',
            'timestamp': datetime.now(),
        }
        res = es.index(index="test-index", doc_type='tweet', id=1, body=doc)
        print(res['created'])

        res = es.get(index="test-index", doc_type='tweet', id=1)
        print(res['_source'])

        es.indices.refresh(index="test-index")

        res = es.search(index="test-index", body={"query": {"match_all": {}}})


if __name__ == '__main__':
    unittest.main()
