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
from math import floor
import time

from librato_python_web.instrumentor import telemetry
from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor
from librato_python_web.instrumentor.instrument import get_conditional_wrapper
from librato_python_web.instrumentor.util import Timing
from librato_python_web.instrumentor.custom_logging import getCustomLogger


logger = getCustomLogger(__name__)


def _after_request(response):
    # We need this since the response object isn't available in main function wrapper below (flask_dispatch).
    # Might not get called in the event of an application error.
    if response.status_code:
        telemetry.count('web.status.%ixx' % floor(response.status_code / 100))
    return response


def _teardown_request(e=None):
    if e:
        telemetry.count('web.errors')


def _flask_app(f, *args, **keywords):
    try:
        a = f(*args, **keywords)
        app = args[0]
        app.after_request(_after_request)
        app.teardown_request(_teardown_request)
        return a
    except Exception as e:
        raise e
    finally:
        pass


def _flask_dispatch(f, *args, **keywords):
    try:
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
        return f(*args, **kwargs)
    finally:
        elapsed = time.time() - t
        telemetry.record('wsgi.response.latency', elapsed)


class FlaskInstrumentor(BaseInstrumentor):
    modules = {'flask.app': ['Flask']}

    def __init__(self):
        super(FlaskInstrumentor, self).__init__()

    def run(self):
        self.set_wrapped(
            {
                'flask.app.Flask.__init__': get_conditional_wrapper(_flask_app, enable_if=None),
                'flask.app.Flask.dispatch_request': get_conditional_wrapper(_flask_dispatch, enable_if=None,
                                                                            state='web'),
                'flask.app.Flask.__call__': get_conditional_wrapper(_flask_wsgi_call, enable_if=None, state='wsgi'),
            })
        super(FlaskInstrumentor, self).run()
