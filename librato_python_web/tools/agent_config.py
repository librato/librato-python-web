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


import logging
import json
import os
import sys
import argparse

LIBRATO_HOSTNAME = "metrics-api.librato.com"

logger = logging.getLogger(__name__)

python_agent_conf = './agent-conf.json'
config_options = [
    'daemonize',
    'debug',
    'create',
    'expire',
    'flush_interval',
    'hostname',
    'user',
    'api_token',
    'metrics_hostname',
    'no_aggregate_counters',
    'pct',
    'pidfile',
    'port',
    'app_id',
    'restart',
    'stop',
    'integration'
]
required_options = [
    ('user', 'Librato user email'),
    ('api_token', 'Librato api token'),
    ('app_id', 'Unique ID for application'),
    ('integration', 'Librato integration (django, flask)'),
    ('metrics_hostname', 'Librato metrics API URL')
]
defaults = {
    "daemonize": False,
    "debug": False,
    "create": False,
    "expire": 0,
    "hostname": "localhost",
    "pidfile": '/var/run/solarwinds-python-statsd.pid',
    "port": 8142,
    "pct": 95,
    "flush_interval": 60000,
    'no_aggregate_counters': False,
    'metrics_hostname': LIBRATO_HOSTNAME,
    'integration': 'django'
}


class _globals(object):
    config_path = "./agent-conf.json"


class config_info(object):
    pass


def load_config(args=sys.argv[1:], use_env=True):
    """ Load configuration with the following priority """
    """ a. Command line params """
    """ b. Configuration file """
    """ c. Baked in defaults, where appropriate """
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', help='debug mode')
    parser.add_argument('--config-path', help='configuration file path (default: {})'.format(python_agent_conf),
                        default=python_agent_conf)
    parser.add_argument('-c', '--create', help='create librato space (default: false)')
    parser.add_argument('-H', '--hostname', help='hostname to run on (default: localhost')
    parser.add_argument('-p', '--port', help='port to run on (default: 8142)', type=int)
    parser.add_argument('-u', '--user', dest='user', help='librato user email')
    parser.add_argument('--api-token', dest='api_token', help='librato api token')
    parser.add_argument('--flush-interval',
                        help='how often to send data to librato in milli-seconds (default: 60000)', type=int)
    parser.add_argument('--no-aggregate-counters',
                        help='should statsd report counters as absolute instead of count/sec', action='store_true')
    parser.add_argument('-t', '--pct', help='stats pct threshold (default: 95)', type=int)
    parser.add_argument('-D', '--daemon', dest='daemonize', action='store_true', help='daemonize')
    parser.add_argument('--pidfile', help='pid file')
    parser.add_argument('--restart', action='store_true', help='restart a running daemon')
    parser.add_argument('--stop', action='store_true', help='stop a running daemon')
    parser.add_argument('--expire', help='time-to-live for old stats (in secs)', type=int)
    parser.add_argument('--app-id', help='unique id for application')
    parser.add_argument('-M', '--metrics-hostname', help='Librato metrics API URL')
    parser.add_argument('-I', '--integration', help='Librato Python integration (django, flask or cherrypy)')

    options = parser.parse_args(args)
    _globals.config_path = options.config_path

    # Drop the null values argparse supplies
    new_options = config_info()
    for f in config_options:
        if hasattr(options, f):
            val = getattr(options, f)
            if val is not None:
                setattr(new_options, f, val)
    options = new_options

    if use_env:
        update_config_from_env(options)
    update_config_from_config_file(options)

    # Use baked in defaults
    for key in defaults:
        if not hasattr(options, key):
            setattr(options, key, defaults.get(key))

    setattr(options, 'integration', getattr(options, 'integration', 'django').lower())
    return options


def update_config_from_env(options=None):
    options = options or config_info()

    for attr, var in [("user", "LIBRATO_USER"), ("api_token", "LIBRATO_TOKEN"),
                      ("app_id", "LIBRATO_APP_ID"), ("integration", "LIBRATO_INTEGRATION")]:
        if var in os.environ:
            setattr(options, attr, os.environ[var])

    if "LIBRATO_INSTRUMENTATION_PORT" in os.environ:
        setattr(options, "port", int(os.environ["LIBRATO_INSTRUMENTATION_PORT"]))

    return options


def update_config_from_config_file(options=None, config_file=None):
    if not config_file:
        config_file = _globals.config_path

    options = options or config_info()

    if os.path.isfile(config_file):
        with open(config_file) as conf:
            agent_conf = json.load(conf)

            for key in config_options:
                if key in agent_conf and not hasattr(options, key):
                    setattr(options, key, agent_conf.get(key))
    else:
        logger.info("Config file %s doesn't exist", config_file)

    return options


def update_config_file(agent_settings, config_file=None):
    if not config_file:
        config_file = _globals.config_path

    with open(config_file, 'w') as conf:
        json.dump(agent_settings, conf, indent=3)


def validate_config(options):
    errors = []

    for (key, desc) in required_options:
        if not hasattr(options, key):
            errors.append('{} [{}] must be specified.'.format(key, desc))

    return len(errors) == 0, errors
