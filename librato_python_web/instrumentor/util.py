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


from collections import OrderedDict
import functools
import hashlib
import re
import time

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
    def _get_timers():
        """
        :return:
        :rtype: list
        """
        if not Timing.context:
            import threading
            Timing.context = threading.local()
        if not hasattr(Timing.context, 'timers'):
            Timing.context.timers = list()
        return Timing.context.timers

    @staticmethod
    def get_value(name, default=None):
        value = Timing._get_dict().get(name)
        if value is None and default is not None:
            Timing._get_dict()[name] = default
            return default
        else:
            return value

    @staticmethod
    def push_timer():
        """
        Create a new timing context
        """
        # start time and accumulator for children to use
        Timing._get_timers().append([time.time(), 0])

    @staticmethod
    def pop_timer():
        """
        Returns a tuple consisting of elapsed time in this timer and net time spent in this timer, exclusive of
        children.

        Updates parent's time for this child, if applicable.

        :return: elapsed time and net time in seconds
        """
        # start time and accumulator for children to use
        timers = Timing._get_timers()
        start_time, children = timers.pop()
        elapsed_time = time.time() - start_time
        net_time = elapsed_time - children
        if timers:
            # accumulate as child time
            timers[-1][1] += elapsed_time
        return elapsed_time, net_time


def wraps(wrapped, assigned=functools.WRAPPER_ASSIGNMENTS, updated=functools.WRAPPER_UPDATES):
    """
    Safely wraps the given method, avoid problems when attributes are missing (e.g., from native methods).
    :param wrapped: the method to be wrapped
    :param assigned: the attributes to assign from the wrapped method to the wrapper
    :param updated: the attributes to update from the wrapped method to the wrapper
    :return: the wrapped method
    """
    return functools.wraps(wrapped, assigned=filter(lambda a: hasattr(wrapped, a), assigned),
                           updated=filter(lambda a: hasattr(wrapped, a), updated))


def prepend_to_tuple(t, value):
    """
    Creates a new version of tuple t with the given value prepended to it.
    :param t: the given tuple
    :param value: the given value
    :return: the new tuple
    """
    l = list(t)
    l.insert(0, value)
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
            h.update(str_value.encode('utf-8'))
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
    """
    Returns the given argument or, if that's missing, the given keyword.

    :param i: the args position
    :param key: the name of the keyword
    :param args: list of arguments
    :param keywords: dict of keyword names
    :return: the value, or None if not present
    """
    return args[i] if len(args) > i else keywords.get(key)


def is_class_available(fully_qualified_class_name):
    """
    Return True if the class / module with fully_qualified_class_name is loadable.

    :param fully_qualified_class_name:
    :type fully_qualified_class_name: str
    :return: True if class is found, False otherwise
    :returns: bool
    """
    return get_module_by_name(fully_qualified_class_name) is not None or \
        get_class_by_name(fully_qualified_class_name) is not None


def get_module_by_name(fully_qualified_module_name):
    """
    Returns a reference to the given module.

    :param fully_qualified_module_name: fully qualified name of the module
    :return: the module, or None if not found
    """
    try:
        return __import__(fully_qualified_module_name)
    except ImportError:
        return None


def get_class_by_name(fully_qualified_class_name):
    """
    Return the class with fully_qualified_class_name.

    :param fully_qualified_class_name:
    :type fully_qualified_class_name: str
    :return: the specified class, None if not found
    """
    (module_path, class_name) = fully_qualified_class_name.rsplit('.', 1) if '.' in fully_qualified_class_name \
        else (fully_qualified_class_name, None)
    try:
        module_def = __import__(module_path, globals(), locals(), [class_name] if class_name else [])
        class_def = getattr(module_def, class_name) if module_def and class_name else module_def
    except ImportError:
        logger.info('%s not found', fully_qualified_class_name)
        class_def = None

    return class_def


def wrap_method(method_owner, method_name, method_wrapper):
    """
    Wrap the method with the method_name on the class_def using the method_wrapper.

    Records original information on the wrapper method so that method can be "unwrapped" as an "original" attribute on
    the method_wrapper (see unwrap_method()).

    :param method_owner: the object on which the method is set (e.g., class or module)
    :param method_name: the name of the attribute to be overridden
    :param method_wrapper: the function that wraps the method (takes the method as the sole argument)
    """
    original_method = getattr(method_owner, method_name)
    wrapped_method = method_wrapper(original_method)
    wrapped_method.original = (method_owner, method_name, original_method)
    replace_method(method_owner, method_name, wrapped_method)


def unwrap_method(method_wrapper):
    """
    Unwraps the given method presuming that it was set using wrap_method.

    Needs original information on the wrapper method so that method can be "unwrapped" (in "original" attribute).

    :param method_wrapper: the function that wraps the method to be restored
    """
    if hasattr(method_wrapper, 'original'):
        original = method_wrapper.original
        replace_method(*original)
        delattr(method_wrapper, 'original')


def replace_method(owner, method_name, method):
    """
    Replaces the given method name on the given class_def with the given method.

    :param owner: the owner of the method (class or module)
    :param method_name: the method name on the owner
    :param method: the method to use
    """
    try:
        setattr(owner, method_name, method)
    except TypeError as e:
        msg = str(e)
        if "can't set attributes of built-in/extension type" in msg:
            logger.info(str(e))  # expected problem
        else:
            logger.error(str(e))
