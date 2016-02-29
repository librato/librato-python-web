from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor, default_context_wrapper_factory


class MysqlInstrumentor(BaseInstrumentor):
    modules = {
                  'MySQLdb.cursors': ['Cursor']
              }

    def __init__(self):
        super(MysqlInstrumentor, self).__init__()
        self.set_wrapped(
            {
                'MySQLdb.cursors.Cursor.execute':
                    default_context_wrapper_factory('data.mysql.execute.', mapping={'resource': 1},
                                                    state='data.mysql', disable_if='model'),
                'MySQLdb.cursors.Cursor.callproc':
                    default_context_wrapper_factory('data.mysql.callproc.', mapping={'resource': 1},
                                                    state='data.mysql', disable_if='model'),
            }
        )

    def run(self):
        super(MysqlInstrumentor, self).run()
