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


from librato_python_web.instrumentor.instrument import instrument_methods, function_wrapper_factory, \
    context_function_wrapper_factory, generator_wrapper_factory
from librato_python_web.instrumentor import context as context
from librato_python_web.instrumentor import telemetry
from librato_python_web.instrumentor.telemetry import default_instrumentation, generate_record_telemetry
from librato_python_web.instrumentor.util import prepend_to_tuple, Timing
from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor
from librato_python_web.instrumentor.custom_logging import getCustomLogger

import time
from math import floor

logger = getCustomLogger(__name__)

STATE_NAME = 'web'


class AgentMiddleware(object):
    def __init__(self):
        self.is_active = False

    def process_request(self, request):
        self.is_active = True
        Timing.push_timer()
        context.push_state(STATE_NAME)
        context.push_tag('web.route', request.path)
        telemetry.count('web.requests')

    def process_view(self, request, view_func, view_args, view_kwargs):
        if self.is_active:
            telemetry.record('web.view.latency', time.time() - self.is_active)

    def process_response(self, request, response):
        elapsed, net_elapsed = Timing.pop_timer()
        if self.is_active:
            telemetry.record('web.response.latency', elapsed)
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


_middleware_hook_installed = False


def django_inject_middleware(original_method):
    """TODO: create one-time wrapper that removes itself after success"""
    """TODO: eliminate global flag"""

    def decorator(*args, **keywords):
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

    return decorator


def _django_wsgi_call(original_method):
    def decorator(*args, **keywords):
        Timing.push_timer()
        try:
            return original_method(*args, **keywords)
        finally:
            elapsed, net_elapsed = Timing.pop_timer()
            telemetry.record('wsgi.response.latency', elapsed)

    return decorator


class DjangoInstrumentor(BaseInstrumentor):
    required_class_names = ['django.core', 'django.apps']
    _wrapped = {
        'django.core.handlers.wsgi.WSGIHandler.__call__': function_wrapper_factory(_django_wsgi_call, state='wsgi',
                                                                                   enable_if=None),
        'django.conf.LazySettings.__getattr__': django_inject_middleware,

        'django.db.models.query.QuerySet.iterator': generator_wrapper_factory(
            generate_record_telemetry('model.iterator.'), state='model'),
    }
    _query_set_methods = 'aggregate, count, bulk_create, create, get, get_or_create, latest, first, last, in_bulk,' \
                         'iterator, update_or_create, delete, update, exists'

    def __init__(self):
        super(DjangoInstrumentor, self).__init__()
        for method in [m.strip() for m in self._query_set_methods.split(',')]:
            self._wrapped['django.db.models.query.QuerySet.%s' % method] = self.instrument('model.%s.' % method,
                                                                                           state='model')

    def run(self):
        try:
            instrument_methods(self._wrapped)
            logger.debug('django instrumentation complete')
        except:
            logger.exception('problem with django instrumentation')
            raise
