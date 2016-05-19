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

import inspect

from librato_python_web.instrumentor.instrument import get_complex_wrapper
from librato_python_web.instrumentor.objproxies import ObjectWrapper
from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor


class WrappedCursor(ObjectWrapper):
    """ Wraps native cursor class to permit instrumentation """
    """ Native class methods can't be instrumented in-place """
    def callproc(self, *args, **kwargs):
        return self.__subject__.callproc(*args, **kwargs)

    def execute(self, *args, **kwargs):
        return self.__subject__.execute(*args, **kwargs)

    def executemany(self, *args, **kwargs):
        return self.__subject__.executemany(*args, **kwargs)

    def fetchone(self, *args, **kwargs):
        return self.__subject__.fetchone(*args, **kwargs)

    def fetchmany(self, *args, **kwargs):
        return self.__subject__.fetchmany(*args, **kwargs)

    def fetchall(self, *args, **kwargs):
        return self.__subject__.fetchall(*args, **kwargs)

    def nextset(self, *args, **kwargs):
        return self.__subject__.nextset(*args, **kwargs)


class ConnWrapper(ObjectWrapper):
    """ Wraps native connection class to permit instrumentation """
    def cursor(self):
        cursor = self.__subject__.cursor()
        return WrappedCursor(cursor)


def wrapped_connect(func, *args, **kwargs):
    """ Returns a wrapped connection which intercepts cursor() """
    conn = func(*args, **kwargs)
    return ConnWrapper(conn)


class Psycopg2Instrumentor(BaseInstrumentor):
    modules = {'psycopg2': ['connect'], 'psycopg2.extensions': ['connection', 'cursor']}

    def __init__(self):
        super(Psycopg2Instrumentor, self).__init__()

    def run(self):
        """ Instruments our cursor wrapper class and psycopg2.connect """

        # Generate a list of methods in the cursor wrapper
        meth_names = [n for (n, _) in inspect.getmembers(WrappedCursor) if '_' not in n]

        meths = {
            'librato_python_web.instrumentor.data.psycopg2.WrappedCursor.' + m:
                get_complex_wrapper('data.psycopg2.%s.' % m, state='data.psycopg2', disable_if='model')
            for m in meth_names
           }

        # Instrument connect method
        meths['psycopg2.connect'] = wrapped_connect

        self.set_wrapped(meths)
        super(Psycopg2Instrumentor, self).run()
