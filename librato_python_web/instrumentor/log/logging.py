from librato_python_web.instrumentor.instrument import context_function_wrapper_factory
from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor
from librato_python_web.instrumentor.telemetry import increment_count


class LoggingInstrumentor(BaseInstrumentor):
    required_class_names = ['logging.Logger']

    def __init__(self):
        super(LoggingInstrumentor, self).__init__(
            {
                'logging.Logger.critical': context_function_wrapper_factory(increment_count('logging.critical.')),
                'logging.Logger.exception': context_function_wrapper_factory(increment_count('logging.exception.')),
                'logging.Logger.error': context_function_wrapper_factory(increment_count('logging.error.')),
                'logging.Logger.warning': context_function_wrapper_factory(increment_count('logging.warning.')),
            }
        )

    def run(self):
        super(LoggingInstrumentor, self).run()
