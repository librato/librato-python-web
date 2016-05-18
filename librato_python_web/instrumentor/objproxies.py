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


"""
Adapted from objproxies (https://pypi.python.org/pypi/objproxies/0.9.4) and
ProxyTypes (https://pypi.python.org/pypi/ProxyTypes).
Pruned and modified to work on Python 2 and 3.
"""


import sys
from six import exec_

_is_py2 = sys.version_info.major < 3


class AbstractProxy(object):
    """Delegates all operations (except ``.__subject__``) to another object"""
    __slots__ = ()

    def __call__(self, *args, **kw):
        return self.__subject__(*args, **kw)

    def __getattribute__(self, attr, oga=object.__getattribute__):
        subject = oga(self, '__subject__')
        if attr == '__subject__':
            return subject
        return getattr(subject, attr)

    def __setattr__(self, attr, val, osa=object.__setattr__):
        if attr == '__subject__':
            osa(self, attr, val)
        else:
            setattr(self.__subject__, attr, val)

    def __delattr__(self, attr, oda=object.__delattr__):
        if attr == '__subject__':
            oda(self, attr)
        else:
            delattr(self.__subject__, attr)

    if _is_py2:
        def __nonzero__(self):
            return bool(self.__subject__)
    else:
        def __bool__(self):
            return bool(self.__subject__)

    def __getitem__(self, arg):
        return self.__subject__[arg]

    def __setitem__(self, arg, val):
        self.__subject__[arg] = val

    def __delitem__(self, arg):
        del self.__subject__[arg]

    def __getslice__(self, i, j):
        return self.__subject__[i:j]

    def __setslice__(self, i, j, val):
        self.__subject__[i:j] = val

    def __delslice__(self, i, j):
        del self.__subject__[i:j]

    def __contains__(self, ob):
        return ob in self.__subject__

    for name in 'repr str hash len abs complex int long float iter oct hex'.split():
        exec_("def __%s__(self): return %s(self.__subject__)" % (name, name))

    for name in 'cmp', 'coerce', 'divmod':
        exec_("def __%s__(self, ob): return %s(self.__subject__, ob)" % (name, name))

    for name, op in [
            ('lt', '<'), ('gt', '>'), ('le', '<='), ('ge', '>='),
            ('eq', '=='), ('ne', '!=')
    ]:
        exec_("def __%s__(self, ob): return self.__subject__ %s ob" % (name, op))

    for name, op in [('neg', '-'), ('pos', '+'), ('invert', '~')]:
        exec_("def __%s__(self): return %s self.__subject__" % (name, op))

    for name, op in [
            ('or', '|'), ('and', '&'), ('xor', '^'), ('lshift', '<<'), ('rshift', '>>'),
            ('add', '+'), ('sub', '-'), ('mul', '*'), ('div', '/'), ('mod', '%'),
            ('truediv', '/'), ('floordiv', '//')
    ]:
        exec_((
            "def __%(name)s__(self, ob):\n"
            "    return self.__subject__ %(op)s ob\n"
            "\n"
            "def __r%(name)s__(self, ob):\n"
            "    return ob %(op)s self.__subject__\n"
            "\n"
            "def __i%(name)s__(self, ob):\n"
            "    self.__subject__ %(op)s=ob\n"
            "    return self\n"
        ) % locals())

    del name, op

    # Oddball signatures

    if not _is_py2:
        def __index__(self):
            return self.__subject__.__index__()

    def __rdivmod__(self, ob):
        return divmod(ob, self.__subject__)

    def __pow__(self, *args):
        return pow(self.__subject__, *args)

    def __ipow__(self, ob):
        self.__subject__ **= ob
        return self

    def __rpow__(self, ob):
        return pow(ob, self.__subject__)


class ObjectProxy(AbstractProxy):
    """Proxy for a specific object"""

    __slots__ = "__subject__"

    def __init__(self, subject):
        self.__subject__ = subject


class AbstractWrapper(AbstractProxy):
    """Mixin to allow extra behaviors and attributes on proxy instance"""
    __slots__ = ()

    def __getattribute__(self, attr, oga=object.__getattribute__):
        if attr.startswith('__'):
            subject = oga(self, '__subject__')
            if attr == '__subject__':
                return subject
            return getattr(subject, attr)
        return oga(self, attr)

    def __getattr__(self, attr, oga=object.__getattribute__):
        return getattr(oga(self, '__subject__'), attr)

    def __setattr__(self, attr, val, osa=object.__setattr__):
        if (
                attr == '__subject__' or
                hasattr(type(self), attr) and not attr.startswith('__')
        ):
            osa(self, attr, val)
        else:
            setattr(self.__subject__, attr, val)

    def __delattr__(self, attr, oda=object.__delattr__):
        if (
                attr == '__subject__' or
                hasattr(type(self), attr) and not attr.startswith('__')
        ):
            oda(self, attr)
        else:
            delattr(self.__subject__, attr)


class ObjectWrapper(ObjectProxy, AbstractWrapper):
    __slots__ = ()
