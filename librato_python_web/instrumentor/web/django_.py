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

DJANGO = 'web.django'


class AgentMiddleware(object):
    def __init__(self):
        self.is_active = False

    def process_request(self, request):
        self.is_active = True
        Timing.start_timer(DJANGO)
        context.push_state(DJANGO)
        context.push_tag('web.route', request.path)
        telemetry.count('web.django.requests')

    def process_view(self, request, view_func, view_args, view_kwargs):
        if self.is_active:
            telemetry.record('web.django.view.latency', time.clock() - self.is_active)

    def process_response(self, request, response):
        elapsed = Timing.stop_timer(DJANGO, accumulate=False)
        if self.is_active:
            telemetry.record('web.django.response.latency', elapsed)
            net_elapsed = elapsed - Timing.get_timer(DJANGO + Timing.NET_KEY, clear=True)
            telemetry.record('app.django.response.latency', net_elapsed)
            telemetry.count('web.django.status.%ixx' % floor(response.status_code / 100))
            try:
                context.pop_tag()
            except IndexError:
                logger.exception('process_response cannot pop context')
            context.pop_state(DJANGO)
            self.is_active = False
        else:
            logger.warn('process_response without request')
        return response

    def process_exception(self, request, exception):
        logger.debug('process_exception')
        if self.is_active:
            telemetry.count('web.django.errors')
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
            telemetry.record('wsgi.django.response.latency', elapsed)

    return inner_wsgi_call


class DjangoInstrumentor(BaseInstrumentor):
    settings = None
    required_class_names = ['django.core', 'django.apps']
    QUERY_SET = 'django.db.models.query.QuerySet'
    _wrapped = {
        'django.core.handlers.wsgi.WSGIHandler.__call__': function_wrapper_factory(_django_wsgi_call, state='wsgi',
                                                                                   enable_if=None),
        'django.conf.LazySettings.__getattr__': django_inject_middleware,

        QUERY_SET + '.aggregate': context_function_wrapper_factory(
            default_instrumentation('model.django.aggregate.'), state='model'),
        QUERY_SET + '.count': context_function_wrapper_factory(
            default_instrumentation('model.django.count.'), state='model'),
        QUERY_SET + '.bulk_create': context_function_wrapper_factory(
            default_instrumentation('model.django.bulk_create.'), state='model'),
        QUERY_SET + '.create': context_function_wrapper_factory(
            default_instrumentation('model.django.create.'), state='model'),
        QUERY_SET + '.get': context_function_wrapper_factory(
            default_instrumentation('model.django.get.'), state='model'),
        QUERY_SET + '.get_or_create': context_function_wrapper_factory(
            default_instrumentation('model.django.get_or_create.'), state='model'),
        QUERY_SET + '.latest': context_function_wrapper_factory(
            default_instrumentation('model.django.latest.'), state='model'),
        QUERY_SET + '.first': context_function_wrapper_factory(
            default_instrumentation('model.django.first.'), state='model'),
        QUERY_SET + '.last': context_function_wrapper_factory(
            default_instrumentation('model.django.last.'), state='model'),
        QUERY_SET + '.in_bulk': context_function_wrapper_factory(
            default_instrumentation('model.django.in_bulk.'), state='model'),
        QUERY_SET + '.iterator': context_function_wrapper_factory(
            default_instrumentation('model.django.iterator.'), state='model'),
        QUERY_SET + '.update_or_create': context_function_wrapper_factory(
            default_instrumentation('model.django.update_or_create.'), state='model'),
        QUERY_SET + '.delete': context_function_wrapper_factory(
            default_instrumentation('model.django.delete.'), state='model'),
        QUERY_SET + '.update': context_function_wrapper_factory(
            default_instrumentation('model.django.update.'), state='model'),
        QUERY_SET + '.exists': context_function_wrapper_factory(
            default_instrumentation('model.django.exists.'), state='model'),
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
