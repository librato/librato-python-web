from librato_python_web.instrumentor.instrument import context_function_wrapper_factory
from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor
from librato_python_web.instrumentor.telemetry import default_instrumentation


class MysqlInstrumentor(BaseInstrumentor):
    required_class_names = ['MySQLdb']

    def __init__(self):
        super(MysqlInstrumentor, self).__init__(
            {
                'MySQLdb.cursors.Cursor.execute': context_function_wrapper_factory(
                    default_instrumentation('data.mysql.execute.'),
                    prefix='resource',
                    keys=[1],
                    disable_if='model',
                    state='data.mysql'
                ),
            }
        )

    def run(self):
        super(MysqlInstrumentor, self).run()
