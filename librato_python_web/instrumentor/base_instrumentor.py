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

from .telemetry import default_instrumentation

from librato_python_web.instrumentor.instrument import instrument_methods, contextmanager_wrapper_factory, \
    override_classes

_default = object()


class BaseInstrumentor(object):
    def __init__(self, wrapped=None, state=None):
        self.wrapped = wrapped
        self.overridden_classes = {}
        self.state = state

    def set_overridden(self, overridden_classes):
        self.overridden_classes = overridden_classes if overridden_classes is not None else {}

    def set_wrapped(self, wrapped):
        self.wrapped = wrapped if wrapped is not None else {}

    def run(self):
        # instrument static resources
        override_classes(self.overridden_classes, self.wrapped)
        instrument_methods(self.wrapped)

    def instrument(self, metric_name, mapping=None, state=_default, enable_if='web', disable_if=None):
        state = self.get_state(state)
        return contextmanager_wrapper_factory(default_instrumentation(metric_name),
                                              mapping, state, enable_if, disable_if)

    def get_state(self, state=_default):
        try:
            return self.state if state == _default else state
        except:
            return state
