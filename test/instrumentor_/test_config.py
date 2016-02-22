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


import random
import unittest
import six

from librato_python_web.instrumentor.config import ConfigReporter


class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.config = ConfigReporter()

    def tearDown(self):
        pass

    def test_set_single(self):
        self.config.declare("foo", 1)
        self.assertEntry("foo", 1)

    def test_set_multiple(self):
        self.config.declare("foo.a", 1)
        self.assertEntry("foo.a", 1)
        self.config.declare("foo.b", 2)
        self.assertEntry("foo.b", 2)
        self.config.declare("foo.c", 3)
        self.assertEntry("foo.c", 3)
        self.config.declare("foo.c", 4)
        self.assertEntry("foo.c", 4)

    def test_set_array(self):
        self.config.declare("foo", [1, 2, 3])
        self.assertEntry("foo", [1, 2, 3])

    def assertEntry(self, name, value):
        actual = six.moves.reduce(lambda a, k: a.get(k), name.split('.'), self.config.config)
        self.assertEqual(value, actual)

    def test_hash(self):
        for i, k in enumerate('qwertyuiopasdfghjklzxcvbnm'):
            self.config.declare(k, i)
        hash_code = self.config.internal_hash()

        letters = list('qwertyuiopasdfghjklzxcvbnm')
        random.shuffle(letters)
        for i, k in enumerate(letters):
            self.config.declare(k, i)
        self.assertNotEqual(hash_code, self.config.internal_hash())

        enumerated = [p for p in enumerate(list('qwertyuiopasdfghjklzxcvbnm'))]
        random.shuffle(enumerated)
        for i, k in enumerated:
            self.config.declare(k, i)
        self.assertEqual(hash_code, self.config.internal_hash())

if __name__ == '__main__':
    unittest.main()
