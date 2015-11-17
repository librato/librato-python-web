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


import unittest
from librato_python_web.instrumentor import instrument


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
        a_class = instrument.get_class_by_name('instrument_test.A')
        self.assertEqual(A, a_class)

    def test_replace_method(self):
        a = A()
        self.assertEqual('foo', a.foo())

        original = a.foo
        try:
            instrument.replace_method(A, 'foo', lambda v: 'bar')
            self.assertEqual('bar', a.foo())
        finally:
            instrument.replace_method(A, 'foo', original)
        self.assertEqual('foo', a.foo())

    def test_function_wrapper(self):
        instrument.context_function_wrapper_factory(None)
        a = A()
        self.assertEqual('foo', a.foo())

        original = a.foo
        try:
            instrument.replace_method(A, 'foo', lambda v: 'bar')
            self.assertEqual('bar', a.foo())
        finally:
            instrument.replace_method(A, 'foo', original)
        self.assertEqual('foo', a.foo())
