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

from contextlib import contextmanager

from librato_python_web.instrumentor import telemetry


def count(metric, incr=1):
    """
    Increment the count for the given metric by the given increment.

    Example
        telemetry.count('requests')
        telemetry.count('bytesReceived', len(request.content))

    :param metric: the given metric name
    :param incr: the value by which it is incremented
    """
    return telemetry.count(metric, incr)


def record(metric, value):
    """
    Records a given value as a data point for the given metric at the current timestamp.

    The current of the context stack is included.

    Example
        telemetry.record('maxHeap', max_heap_size)

    :param metric: the given metric name
    :param value: the value to be recorded
    """
    return telemetry.record(metric, value)


def event(event_type, dictionary=None):
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
    telemetry.event(event_type, dictionary)


def default_instrumentation(type_name='resource'):
    return telemetry.default_instrumentation()


def increment_count(type_name='resource'):
    @contextmanager
    def wrapper_func(*args, **keywords):
        count(type_name + 'requests')
        yield

    return wrapper_func
