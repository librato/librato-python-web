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

from librato_python_web.instrumentor import general


def configure(config_dict_or_filename):
    """
    TBD Configures the instrumentation using key value pairs.

    The config_dict_or_filename is either a dict or a string filename. If it is a dict, it provides the key-value pairs
    directly. If it is a st, it identifies a path to a JSON file containing key-value pairs.

    Valid configuration parameters include:
    * autoInstrument: Boolean value that enables instrumentation if True (default False)
    * reporter: qualified class name of the class used to report metrics
    *           (default is the existing collectd implementation

    :param config_dict_or_filename: the given dict or filename
    """
    general.configure(config_dict_or_filename)


def define_metric(metric, metadata_dict):
    """
    TBD Defines a new metric for the application.

    Provides metadata required for the system as key-value pairs in metadata_dict. Metadata could include, for example,
    metric type, display name, aggregation function.

    The metadata is reported to the back-end.

    :param metric: the given metric name to define
    :type metric: basestring
    :param metadata_dict: the given metric's definition as a dict
    :type metadata_dict: dict
    """
    general.define_metric(metric, metadata_dict)


def set_option(param, value):
    """

    :param param:
    :param value:
    """
    general.set_option(param, value)


def get_option(param, default_value=None):
    """

    :param param:
    :param default_value:
    :return:
    """
    return general.get_option(param, default_value)
