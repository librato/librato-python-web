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
from contextlib import contextmanager
from math import floor
import threading
import time

from librato_python_web.instrumentor import config as agent_api_config
from librato_python_web.instrumentor import context as context
from librato_python_web.instrumentor import telemetry
from librato_python_web.instrumentor.instrument import contextmanager_wrapper_factory, function_wrapper_factory
from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor
from librato_python_web.instrumentor.util import Timing
from librato_python_web.instrumentor.custom_logging import getCustomLogger

STATE_NAME = 'web'

logger = getCustomLogger(__name__)


@contextmanager
def _flask_add_url_rule(self, route, *args, **kwargs):
    FlaskInstrumentor.urls.extend([route])
    agent_api_config.declare('urls', FlaskInstrumentor.urls)
    yield
    _publish_config()


def get_fw_version():
    """
    Tries to determine flask restful package version
    """
    if not FlaskInstrumentor.fw_version:
        try:
            import pkg_resources
            FlaskInstrumentor._fw_version = pkg_resources.require("flask")[0].version
            agent_api_config.declare('fw_version', FlaskInstrumentor.fw_version)
        except:
            # Might fail due to setuptools dependency
            pass


def _publish_config():
    """
    Publish the configuration
    """
    get_fw_version()
    agent_api_config.publish()


_context = threading.local()


def _before_request():
    try:
        from flask import request
        route = request.url_rule.rule if request.url_rule else None
        context.push_state(STATE_NAME)
        context.push_tag('web.route', route)
        context.push_tag('web.method', request.method)
        telemetry.count('web.requests')
        Timing.push_timer()
    except:
        logger.exception('before_request instrumentation failure')


def _after_request(response):
    try:
        context.pop_state(STATE_NAME)
        if response.status_code:
            telemetry.count('web.status.%ixx' % floor(response.status_code / 100))
    except:
        logger.exception('after_request instrumentation failure')
    finally:
        return response


def _teardown_request(e=None):
    try:
        if e:
            telemetry.count('web.errors')
    finally:
        try:
            elapsed, net_elapsed = Timing.pop_timer()
            telemetry.record('web.response.latency', elapsed)
            telemetry.record('app.response.latency', net_elapsed)
            try:
                context.pop_tag()
                context.pop_tag()
            except:
                logger.exception('Problem popping contexts')
        except:
            logger.exception('Teardown handler failed')
            raise


def _flask_app(f):
    def decorator(*args, **keywords):
        try:
            a = f(*args, **keywords)
            app = args[0]
            app.before_request(_before_request)
            app.after_request(_after_request)
            app.teardown_request(_teardown_request)
            return a
        except Exception as e:
            raise e
        finally:
            pass
    return decorator


def _flask_wsgi_call(f):
    def decorator(*args, **keywords):
        t = time.time()
        try:
            return f(*args, **keywords)
        finally:
            elapsed = time.time() - t
            telemetry.record('wsgi.response.latency', elapsed)
    return decorator


class FlaskInstrumentor(BaseInstrumentor):
    required_class_names = ['flask']

    fw_version = None
    urls = []

    def __init__(self):
        super(FlaskInstrumentor, self).__init__(
            {
                'flask.app.Flask.__init__': function_wrapper_factory(_flask_app, enable_if=None),
                'flask.app.Flask.add_url_rule': contextmanager_wrapper_factory(_flask_add_url_rule, enable_if=None),
                'flask.app.Flask.__call__': function_wrapper_factory(_flask_wsgi_call, enable_if=None, state='wsgi'),
            }
        )

    def run(self):
        super(FlaskInstrumentor, self).run()
