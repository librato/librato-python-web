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


"""
Responsible for managing and communicating configuration state of the process.
"""
import hashlib
import json
import os
import tempfile

from .util import debounce

CONFIG_REPORT = 'flask_restful.json'


class _globals:
    reporter = None


def set_reporter(reporter):
    """
    Sets the reporter for configuration information.

    Defaults to StdoutConfigReporter.

    :param reporter: the reporter instance
    """
    _globals.reporter = reporter


def declare(property_name, property_value):
    """
    Expresses a property name and value for this component.

    Example
        config.declare('flask.fw_versions', fw_version)
        config.declare('db.connectionpool.min', 10)
        config.declare('db.connectionpool.max', 50)

    :param property_name: the property name to report
    :param property_value: the value of the property (may be a dict containing nested properties)
    """
    _globals.reporter.declare(property_name, property_value)


def publish():
    """
    Signals that the configuration is ready to be pushed.

    This operation is not guaranteed to be synchronous.
    """
    _globals.reporter.publish()


class ConfigReporter(object):
    def __init__(self):
        super(ConfigReporter, self).__init__()
        self.config = {}

    def declare(self, property_name, property_value):
        """
        Expresses a property name and value for this component.

        :param property_name: the property name to report
        :type property_name: str
        :param property_value: the value of the property (may be a dict containing nested properties)
        """
        current = self.config
        elements = property_name.split('.')
        last_i = len(elements) - 1
        for i, element in enumerate(elements):
            if i == last_i:
                current[element] = property_value
            else:
                if element not in current:
                    current[element] = {}
                current = current[element]

    def publish(self):
        """
        Signals that the configuration is ready to be pushed.

        This operation is not guaranteed to be synchronous.
        """
        pass

    def internal_hash(self, config=None, md5=None):
        """
        Generates a hash code for the configuration that should be reliable, consistent, and unique.
        """
        config = self.config if config is None else config
        hasher = hashlib.md5() if md5 is None else md5
        if isinstance(config, dict):
            for k in sorted(config.keys()):
                value = config.get(k)
                if value:
                    self.internal_hash(value, hasher)
        elif hasattr(config, '__item__'):  # iterable
            for k in sorted(config):
                value = config.get(k)
                if value:
                    self.internal_hash(config.get(k), hasher)
        else:
            # Not iterable, it's a leaf... just encode it (should be in order)
            hasher.update(bytes(config))
        if md5 is None:
            return hasher.hexdigest()
        else:
            return None


class StdoutConfigReporter(ConfigReporter):
    def __init__(self):
        super(StdoutConfigReporter, self).__init__()

    def declare(self, property_name, property_value):
        super(StdoutConfigReporter, self).declare(property_name, property_value)

    def publish(self):
        """
        Signals that the configuration is ready to be pushed.

        This operation is not guaranteed to be synchronous.
        """
        super(StdoutConfigReporter, self).publish()
        print('Publishing configuration', self.internal_hash())
        for name, value in self.config.iteritems():
            print(name, value)


REPORTING_DELAY = 0.1  # 100 milliseconds delay


class LegacyConfigReporter(ConfigReporter):
    BASEDIR = '/tmp/solarwinds/swagd/python'

    def __init__(self):
        super(LegacyConfigReporter, self).__init__()
        self.debounce_publish = debounce(REPORTING_DELAY)(self.inner_publish)

    def declare(self, property_name, property_value):
        super(LegacyConfigReporter, self).declare(property_name, property_value)

    def publish(self):
        """
        Write configuration json in well-known place for collectd to collect
        """
        self.debounce_publish()

    def inner_publish(self):
        config_file = os.path.join(self.BASEDIR, str(os.getpid()), CONFIG_REPORT)
        try:
            os.makedirs(os.path.dirname(config_file))
        except OSError:
            pass

        # Write to a temporary file and rename for atomicity
        config = dict(self.config)
        config['identityHash'] = self.internal_hash()
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(json.dumps(config))
            f.flush()
            os.fsync(f.fileno())
            f.close()
        os.rename(f.name, config_file)


set_reporter(ConfigReporter())
