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

import bootstrap    # Initialize instrumentation

import json
import unittest
import cherrypy
from test_helper import TestCaseBase

from librato_python_web.instrumentor import telemetry
from librato_python_web.instrumentor.telemetry import TestTelemetryReporter

import state_app


class StateTestCase(TestCaseBase):
    def setup_server():
        cherrypy.tree.mount(state_app.StateApp())
    setup_server = staticmethod(setup_server)

    def setUp(self):
        self.reporter = TestTelemetryReporter()
        telemetry.set_reporter(self.reporter)

    def tearDown(self):
        telemetry.set_reporter(None)

    def test_state(self):
        self.getPage('/')
        self.assertStatus(200)

        self.check_tags(self.reporter)

        states = json.loads(self.body.decode())
        print "State = %s" % states

        self.assertEqual(len(states), 2)
        self.assertIn('web', states)
        self.assertIn('wsgi', states)
        self.assertEqual(states['web'], 1)
        self.assertEqual(states['wsgi'], 1)

if __name__ == '__main__':
    unittest.main()
