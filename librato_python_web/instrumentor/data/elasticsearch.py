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


from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor
from librato_python_web.instrumentor.instrument import get_complex_wrapper


class ElasticsearchInstrumentor(BaseInstrumentor):
    modules = {
        'elasticsearch.client': ['Elasticsearch']
    }

    def __init__(self):
        super(ElasticsearchInstrumentor, self).__init__()

    def run(self):
        self.set_wrapped(
            {
                'elasticsearch.client.Elasticsearch.create':
                    get_complex_wrapper('data.es.create.', state='data.elasticsearch', disable_if='model'),
                'elasticsearch.client.Elasticsearch.get':
                    get_complex_wrapper('data.es.get.', state='data.elasticsearch', disable_if='model'),
                'elasticsearch.client.Elasticsearch.index':
                    get_complex_wrapper('data.es.index.', state='data.elasticsearch', disable_if='model'),
                'elasticsearch.client.Elasticsearch.search':
                    get_complex_wrapper('data.es.search.', state='data.elasticsearch', disable_if='model'),
                'elasticsearch.client.Elasticsearch.delete':
                    get_complex_wrapper('data.es.delete.', state='data.elasticsearch', disable_if='model'),
            }
        )

        super(ElasticsearchInstrumentor, self).run()
