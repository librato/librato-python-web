import re
from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor


class Psycopg2Instrumentor(BaseInstrumentor):
    required_class_names = ['psycopg2']

    def __init__(self):
        super(Psycopg2Instrumentor, self).__init__()
        self.set_overridden(
            {
                # 'psycopg2': {
                #     'connect': {
                #         'returns': 'psycopg2.extensions.connection'
                #     }
                # },
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
                self.instrument('data.psycopg2.%s.' % func_name(m), mapping={a: 1 for a in func_args(m)},
                                state='data.postgres', disable_if='model')
            for m in 'callproc(resource),execute(resource),executemany(resource),fetchone,fetchmany,fetchall,'
                     'nextset'.split(',')
            }

        # def wrap_cursor(f):
        #     def decorator(*args, **keywords):
        #         print 'pre', f, args, keywords
        #         try:
        #             return f(*args, **keywords)
        #         finally:
        #             print 'post', f, args, keywords
        #     return decorator
        #
        # wrapped['psycopg2.extensions.connection.cursor'] = proxy_returned_instance(
        #     get_class_by_name('psycopg2.extensions.connection'), 'cursor', 'psycopg2.extensions.cursor', wrapped
        # )

        self.set_wrapped(
            wrapped
        )

    def run(self):
        super(Psycopg2Instrumentor, self).run()
