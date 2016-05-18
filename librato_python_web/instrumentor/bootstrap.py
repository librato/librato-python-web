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
from six.moves import builtins

from . import general
from . import telemetry
from .telemetry import StatsdTelemetryReporter
from .data.psycopg2 import Psycopg2Instrumentor
from .data.sqlite import SqliteInstrumentor
from .data.elasticsearch import ElasticsearchInstrumentor
from .data.mysqldb import MysqlInstrumentor
from . import custom_logging
from .external.requests_ import RequestsInstrumentor
from .external.urllib_ import Urllib2Instrumentor, UrllibInstrumentor
from .log.logging import LoggingInstrumentor
from .messaging.pykafka import PykafkaInstrumentor
from .web.django_ import DjangoCoreInstrumentor, DjangoConfInstrumentor, DjangoDbInstrumentor
from .web.flask_ import FlaskInstrumentor
from .web.cherrypy_ import CherryPyInstrumentor
from .web.gunicorn_ import GunicornInstrumentor

logger = custom_logging.getCustomLogger(__name__)


# Maps a library name to its corresponding instrumentor classes
# An instrumentor handles one or more related modules
_instrumentors = {
    'django': [DjangoCoreInstrumentor, DjangoConfInstrumentor, DjangoDbInstrumentor],
    'elasticsearch': [ElasticsearchInstrumentor],
    'flask': [FlaskInstrumentor],
    'logging': [LoggingInstrumentor],
    'mysql': [MysqlInstrumentor],
    'sqlite': [SqliteInstrumentor],
    'psycopg2': [Psycopg2Instrumentor],
    'pykafka': [PykafkaInstrumentor],
    'requests': [RequestsInstrumentor],
    'urllib': [UrllibInstrumentor],
    'urllib2': [Urllib2Instrumentor],
    'cherrypy': [CherryPyInstrumentor],
    'gunicorn': [GunicornInstrumentor],
}
_web_fxes = ['django', 'flask', 'cherrypy']


class _globals:
    bootstrapped = False
    targeted_modules = {}    # Lets the custom loader find the instrumentor for a targeted module
    instrumented_modules = set()
    builtin_importer = None


def init(config_path=None):
    try:
        if _globals.bootstrapped:
            return
        _globals.bootstrapped = True

        if not config_path:
            config_path = os.environ.get('LIBRATO_CONFIG_PATH', "./agent-conf.json")

        if os.path.isfile(config_path):
            general.configure(config_path)
        else:
            logger.info("Can't load configuration file: %s", config_path)
            # sys.exit(1)

        if 'LIBRATO_INSTRUMENTATION_LOG_LEVEL' in os.environ:
            general.set_option('instrumentor.log_level', os.environ.get('LIBRATO_INSTRUMENTATION_LOG_LEVEL'))

        log_level = general.get_option("instrumentor.log_level", 30)
        custom_logging.setDefaultLevel(int(log_level))

        if 'LIBRATO_INSTRUMENTATION_PORT' in os.environ:
            general.set_option('statsd.enabled', True)
            general.set_option('statsd.port', int(os.environ.get('LIBRATO_INSTRUMENTATION_PORT')))

        if 'LIBRATO_INTEGRATION' in os.environ:
            general.set_option('integration', os.environ.get('LIBRATO_INTEGRATION'))

        if 'LIBRATO_INSTRUMENTATION_LIBS' in os.environ:
            libs = os.environ.get('LIBRATO_INSTRUMENTATION_LIBS').split()
            general.set_option('libraries', libs)

        set_instrumentors()
        set_importer()
        set_reporter()    # TBD: This binds the reporter to the baked-in UDP module and needs further review
    except:
        logger.exception("Error initializing instrumentation")


def set_instrumentors():
    """ Populates the targeted_modules dict, which is required by the custom loader """
    integration = general.get_option('integration', 'django')
    logger.info("Integration = %s", integration)

    libs = general.get_option('libraries')
    logger.info("Specified libraries = %s", libs)

    if not libs:
        # By default, let us exclude the other web frameworks
        # The user can pull in multiple frameworks by being explicit
        libs = [lib for lib in _instrumentors.keys() if lib not in _web_fxes or lib == integration]
    elif libs == '*':
        libs = _instrumentors.keys()
    logger.info("Computed libraries = %s", libs)

    for alias in _instrumentors:
        if alias not in libs:
            logger.info("Skipping %s", alias)
            continue

        for instrumentor_class in _instrumentors[alias]:
            instrumentor = instrumentor_class()
            for mod_ in instrumentor.modules:
                _globals.targeted_modules[mod_] = instrumentor


def set_reporter():
    if general.get_option('statsd.enabled', False):
        logger.debug("Using Statsd reporter")
        statsd_port = general.get_option('statsd.port', 8142)
        integration = general.get_option('integration')
        telemetry.set_reporter(StatsdTelemetryReporter(statsd_port, prefix=integration))
        telemetry.set_reporter(StatsdTelemetryReporter(statsd_port), name='gunicorn')


def set_importer():
    _globals.builtin_importer = builtins.__import__
    builtins.__import__ = import2    # Substitute built-in import function with our own


def import2(*args, **kwargs):
    """ Our import function which instruments the modules we care about """

    mod_ = _globals.builtin_importer(*args, **kwargs)
    name = mod_.__name__

    if name in _globals.targeted_modules and name not in _globals.instrumented_modules:
        # We care about this module and it hasn't already been instrumented

        logger.debug("Request to load module %s", name)
        instrumentor = _globals.targeted_modules[name]

        # Don't proceed till required attributes are present
        # Recursion in the module loading process can result in partially loaded modules
        if not instrumentor.can_run():
            return mod_

        # Check off all the modules this instrumentor handles
        _globals.instrumented_modules.update(instrumentor.modules.keys())

        try:
            logger.info("Instrumenting %s", name)
            instrumentor.run()
        except:
            logger.exception("Error instrumenting %s", name)

    return mod_
