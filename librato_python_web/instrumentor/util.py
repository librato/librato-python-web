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


import base64
from collections import OrderedDict, defaultdict
import hashlib
import re
import time
from librato_python_web.instrumentor import context

from librato_python_web.instrumentor.instrument import get_module_by_name
from librato_python_web.instrumentor.custom_logging import getCustomLogger

logger = getCustomLogger(__name__)

RE_CLEANSE = re.compile('[^A-Za-z0-9.:\\-_]')
MAX_NAME_LEN = 48
ALIAS_CACHE_LEN = 48


class Timing(object):
    context = None
    NET_KEY = '_net'

    @staticmethod
    def _get_dict():
        if not Timing.context:
            import threading
            Timing.context = threading.local()
        if not hasattr(Timing.context, 'dict'):
            Timing.context.dict = {}
        return Timing.context.dict

    @staticmethod
    def get_value(name, default=None):
        value = Timing._get_dict().get(name)
        if value is None and default is not None:
            Timing._get_dict()[name] = default
            return default
        else:
            return value

    @staticmethod
    def get_timers():
        return Timing.get_value('timers', defaultdict(int))

    @staticmethod
    def start_timer(name='default'):
        logger.debug('>start_timer %s', name)
        Timing.get_timers()[name] = time.clock()

    @staticmethod
    def get_timer(name='default', clear=False):
        try:
            return Timing.get_timers()[name]
        finally:
            if clear:
                del Timing.get_timers()[name]

    @staticmethod
    def stop_timer(name='default', accumulate=True):
        timers = Timing.get_timers()
        logger.debug('<stop_timer %s', name)
        if name in timers:
            try:
                elapsed = time.clock() - timers[name]
                if accumulate:
                    for state in context._get_state():
                        key = state + Timing.NET_KEY
                        timers[key] += elapsed
                return elapsed
            finally:
                if name in timers:
                    del timers[name]
                pass
        else:
            logger.error('timer not found %s', name)
            return 0


def prepend_to_tuple(t, value):
    l = list(t)
    l.insert(0, value)
    return tuple(l)


def append_to_tuple(t, value):
    l = list(t)
    l.extend([value])
    return tuple(l)


class AliasGenerator(object):
    def __init__(self, size=200):
        self.MAX_CACHE = size  # TODO: Make configurable
        self.cache = OrderedDict()

    def generate_alias(self, str_value):
        """
        Generate an alias for the given string.
        :param str_value: the given string
        :return: a 24 character alias string
        """
        alias = self.get_alias(str_value)
        if not alias:
            h = hashlib.md5()
            h.update(str_value)
            alias = h.hexdigest()
            self.cache[str_value] = alias
            if len(self.cache) > self.MAX_CACHE:
                self.cache.popitem(last=False)  # FIFO
        else:
            alias = alias
        return alias

    def needs_alias(self, str_value):
        return len(str_value) > MAX_NAME_LEN or len(RE_CLEANSE.findall(str_value)) > 0

    def get_alias(self, str_value):
        return self.cache.get(str_value)

    def clear_aliases(self):
        self.cache.clear()


def is_safe_name(name):
    return len(RE_CLEANSE.findall(name)) == 0


def safe_name(name):
    return RE_CLEANSE.sub('_', name)


def pseudo_base64(val):
    """
    Generates a "Librato-safe" version of the base-64 encoding.

    :param val: the string to encode
    :type val: basestring
    :return: the safe version
    """
    return safe_name(base64.b64encode(val))


def debounce(delay):
    from threading import Timer

    def wrapper(func):
        def wrapped(*args, **keywords):
            try:
                wrapped.timer.cancel()
            except AttributeError:
                pass  # timer does not exist yet
            wrapped.timer = Timer(delay, lambda: func(*args, **keywords))
            wrapped.timer.start()

        return wrapped

    return wrapper


def get_parameter(i, key, *args, **keywords):
    return args[i] if len(args) > i else keywords.get(key)


def lazy_import(package):
    return get_module_by_name(package)
