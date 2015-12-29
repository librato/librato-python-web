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
import time

from librato_python_web.instrumentor.util import AliasGenerator


class UtilTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_alias(self):
        aliases = AliasGenerator()
        a1 = aliases.generate_alias('/foo/bar/zap/1')

        self.assertEqual(a1, aliases.generate_alias('/foo/bar/zap/1'))

    def test_aliases(self):
        size = 10
        aliases = AliasGenerator(size)
        for i in range(0, size):
            aliases.generate_alias('/foo/bar/zap/%s' % i)
        aliases.generate_alias('/foo/bar/zap/%s' % (i+1))

        # White box test... is oldest entry in cache
        self.assertNotIn('/foo/bar/zap/%s' % 0, aliases.cache)
        self.assertIn('/foo/bar/zap/%s' % 1, aliases.cache)

    def test_time(self):
        aliases = AliasGenerator(1)
        t = time.time()
        for _ in range(0, 5000):
            for i in range(0, 100):
                aliases.generate_alias('/foo/bar/zap/%s' % i)
        print 'no cache', (time.time()-t)/500000

        aliases = AliasGenerator(200)
        # pre-cache
        for i in range(0, 100):
            aliases.generate_alias('/foo/bar/zap/%s' % i)

        t = time.time()
        for _ in range(0, 5000):
            for i in range(0, 100):
                aliases.generate_alias('/foo/bar/zap/%s' % i)
        print 'cache', (time.time()-t)/500000

if __name__ == '__main__':
    unittest.main()
