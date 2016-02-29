from librato_python_web.instrumentor.instrument import contextmanager_wrapper_factory
from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor
from librato_python_web.instrumentor.telemetry import increment_count


class LoggingInstrumentor(BaseInstrumentor):
    modules = {'logging': ['Logger']}

    def __init__(self):
        super(LoggingInstrumentor, self).__init__(
            {
                'logging.Logger.critical': contextmanager_wrapper_factory(increment_count('logging.critical.')),
                'logging.Logger.exception': contextmanager_wrapper_factory(increment_count('logging.exception.')),
                'logging.Logger.error': contextmanager_wrapper_factory(increment_count('logging.error.')),
                'logging.Logger.warning': contextmanager_wrapper_factory(increment_count('logging.warning.')),
            }
        )

    def run(self):
        super(LoggingInstrumentor, self).run()
