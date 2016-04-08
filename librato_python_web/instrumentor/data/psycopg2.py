import re

from librato_python_web.instrumentor.instrument import wrap_returned_instance_decorator
from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor, default_context_wrapper_factory


class Psycopg2Instrumentor(BaseInstrumentor):
    modules = {'psycopg2': ['connect'], 'psycopg2.extensions': ['connection', 'cursor']}

    def __init__(self):
        super(Psycopg2Instrumentor, self).__init__()
        self.major_versions = [2]

    def run(self):
        self.set_overridden(
            {
                'psycopg2': {
                    'connect': {
                        'returns': 'psycopg2.extensions.connection'
                    }
                },
                'psycopg2.extensions.connection': {
                    'cursor': {
                        'returns': 'psycopg2.extensions.cursor'
                    }
                },
            }
        )

        cursor_path = 'psycopg2.extensions.cursor.%s'

        def func_name(e):
            return e.split('(')[0]

        def func_args(e):
            return re.findall('[^(,)]+', e)[1:]

        wrapped = {
            cursor_path % func_name(m):
                default_context_wrapper_factory('data.psycopg2.%s.' % func_name(m),
                                                mapping={a: 1 for a in func_args(m)},
                                                state='data.postgres', disable_if='model')
            for m in 'callproc(resource),execute(resource),executemany(resource),fetchone,fetchmany,fetchall,'
                     'nextset'.split(',')
            }

        wrapped['psycopg2.extensions.connection.cursor'] = wrap_returned_instance_decorator(
            'psycopg2.extensions.cursor', wrapped
        )

        self.set_wrapped(
            wrapped
        )

        super(Psycopg2Instrumentor, self).run()
