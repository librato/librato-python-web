# Copyright (c) 2016. Librato, Inc.
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


from librato_python_web.instrumentor.objproxies import ObjectProxy, ObjectWrapper
import unittest


class dummy(object):
    pass


class annotator(ObjectWrapper):
    def label(self):
        return 'nice'


class ObjectProxiesTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_proxy_type(self):
        p = ObjectProxy(1)

        self.assertTrue(isinstance(p, int))
        self.assertEqual(p.__class__, int)

        self.assertNotEqual(type(p), type(1))

    def test_proxy_attr(self):
        p = ObjectProxy(1)
        self.assertTrue(hasattr(p, '__subject__'))

    def test_proxy_delegation(self):
        subject = dummy()
        p = ObjectProxy(subject)
        self.assertTrue(hasattr(p, '__subject__'))
        self.assertEqual(p.__subject__, subject)

        p.foo = 'bar'

        self.assertTrue(hasattr(p, 'foo'))
        self.assertEqual(p.foo, 'bar')

        self.assertTrue(hasattr(subject, 'foo'))
        self.assertEqual(subject.foo, 'bar')

    def test_proxy_ops(self):
        p = ObjectProxy(42)

        self.assertEqual(p, 42)
        self.assertEqual(2*p, 84)

        self.assertEqual(hex(p), '0x2a')
        self.assertEqual(chr(p), '*')

    def test_wrapper_type(self):
        p = ObjectWrapper(1)

        self.assertTrue(isinstance(p, ObjectProxy))
        self.assertEqual(p.__class__, int)

    def test_wrapper_attr(self):
        p = annotator(5)

        self.assertEqual(p, 5)
        self.assertTrue(isinstance(p, int))
        self.assertEqual(p.__class__, int)
        self.assertEqual(2*p, 10)

        self.assertTrue(hasattr(p, 'label'))
        self.assertEqual(p.label(), 'nice')

        self.assertFalse(hasattr(p.__subject__, 'label'))


if __name__ == '__main__':
    unittest.main()


if __name__ == '__main__':
    unittest.main()
