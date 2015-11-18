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
import time
from math import floor

from librato_python_web.instrumentor.instrument import instrument_methods, function_wrapper_factory, \
    context_function_wrapper_factory
from librato_python_web.instrumentor import context as context
from librato_python_web.instrumentor import telemetry
from librato_python_web.instrumentor.telemetry import default_instrumentation
from librato_python_web.instrumentor.util import prepend_to_tuple, Timing
from librato_python_web.instrumentor.instrumentor import BaseInstrumentor

logger = logging.getLogger(__name__)

STATE_NAME = 'web'


class AgentMiddleware(object):
    def __init__(self):
        self.is_active = False

    def process_request(self, request):
        self.is_active = True
        Timing.start_timer(STATE_NAME)
        context.push_state(STATE_NAME)
        context.push_tag('web.route', request.path)
        telemetry.count('web.requests')

    def process_view(self, request, view_func, view_args, view_kwargs):
        if self.is_active:
            telemetry.record('web.view.latency', time.clock() - self.is_active)

    def process_response(self, request, response):
        elapsed = Timing.stop_timer(STATE_NAME, accumulate=False)
        if self.is_active:
            telemetry.record('web.response.latency', elapsed)
            net_elapsed = elapsed - Timing.get_timer(STATE_NAME + Timing.NET_KEY, clear=True)
            telemetry.record('app.response.latency', net_elapsed)
            telemetry.count('web.status.%ixx' % floor(response.status_code / 100))
            try:
                context.pop_tag()
            except IndexError:
                logger.exception('process_response cannot pop context')
            context.pop_state(STATE_NAME)
            self.is_active = False
        else:
            logger.warn('process_response without request')
        return response

    def process_exception(self, request, exception):
        logger.debug('process_exception')
        if self.is_active:
            telemetry.count('web.errors')
            self.is_active = False


_middleware_hook_installed = False


def django_inject_middleware(class_def, original_method):
    """TODO: create one-time wrapper that removes itself after success"""
    """TODO: eliminate global flag"""

    def wrapped(*args, **keywords):
        settings = args[0]
        global _middleware_hook_installed
        if not _middleware_hook_installed:
            logger.info('injecting AgentMiddleware into django')
            a = original_method(settings, 'MIDDLEWARE_CLASSES')
            # Capture all calls
            a = prepend_to_tuple(a, 'librato_python_web.instrumentor.web.django_.AgentMiddleware')
            settings._wrapped.MIDDLEWARE_CLASSES = a
            _middleware_hook_installed = True
            logger.info('new middleware stack: %s', str(a))

        a = original_method(*args, **keywords)
        return a

    return wrapped


def _django_wsgi_call(f):
    def inner_wsgi_call(*args, **keywords):
        t = time.clock()
        try:
            return f(*args, **keywords)
        finally:
            elapsed = time.clock() - t
            telemetry.record('wsgi.response.latency', elapsed)

    return inner_wsgi_call


class DjangoInstrumentor(BaseInstrumentor):
    settings = None
    required_class_names = ['django.core', 'django.apps']
    QUERY_SET_CLASS_NAME = 'django.db.models.query.QuerySet'
    _wrapped = {
        'django.core.handlers.wsgi.WSGIHandler.__call__': function_wrapper_factory(_django_wsgi_call, state='wsgi',
                                                                                   enable_if=None),
        'django.conf.LazySettings.__getattr__': django_inject_middleware,

        QUERY_SET_CLASS_NAME + '.aggregate': context_function_wrapper_factory(
            default_instrumentation('model.aggregate.'), state='model'),
        QUERY_SET_CLASS_NAME + '.count': context_function_wrapper_factory(
            default_instrumentation('model.count.'), state='model'),
        QUERY_SET_CLASS_NAME + '.bulk_create': context_function_wrapper_factory(
            default_instrumentation('model.bulk_create.'), state='model'),
        QUERY_SET_CLASS_NAME + '.create': context_function_wrapper_factory(
            default_instrumentation('model.create.'), state='model'),
        QUERY_SET_CLASS_NAME + '.get': context_function_wrapper_factory(
            default_instrumentation('model.get.'), state='model'),
        QUERY_SET_CLASS_NAME + '.get_or_create': context_function_wrapper_factory(
            default_instrumentation('model.get_or_create.'), state='model'),
        QUERY_SET_CLASS_NAME + '.latest': context_function_wrapper_factory(
            default_instrumentation('model.latest.'), state='model'),
        QUERY_SET_CLASS_NAME + '.first': context_function_wrapper_factory(
            default_instrumentation('model.first.'), state='model'),
        QUERY_SET_CLASS_NAME + '.last': context_function_wrapper_factory(
            default_instrumentation('model.last.'), state='model'),
        QUERY_SET_CLASS_NAME + '.in_bulk': context_function_wrapper_factory(
            default_instrumentation('model.in_bulk.'), state='model'),
        QUERY_SET_CLASS_NAME + '.iterator': context_function_wrapper_factory(
            default_instrumentation('model.iterator.'), state='model'),
        QUERY_SET_CLASS_NAME + '.update_or_create': context_function_wrapper_factory(
            default_instrumentation('model.update_or_create.'), state='model'),
        QUERY_SET_CLASS_NAME + '.delete': context_function_wrapper_factory(
            default_instrumentation('model.delete.'), state='model'),
        QUERY_SET_CLASS_NAME + '.update': context_function_wrapper_factory(
            default_instrumentation('model.update.'), state='model'),
        QUERY_SET_CLASS_NAME + '.exists': context_function_wrapper_factory(
            default_instrumentation('model.exists.'), state='model'),
        # 'django.core.urlresolvers.get_resolver': django_resolve_url,
        # 'django.apps.registry.Apps.populate': get_urls,
    }

    def __init__(self):
        super(DjangoInstrumentor, self).__init__()

    def run(self):
        try:
            instrument_methods(self._wrapped)
            logger.debug('django instrumentation complete')
        except:
            logger.exception('problem with django instrumentation')
            raise
