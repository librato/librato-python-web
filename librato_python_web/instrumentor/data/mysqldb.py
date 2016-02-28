from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor
from librato_python_web.instrumentor.instrument2 import get_complex_wrapper, instrument_methods_v2


class MysqlInstrumentor(BaseInstrumentor):
    modules = {
                  'MySQLdb.cursors': ['Cursor']
              }

    def __init__(self):
        super(MysqlInstrumentor, self).__init__()
        self.set_wrapped(
            {
                'MySQLdb.cursors.Cursor.execute':
                    get_complex_wrapper('data.mysql.execute.', state='data.mysql', disable_if='model'),
                'MySQLdb.cursors.Cursor.callproc':
                    get_complex_wrapper('data.mysql.callproc.', state='data.mysql', disable_if='model'),
            }
        )

    def run(self):
        instrument_methods_v2(
            {
                'MySQLdb.cursors.Cursor.execute':
                    get_complex_wrapper('data.mysql.execute.', state='data.mysql', disable_if='model'),
                'MySQLdb.cursors.Cursor.callproc':
                    get_complex_wrapper('data.mysql.callproc.', state='data.mysql', disable_if='model'),
            }
        )
