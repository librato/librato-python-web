from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor, default_context_wrapper_factory


class PykafkaInstrumentor(BaseInstrumentor):
    modules = {'pykafka': ['Producer'], 'pykafka.simpleconsumer': ['SimpleConsumer']}

    def __init__(self):
        super(PykafkaInstrumentor, self).__init__()
        self.set_wrapped(
            {
                # Kafka (pykafka)
                'pykafka.simpleconsumer.SimpleConsumer.consume':
                    default_context_wrapper_factory('messaging.kafka.consume.',
                                                    mapping={'resource': 'self._topic._name'},
                                                    state='messaging.kafka', disable_if='model'),
                'pykafka.Producer.produce':
                    default_context_wrapper_factory('messaging.kafka.produce.',
                                                    mapping={'resource': 'self._topic._name'},
                                                    state='messaging.kafka', disable_if='model'),
            }
        )

    def run(self):
        super(PykafkaInstrumentor, self).run()
