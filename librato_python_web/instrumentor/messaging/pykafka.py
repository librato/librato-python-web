from librato_python_web.instrumentor.instrument import context_function_wrapper_factory
from librato_python_web.instrumentor.instrumentor import BaseInstrumentor
from librato_python_web.instrumentor.telemetry import default_instrumentation


class PykafkaInstrumentor(BaseInstrumentor):
    required_class_names = ['pykafka']

    def __init__(self):
        super(PykafkaInstrumentor, self).__init__(
            {
                # Kafka (pykafka)
                'pykafka.simpleconsumer.SimpleConsumer.consume': context_function_wrapper_factory(
                    default_instrumentation('messaging.kafka.consume.'),
                    prefix='resource',
                    keys=['self._topic._name']),
                'pykafka.Producer.produce': context_function_wrapper_factory(
                    default_instrumentation('messaging.kafka.produce.'),
                    prefix='resource',
                    keys=['self._topic._name']),
            }
        )

    def run(self):
        super(PykafkaInstrumentor, self).run()
