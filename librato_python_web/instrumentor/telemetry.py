from contextlib import contextmanager
from collections import defaultdict

from librato_python_web.statsd.client import statsd_client
from librato_python_web.instrumentor.custom_logging import getCustomLogger

logger = getCustomLogger(__name__)


# noinspection PyClassHasNoInit
class _global:
    reporters = {}


def set_reporter(reporter, name='web'):
    """
    Sets the reporter for configuration information.

    Defaults to StdoutConfigReporter.

    :param reporter: the reporter instance
    :type reporter: TelemetryReporter
    """
    _global.reporters[name] = reporter


def count(metric, incr=1, reporter='web'):
    """
    Increment the count for the given metric by the given increment.
    Example
        telemetry.count('requests')
        telemetry.count('bytesReceived', len(request.content))

    :param metric: the given metric name
    :param incr: the value by which it is incremented
    """
    return _global.reporters[reporter].count(metric, incr)


def record(metric, value, is_timer=True, reporter='web'):
    """
    Records a given value as a data point for the given metric at the current timestamp.

    The current of the context stack is included.

    Example
        telemetry.record('maxHeap', max_heap_size)

    :param metric: the given metric name
    :param value: the value to be recorded
    """
    return _global.reporters[reporter].record(metric, value, is_timer)


def event(event_type, dictionary=None, reporter='web'):
    """
    Reports an event of a given type.

    dict provides optional additional values. Valid dictionary values include:
    * id: unique identifier for this event (defaults to generated UUID4 string)
    * message: descriptive string value (optional)

    Example
        telemetry.event('new-account', {
            'id':'a039fdf8-66e4-4ac9-8d83-51179d395984',
            'message': 'Created new user account',
            'user': 'test@example.com',
            'account': '437fbd24-5dd3-45f1-9fb3-c86db5283c8d'

        })
    :param event_type: descriptor for event type
    :param dictionary: additional values for event
    """
    _global.reporters[reporter].event(event_type, dictionary)


def record_telemetry(type_name, elapsed, reporter='web'):
    count(type_name + 'requests', reporter=reporter)
    record(type_name + 'latency', elapsed, reporter=reporter)


def generate_record_telemetry(type_name, reporter='web'):
    return lambda elapsed: record_telemetry(type_name, elapsed, reporter)


def increment_count(type_name='resource', reporter='web'):
    @contextmanager
    def wrapper_func(*args, **keywords):
        count(type_name + 'requests', reporter=reporter)
        yield

    return wrapper_func


class TelemetryReporter(object):
    def __init__(self):
        super(TelemetryReporter, self).__init__()

    def count(self, metric, incr=1):
        pass

    def record(self, metric, value):
        pass

    def event(self, type_name, dictionary=None):
        pass


class TestTelemetryReporter(TelemetryReporter):
    """
    Gathers metrics to allow verification
    """
    def __init__(self):
        super(TestTelemetryReporter, self).__init__()
        self.counts = defaultdict(int)
        self.records = {}

    def reset(self):
        self.counts = defaultdict(int)
        self.records = {}

    def count(self, metric, incr=1):
        self.counts[metric] += incr

    def get_count(self, metric):
        return self.counts[metric]

    def record(self, metric, value, is_timer=True):
        self.records[metric] = value

    def get_record(self, metric):
        return self.records.get(metric)

    def event(self, type_name, dictionary=None):
        pass

    def get_counter_names(self):
        return self.counts.keys()

    def get_counter_value(self, metric):
        return self.counts[metric] if metric in self.counts else None

    def get_gauge_names(self):
        return self.records.keys()

    def get_gauge_value(self, metric):
        return self.records[metric] if metric in self.records else None


class StdoutTelemetryReporter(TelemetryReporter):
    def __init__(self):
        super(StdoutTelemetryReporter, self).__init__()

    def count(self, metric, incr=1):
        print(metric, incr)

    def record(self, metric, value, is_timer=True):
        print(metric, value)

    def event(self, type_name, dictionary=None):
        print(type_name, dictionary)


class StatsdTelemetryReporter(TelemetryReporter):
    def __init__(self, port=8142, prefix=None):
        super(StatsdTelemetryReporter, self).__init__()
        self.client = statsd_client.Client(port=port, prefix=prefix)
        self.prefix = prefix

    def count(self, metric, incr=1):
        self.client.increment(metric, incr)

    def record(self, metric, value, is_timer=True):
        if is_timer:
            self.client.timing(metric, value * 1000)
        else:
            self.client.gauge(metric, value)

    def event(self, type_name, dictionary=None):
        # TBD: Not implemented
        pass

    def _register_alias(self, alias, value):
        logger.debug("registering alias %s->%s", alias, value)
        self.client.define_alias(alias, value)


set_reporter(StdoutTelemetryReporter())
