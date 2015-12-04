from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor


class MysqlInstrumentor(BaseInstrumentor):
    required_class_names = ['MySQLdb']

    def __init__(self):
        super(MysqlInstrumentor, self).__init__()
        self.set_wrapped(
            {
                'MySQLdb.cursors.Cursor.execute':
                    self.instrument('data.mysql.execute.', mapping={'resource': 1},
                                    state='data.mysql', disable_if='model'),
                'MySQLdb.cursors.Cursor.callproc':
                    self.instrument('data.mysql.callproc.', mapping={'resource': 1},
                                    state='data.mysql', disable_if='model'),
            }
        )

    def run(self):
        super(MysqlInstrumentor, self).run()
