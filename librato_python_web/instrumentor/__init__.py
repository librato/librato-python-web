# Copyright (c) 2015. Librato, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Librato, Inc. nor the names of project contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL LIBRATO, INC. BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


# Top-level module names and the corresponding proxies
import os

from . import general
from . import telemetry
from . import config
from .config import LegacyConfigReporter
from instrumentor.data.psycopg2 import Psycopg2Instrumentor
from instrumentor.data.sqlite import SqliteInstrumentor
from .telemetry import StatsdTelemetryReporter
from .data.elasticsearch import ElasticsearchInstrumentor
from .data.mysqldb import MysqlInstrumentor
from . import custom_logging
from .external.requests_ import RequestsInstrumentor
from .external.urllib2_ import Urllib2Instrumentor
from .log.logging import LoggingInstrumentor
from .messaging.pykafka import PykafkaInstrumentor
from .web.django_ import DjangoInstrumentor
from .web.flask_ import FlaskInstrumentor
from .instrument import run_instrumentors, instrument_methods

logger = custom_logging.getCustomLogger(__name__)

try:
    _wrapped = {
    }

    _default_libs = '*'
    _instrumentors = {
        'django': DjangoInstrumentor,
        'elasticsearch': ElasticsearchInstrumentor,
        'flask': FlaskInstrumentor,
        'logging': LoggingInstrumentor,
        'mysql': MysqlInstrumentor,
        'sqlite': SqliteInstrumentor,
        'psycopg2': Psycopg2Instrumentor,
        'pykafka': PykafkaInstrumentor,
        'requests': RequestsInstrumentor,
        'urllib2': Urllib2Instrumentor,
    }
    _web_fxes = ['django', 'flask']

    general.set_option('enabled', os.environ.get('LIBRATO_INSTRUMENT_PYTHON'))
    if general.get_option('enabled'):
        config_file = './agent-conf.json'
        if os.path.isfile(config_file):
            general.configure(config_file)
        else:
            logger.info("Can't load configuration file: %s", config_file)
            # sys.exit(1)

        log_level = general.get_option("instrumentor.log_level", 30)
        custom_logging.setDefaultLevel(int(log_level))

        if 'LIBRATO_INSTRUMENTATION_PORT' in os.environ:
            general.set_option('statsd.enabled', True)
            general.set_option('statsd.port', int(os.environ.get('LIBRATO_INSTRUMENTATION_PORT')))

        if general.get_option('statsd.enabled', False):
            logger.debug("Using Statsd reporter")
            telemetry.set_reporter(StatsdTelemetryReporter(general.get_option('statsd.port', 8142)))

        if general.get_option('config.enabled', False):
            logger.debug("Using legacy config reporter")
            config.config.set_reporter(LegacyConfigReporter())

        libs = general.get_option('libraries')
        logger.info("Specified libraries = %s", libs)

        integration = general.get_option('integration', 'django')
        logger.info("Integration = %s", integration)

        if not libs:
            # By default, let us exclude the other web frameworks
            # The user can pull in multiple frameworks by being explicit
            libs = [lib for lib in _instrumentors.keys() if lib not in _web_fxes or lib == integration]
        elif libs == '*':
            libs = _instrumentors.keys()
        logger.info("Computed libraries = %s", libs)

        instrument_methods(_wrapped)
        run_instrumentors(_instrumentors, libs)
except Exception:
    logger.exception("librato_python_web __init__ failure")
