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

""" CherryPy instrumentation """

from importlib import import_module
import time

from librato_python_web.instrumentor import context as context
from librato_python_web.instrumentor import telemetry
from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor
from librato_python_web.instrumentor.instrument import get_conditional_wrapper
from librato_python_web.instrumentor.util import Timing
from librato_python_web.instrumentor.custom_logging import getCustomLogger

STATE_NAME = 'web'

logger = getCustomLogger(__name__)


class __globals:
    set_hook = True
    cherrypy = None


def _cherrypy_respond_wrapper(func, *args, **keywords):
    status_code = None
    try:
        Timing.push_timer()

        # call the request function
        response = func(*args, **keywords)

        if response.status:
            telemetry.count('web.status.%sxx' % response.status[0:1])
            status_code = response.status
        return response
    except Exception as e:
        telemetry.count('web.errors')
        raise e
    finally:
        try:
            elapsed, net_elapsed = Timing.pop_timer()
            telemetry.record('web.response.latency', elapsed)
            telemetry.record('app.response.latency', net_elapsed)
            telemetry.count('web.requests')

            if status_code:
                # Do this here since we only want the wsgi metrics tagged with status
                context.set_tag('status', status_code[0:3])
        except:
            logger.exception('Teardown handler failed')
            raise


def on_start_resource():
    try:
        handler = __globals.cherrypy.serving.request.handler
        if hasattr(handler, 'callable'):
            callable = handler.callable
            klass = callable.im_class
            handler = klass.__module__ + '.' + klass.__name__ + '.' + callable.__name__
            context.set_tag('handler', handler)
    except:
        logger.exception('Error setting handler tag value')


def _cherrypy_wsgi_call(func, *args, **keywords):
    if __globals.set_hook:
        try:
            # Set a hook to set the handler tag for every request
            # This is done here since we need to be sure that cherrypy has been imported
            # Also use the earliest possible hook, since subsequent hooks might wrap the handler instance
            __globals.set_hook = False
            __globals.cherrypy = import_module('cherrypy')
            __globals.cherrypy.request.hooks.attach('on_start_resource', on_start_resource, priority=1)
        except:
            logger.exception('Error setting on_start_resource hook')

    t = time.time()
    try:
        try:
            context.set_tag('method', args[1]['REQUEST_METHOD'])
        except:
            pass
        return func(*args, **keywords)
    finally:
        elapsed = time.time() - t
        telemetry.record('wsgi.response.latency', elapsed)
        context.reset_tags()


class CherryPyInstrumentor(BaseInstrumentor):
    modules = {'cherrypy._cptree': ['Application'], 'cherrypy._cprequest': ['Request']}

    def __init__(self):
        super(CherryPyInstrumentor, self).__init__()

    def run(self):
        self.set_wrapped(
            {
                'cherrypy._cptree.Application.__call__': get_conditional_wrapper(_cherrypy_wsgi_call, enable_if=None,
                                                                                 state='web'),
                'cherrypy._cprequest.Request.run': get_conditional_wrapper(_cherrypy_respond_wrapper, enable_if=None,
                                                                           state='wsgi'),
            })
        super(CherryPyInstrumentor, self).run()
