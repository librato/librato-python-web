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
from contextlib import contextmanager
import six
import unittest
from librato_python_web.api import context

from librato_python_web.instrumentor.telemetry import generate_record_telemetry, TestTelemetryReporter
from librato_python_web.instrumentor import instrument, util
from librato_python_web.instrumentor.instrument import get_generator_wrapper
from librato_python_web.instrumentor import telemetry


class A(object):
    value = None

    def set_value(self, v):
        self.value = v

    def get_value(self):
        return self.value

    def foo(self):
        return 'foo'


class InstrumentTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_class_by_name(self):
        class_name = ".".join([A.__module__, A.__name__])
        a_class = instrument.get_class_by_name(class_name)
        self.assertEqual(A, a_class)

    def test_replace_method(self):
        a = A()
        self.assertEqual('foo', a.foo())

        original = a.foo
        try:
            util.replace_method(A, 'foo', lambda v: 'bar')
            self.assertEqual('bar', a.foo())
        finally:
            util.replace_method(A, 'foo', original)
        self.assertEqual('foo', a.foo())

    def test_replace_wrapper(self):
        a = A()
        self.assertEqual('foo', a.foo())

        original = a.foo
        try:
            util.replace_method(A, 'foo', lambda v: 'bar')
            self.assertEqual('bar', a.foo())
        finally:
            util.replace_method(A, 'foo', original)
        self.assertEqual('foo', a.foo())

    def test_generator_wrapper(self):
        reporter = TestTelemetryReporter()
        telemetry.set_reporter(reporter)

        range_max = 10

        def generator():
            for g in range(range_max):
                yield g

        wrapped_generator = get_generator_wrapper(generate_record_telemetry('test.'), state='model', enable_if=None)

        i = j = 0
        for i in wrapped_generator(generator):
            self.assertEqual(j, i)
            j += 1
        self.assertEqual(range_max - 1, i)

        self.assertLessEqual(0, reporter.get_record('test.latency'))
        self.assertEqual(1, reporter.get_count('test.requests'))

        reporter.record('test.latency', 0)

        wrapped_generator = get_generator_wrapper(generate_record_telemetry('test.'), state='model', enable_if=None)

        def trigger_generator_exit():
            # trigger the GeneratorExit when this goes out of scope
            iterator = wrapped_generator(generator)
            six.next(iterator)

        trigger_generator_exit()

        self.assertLessEqual(0, reporter.get_record('test.latency'))
        self.assertEqual(2, reporter.get_count('test.requests'))

if __name__ == '__main__':
    unittest.main()
