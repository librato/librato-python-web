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


from librato_python_web.instrumentor.instrument import get_complex_wrapper
from librato_python_web.instrumentor.objproxies import ObjectWrapper
from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor


class WrappedCursor(ObjectWrapper):
    """ Wraps native cursor class to permit instrumentation """
    """ Native class methods can't be instrumented in-place """
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


class ConnWrapper(ObjectWrapper):
    """ Wraps native connection class to permit instrumentation """
    def cursor(self):
        cursor = self.__subject__.cursor()
        return WrappedCursor(cursor)


def wrapped_connect(func, *args, **kwargs):
    """ Returns a wrapped connection which intercepts cursor() """
    conn = func(*args, **kwargs)
    return ConnWrapper(conn)


class SqliteInstrumentor(BaseInstrumentor):
    modules = {'sqlite3': []}

    def __init__(self):
        super(SqliteInstrumentor, self).__init__()

    def run(self):
        # Instrument our wrapper connection class
        meths = {
            'librato_python_web.instrumentor.data.sqlite.WrappedCursor.' + m:
                get_complex_wrapper('data.sqlite.%s.' % m, state='data.sqlite', disable_if='model')

            for m in ['execute', 'executemany', 'fetchone', 'fetchmany', 'fetchall']
        }

        # Instrument connect method
        meths['sqlite3.connect'] = wrapped_connect

        self.set_wrapped(meths)
        super(SqliteInstrumentor, self).run()
