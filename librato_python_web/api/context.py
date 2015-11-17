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
enables the aggregation and reporting of telemetry for different dimenions of activity.

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
from contextlib import contextmanager
import logging

from librato_python_web.instrumentor import context

logger = logging.getLogger(__name__)


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
    context.push_tag(key, value)
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
    return context.get_tags()


def get_current():
    """
    Gets the top context element in the context stack (what would be returned by context.pop()).

    :return: the top context element in the stack
    """
    return context.get_current()


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
    return context.pop_tag()


def fail():
    """
    Indicates that the current request has failed and will terminate. Clears the context stack.

    Future: notify listeners of outcome so that telemetry writer can perform appropriate actions.
    """
    context.fail()


def succeed():
    """
    Indicates that the current request has succeeded and will terminate. Clears the context stack.

    Future: notify listeners of outcome so that telemetry writer can perform appropriate actions.
    """
    context.succeed()


def push_state(name):
    context.push_state(name)


def pop_state(name):
    return context.pop_state(name)


def has_state(name):
    return context.has_state(name)
