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
from math import floor

from librato_python_web.instrumentor import context
from librato_python_web.instrumentor.instrument import _should_be_instrumented
from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor
from librato_python_web.instrumentor.objproxies import ObjectWrapper
from librato_python_web.instrumentor import telemetry
from librato_python_web.instrumentor.util import get_parameter, Timing


# TODO: make this generally available in instrument.py??
def _wrapped_call(metric, func, *args, **keywords):
    """ Times and executes arbitrary method """
    state = 'external'

    if not _should_be_instrumented(state, enable_if='web', disable_if='model'):
        return func(*args, **keywords)

    Timing.push_timer()
    try:
        context.push_state(state)
        return func(*args, **keywords)
    finally:
        context.pop_state(state)
        elapsed, _ = Timing.pop_timer()
        telemetry.record(metric, elapsed)


class _response_wrapper(ObjectWrapper):
    """ Wraps responses returned by urllib2.open """
    """ Note: this needs to be an old-style class for the dynamic method assignments """
    """       for __iter__ and next to work """
    def __init__(self, scheme, subject):
        super(_response_wrapper, self).__init__(subject)
        self.metric_name = 'external.{}.response.latency'.format(scheme)

    def read(self, *args, **keywords):
        return _wrapped_call(self.metric_name, self.__subject__.read, *args, **keywords)

    def readline(self, *args, **keywords):
        return _wrapped_call(self.metric_name, self.__subject__.readline, *args, **keywords)

    def readlines(self, *args, **keywords):
        return _wrapped_call(self.metric_name, self.__subject__.readlines, *args, **keywords)


def _urllib_open_wrapper(func, *args, **keywords):
    """ Wraps urllib.request.url_open """

    if not _should_be_instrumented(state='external', enable_if='web', disable_if='model'):
        return func(*args, **keywords)

    url = get_parameter(1, 'fullurl', *args, **keywords)

    if hasattr(url, 'get_full_url'):
        url = url.get_full_url()

    scheme = url.split(':')[0] if ':' in url else 'unknown'

    Timing.push_timer()
    try:
        context.push_state('external')
        telemetry.count('external.{}.requests'.format(scheme))
        a = func(*args, **keywords)
        if a.getcode():
            # Not meaningful for ftp etc
            telemetry.count('external.{}.status.%ixx'.format(scheme) % floor(a.getcode() / 100))
    except:
        telemetry.count('external.{}.errors'.format(scheme))
        raise
    finally:
        context.pop_state('external')
        elapsed, _ = Timing.pop_timer()
        telemetry.record('external.{}.response.latency'.format(scheme), elapsed)

    # Return a wrapped object so we can time subsequent read, readline etc calls
    return _response_wrapper(scheme, a)


class Urllib2Instrumentor(BaseInstrumentor):
    """ Python2 urllib2 """
    modules = {'urllib2': ['OpenerDirector']}

    def __init__(self):
        self.major_versions = [2]
        super(Urllib2Instrumentor, self).__init__()

    def run(self):
        self.set_wrapped({'urllib2.OpenerDirector.open': _urllib_open_wrapper})
        super(Urllib2Instrumentor, self).run()


class UrllibInstrumentor(BaseInstrumentor):
    """ Python3 urllib """
    modules = {'urllib.request': ['OpenerDirector']}

    def __init__(self):
        self.major_versions = [3]
        super(UrllibInstrumentor, self).__init__()

    def run(self):
        self.set_wrapped({'urllib.request.OpenerDirector.open': _urllib_open_wrapper})
        super(UrllibInstrumentor, self).run()
