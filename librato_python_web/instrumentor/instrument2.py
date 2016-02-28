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

import functools
import inspect
import time
import sys

import six

from librato_python_web.instrumentor.custom_logging import getCustomLogger
from librato_python_web.instrumentor.telemetry import count
from librato_python_web.instrumentor.util import get_class_by_name

logger = getCustomLogger(__name__)


def get_increment_wrapper(metric, reporter='web', increment=1):
    """ Returns a wrapper which increments a counter for every invokation """
    def increment_wrapper(func, *args, **kwargs):
        count(metric=metric, reporter=reporter, incr=increment)
        return func(*args, **kwargs)

    return increment_wrapper


def get_delegating_wrapper(original_method, wrapper_method):
    """ Conceptually similar to functools.partial, but returns an object """
    """ that is a descriptor and can hence wrap an instance method """
    def delegator(*args, **kwargs):
        return wrapper_method(original_method, *args, **kwargs)

    return delegator


def instrument_methods_v2(method_wrappers):
    for qualified_method_name, method_wrapper in six.iteritems(method_wrappers):
        (fully_qualified_class_name, method_name) = qualified_method_name.rsplit('.', 1)
        try:
            class_def = get_class_by_name(fully_qualified_class_name)
            if class_def:
                logger.debug('instrumenting method %s', qualified_method_name)

                original_method = getattr(class_def, method_name)
                delegator = get_delegating_wrapper(original_method, method_wrapper)

                setattr(class_def, method_name, delegator)
            else:
                logger.warn('%s not instrumented because not found', fully_qualified_class_name)
        except ImportError:
            logger.debug('could not instrument %s', qualified_method_name)
            logger.warn('%s not instrumented because not found', fully_qualified_class_name)
        except:
            logger.exception('could not instrument %s', qualified_method_name)
