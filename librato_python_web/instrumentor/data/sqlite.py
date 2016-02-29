import re
from librato_python_web.instrumentor.instrument import wrap_returned_instance_decorator
from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor, default_context_wrapper_factory


class SqliteInstrumentor(BaseInstrumentor):
    modules = {'sqlite3': []}

    def __init__(self):
        super(SqliteInstrumentor, self).__init__()
        self.major_versions = [2]

    def run(self):
        self.set_overridden(
            {
                'sqlite3': {
                    'connect': {
                        'returns': 'sqlite3.Connection'
                    }
                },
                'sqlite3.Connection': {
                    'cursor': {
                        'returns': 'sqlite3.Cursor'
                    }
                }
            }
        )

        cursor_path = 'sqlite3.Cursor.%s'

        def func_name(e):
            return e.split('(')[0]

        def func_args(e):
            return re.findall('[^(,)]+', e)[1:]

        wrapped = {cursor_path % func_name(m): default_context_wrapper_factory('data.sqlite.%s.' % func_name(m),
                                                                               mapping={a: 1 for a in func_args(m)},
                                                                               state='data.sqlite',
                                                                               disable_if='model') for m in
                   'execute(resource),executemany(resource),fetchone,fetchmany,fetchall'.split(',')}

        wrapped['sqlite3.Connection.cursor'] = wrap_returned_instance_decorator(
            'sqlite3.Cursor', wrapped
        )

        self.set_wrapped(
            wrapped
        )

        super(SqliteInstrumentor, self).run()
