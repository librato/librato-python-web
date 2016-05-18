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

""" Utility methods module """

import json
import six

from librato_python_web.instrumentor.custom_logging import getCustomLogger

logger = getCustomLogger(__name__)


class _config(object):
    """ Globals """
    instrument = False


def configure(config_dict_or_filename):
    """
    Configures the instrumentation using key value pairs.

    The config_dict_or_filename is either a dict or a string filename. If it is a dict, it provides the key-value pairs
    directly. If it is a st, it identifies a path to a JSON file containing key-value pairs.

    Valid configuration parameters include:
    * autoInstrument: Boolean value that enables instrumentation if True (default False)
    * reporter: qualified class name of the class used to report metrics
    *           (default is the existing collectd implementation

    :param config_dict_or_filename: the given dict or filename
    :return:
    """
    cfg = None
    if isinstance(config_dict_or_filename, six.string_types):
        # Load JSON file
        with open(config_dict_or_filename) as conf:
            cfg = json.load(conf)
    elif isinstance(config_dict_or_filename, dict):
        cfg = config_dict_or_filename
    else:
        raise TypeError('config_dict_or_filename must be a dict or str')

    for k, v in six.iteritems(cfg):
        setattr(_config, k, v)

    if get_option('port'):
        setattr(_config, 'statsd.enabled', True)
        setattr(_config, 'statsd.port', _config.port)

    # TODO: cache.use_weak_refs
    # TODO: cache.max_keys


def set_option(param, value):
    """ Sets the value of a configuration option """
    setattr(_config, param, value)


def get_option(param, default_value=None):
    """ Gets the value of a configuration option """
    try:
        return getattr(_config, param)
    except AttributeError:
        # not found
        return default_value
