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
The API supports the notion of a thread-based context stack. Implemented as a thread local variable, the stack
enables the aggregattion and reporting of telemetry for different dimenions of activity.

For example, a SQL query might be measured in the context of:
*	    a SQL statement (e.g., "SELECT u.name from users as u where id=?")
*	    a database connection pool
*	    the database schema
*	    the database host
*	    a user-defined context (e.g., "create-account")
*	    the HTTP request route
*	    the process identity

Context is implemented as a stack. Each item on the context stack has an identifier.

Auto-instrumentation is currently determined using hard-coded configuration.

Metrics are accumulated individually and as an intersection of the context.
"""
from collections import defaultdict
from contextlib import contextmanager

import threading

from librato_python_web.instrumentor.custom_logging import getCustomLogger

logger = getCustomLogger(__name__)


class _globals:
    context = threading.local()


def _set_stack(stack):
    """
    Assigns the stack to the given stack state.

    :param stack: an array of stack entries
    """
    _globals.context.stack = stack


def _get_stack():
    """
    Returns this thread's stack.

    :return: the stack
    :rtype: list
    """
    if not getattr(_globals.context, 'stack', None):
        _set_stack([])
    return _globals.context.stack


def _set_state(state):
    """
    Assigns the state the given state.

    :param state: an set of state entries
    """
    _globals.context.state = defaultdict(int, state)


def _get_state():
    """
    Returns this thread's state.

    :return: the state
    :rtype: dict
    """
    if not getattr(_globals.context, 'state', None):
        _set_state({})
    return _globals.context.state


@contextmanager
def add_tag(key, value):
    """
    Applies the given key-value pair as a new level of context to the body of code that it wraps. When the code exits,
    the entry is removed.

    This effectively pushes the context on entry and clears it on exit.

    As a Python contextmanager, this is typically applied using a with statement.

    Example
        with context.add('user-operation', 'create-account'):
          # code that creates account goes here...
          # this context includes the key-value pair ('user-operation', 'create-account')

    :param key: the given key
    :param value: the given value
    """
    # noinspection PyBroadException
    try:
        push_tag(key, value)
        yield
        pop_tag()
    except Exception:
        fail()


@contextmanager
def add_all_tags(context_list):
    """
    Applies the context_list as key-value pairs to the context.

    This effectively pushes the contexts on entry and clears it on exit.

    As a Python contextmanager, this is typically applied using a with statement.

    Example
        with context.add([('user-operation', 'create-account')]):
          # code that creates account goes here...
          # this context includes the key-value pair ('user-operation', 'create-account')

    :param context_list: list of tuples containing key-value pairs
    """
    # noinspection PyBroadException
    try:
        for entry in context_list:
            push_tag(entry[0], entry[1])
        # noinspection PyBroadException
        yield
        for _ in context_list:
            pop_tag()
    except:
        fail()
        raise


def push_tag(key, value):
    """
    Pushes the given key-value pair onto the context stack.

    :param key:
    :param value:
    :return:
    """
    _get_stack().append((key, value))
    return None


def get_tags():
    """
    Gets the current stack

    Example
        context.push('route', '/v1/foo')
        context.push('user-operation', 'create-foo')
        c = context.get()
        # c is [('route', '/v1/foo'),('user-operation', 'create-foo')]

    :return: the current stack
    """
    return list(_get_stack())


def get_current():
    """
    Gets the top context element in the context stack (what would be returned by context.pop()).

    :return: the top context element in the stack
    """
    return _get_stack()[-1]


def pop_tag():
    """
    Pops the context entry from the top of the stack and returns it.

    Example
        context.push('route', '/v1/foo')
        context.push('user-operation', 'create-foo')
        # context is [('route', '/v1/foo'),('user-operation', 'create-foo')]
        e = context.pop()
        # e is ('user-operation', 'create-foo')
        e = context.pop()
        # e is ('route', '/v1/foo')
    :return: the entry on the top of the stack
    """
    o = _get_stack().pop()
    # TODO: On empty context, notify listeners (e.g., flush buffers, etc.)
    return o


def fail():
    """
    Indicates that the current request has failed and will terminate. Clears the context stack.

    Future: notify listeners of outcome so that telemetry writer can perform appropriate actions.
    """
    # TODO: notify listeners (e.g., flush buffers, etc.)
    _set_stack([])


def succeed():
    """
    Indicates that the current request has succeeded and will terminate. Clears the context stack.

    Future: notify listeners of outcome so that telemetry writer can perform appropriate actions.
    """
    # TODO: notify listeners (e.g., flush buffers, etc.)
    _set_stack([])


def push_state(name):
    _get_state()[name] += 1
    if '.' in name:
        name = name.split('.')[0]
        _get_state()[name] += 1


def pop_state(name):
    count = _get_state().get(name)
    if count is None:
        logger.error('pop_state state does not contain %s', name)
    elif count > 1:
        _get_state()[name] = count - 1
    else:
        del _get_state()[name]

    if '.' in name:
        name = name.split('.')[0]
        count = _get_state().get(name)
        if count is None:
            logger.error('pop_state state does not contain %s', name)
        elif count > 1:
            _get_state()[name] = count - 1
        else:
            del _get_state()[name]


def has_state(name):
    return _get_state().get(name, 0) > 0
