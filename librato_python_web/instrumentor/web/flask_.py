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

""" Flask instrumentation """
from importlib import import_module
from math import floor
import time

from librato_python_web.instrumentor import context as context
from librato_python_web.instrumentor import telemetry
from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor
from librato_python_web.instrumentor.instrument import get_conditional_wrapper
from librato_python_web.instrumentor.util import Timing
from librato_python_web.instrumentor.custom_logging import getCustomLogger


logger = getCustomLogger(__name__)


class __globals:
    # Reference to a flask.globals module which will be imported later
    flask_globals = None


def _teardown_request(e=None):
    if e:
        telemetry.count('web.errors')


def _flask_app(f, *args, **keywords):
    try:
        a = f(*args, **keywords)
        app = args[0]
        app.teardown_request(_teardown_request)
        return a
    except Exception as e:
        raise e
    finally:
        pass


def _flask_full_dispatch(f, *args, **keywords):
    # Compute and set the status code tag
    # This happens late enough that the status code is available
    rc = f(*args, **keywords)
    if hasattr(rc, 'status_code'):
        telemetry.count('web.status.%ixx' % floor(rc.status_code / 100))

        # Set this at the end, since only the wsgi-related metrics need the status tag
        context.set_tag('status', str(rc.status_code))

    return rc


def _flask_dispatch(f, *args, **keywords):
    try:
        try:
            if not __globals.flask_globals:
                # Flask should already have been imported so this won't actually
                # load anything new
                __globals.flask_globals = import_module('flask.globals')

            req = __globals.flask_globals._request_ctx_stack.top.request
            if req.url_rule:
                # Compute and set the handler tag
                func = args[0].view_functions[req.url_rule.endpoint]
                if hasattr(func, 'view_class'):
                    handler = func.view_class.__module__ + '.' + func.view_class.__name__ + '.' + req.method.lower()
                else:
                    handler = func.__module__ + '.' + func.__name__
                context.set_tag('handler', handler)
        except:
            logger.exception("Unexpected exception setting route tag")

        telemetry.count('web.requests')
        Timing.push_timer()

        return f(*args, **keywords)
    finally:
        elapsed, net_elapsed = Timing.pop_timer()
        telemetry.record('web.response.latency', elapsed)
        telemetry.record('app.response.latency', net_elapsed)


def _flask_wsgi_call(f, *args, **kwargs):
    t = time.time()
    try:
        try:
            context.set_tag('method', args[1]['REQUEST_METHOD'])
        except:
            pass
        return f(*args, **kwargs)
    finally:
        elapsed = time.time() - t
        telemetry.record('wsgi.response.latency', elapsed)
        context.reset_tags()


class FlaskInstrumentor(BaseInstrumentor):
    modules = {'flask.app': ['Flask']}

    def __init__(self):
        super(FlaskInstrumentor, self).__init__()

    def run(self):
        self.set_wrapped(
            {
                'flask.app.Flask.__init__': get_conditional_wrapper(_flask_app, enable_if=None),
                'flask.app.Flask.dispatch_request': get_conditional_wrapper(_flask_dispatch, enable_if=None),
                'flask.app.Flask.full_dispatch_request': get_conditional_wrapper(_flask_full_dispatch, enable_if=None,
                                                                                 state='web'),
                'flask.app.Flask.__call__': get_conditional_wrapper(_flask_wsgi_call, enable_if=None, state='wsgi'),
            })
        super(FlaskInstrumentor, self).run()
