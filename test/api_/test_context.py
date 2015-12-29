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

from librato_python_web.api.context import push_tag, pop_tag, add_tag, get_tags, add_all_tags


def run():
    print "running"


class ImportTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_pushPop(self):
        push_tag('foo', 1)
        pop_tag()

        push_tag('foo', 1)
        push_tag('bar', 2)
        self.assertListEqual([('foo', 1), ('bar', 2)], get_tags())
        pop_tag()
        pop_tag()
        self.assertListEqual([], get_tags())

    def test_pushPopTooMuch(self):
        with self.assertRaises(IndexError):
            push_tag('foo', 1)
            pop_tag()
            pop_tag()

    def test_set(self):
        with add_all_tags([('foo', 1)]):
            visited = True
            self.assertListEqual([('foo', 1)], get_tags())
        self.assertListEqual([], get_tags())
        self.assertTrue(visited)

        visited = False
        self.assertFalse(visited)
        with add_tag('foo', 1):
            self.assertListEqual([('foo', 1)], get_tags())
            with add_tag('bar', 2):
                visited = True
                self.assertListEqual([('foo', 1), ('bar', 2)], get_tags())
            self.assertListEqual([('foo', 1)], get_tags())
        self.assertTrue(visited)
        self.assertListEqual([], get_tags())

if __name__ == '__main__':
    unittest.main()