from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor


class PykafkaInstrumentor(BaseInstrumentor):
    required_class_names = ['pykafka']

    def __init__(self):
        super(PykafkaInstrumentor, self).__init__(
            {
                # Kafka (pykafka)
                'pykafka.simpleconsumer.SimpleConsumer.consume': self.instrument('messaging.kafka.consume.',
                    mapping={'resource': 'self._topic._name'},
                ),
                'pykafka.Producer.produce': self.instrument('messaging.kafka.produce.',
                    mapping={'resource': 'self._topic._name'},
                ),
            }
        )

    def run(self):
        super(PykafkaInstrumentor, self).run()
