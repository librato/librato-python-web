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

from collections import defaultdict
import inspect
import unittest
import sys
import time

from librato_python_web.instrumentor.util import Timing
from librato_python_web.instrumentor import telemetry
from librato_python_web.instrumentor.data.psycopg2 import Psycopg2Instrumentor
from librato_python_web.instrumentor.instrument import contextmanager_wrapper_factory, OverrideWrapper
from librato_python_web.instrumentor.telemetry import telemetry_context_manager, TestTelemetryReporter


def wrap_class(cls, methods=None):
    def __new__(wrapper_cls, *args, **kwargs):
        self = object.__new__(wrapper_cls)
        return self

    def __init__(self, *args, **kwargs):
        object.__setattr__(self, '__wrapped__', cls(*args, **kwargs))

    def __getattribute__(self, name):
        if name in {'__wrapped__'} or hasattr(self, name):
            try:
                return object.__getattribute__(self, name)
            except:
                return None
        else:
            return getattr(self.__wrapped__, name)

    o = {
        '__new__': __new__,
        '__init__': __init__,
        '__getattribute__': __getattribute__,
        # '__setattr__': object.__setattr__,
        'this_is_a_proxy': True
    }

    def wrap(f):
        def decorator2(self, *args, **kwargs):
            try:
                return f(self.__wrapped__, *args, **kwargs)
            finally:
                pass

        return decorator2

    for m in inspect.getmembers(cls):
        name = m[0]
        value = m[1]

        if name in o:
            pass
        else:
            if inspect.isfunction(value) or inspect.ismethod(value) or inspect.ismethoddescriptor(value) or \
                    inspect.isbuiltin(value):
                if methods is None or name in methods:
                    member_wrap = methods.get(name, wrap) if methods else wrap
                    o[name] = member_wrap(value)
                elif name not in {'__new__'}:
                    o[name] = wrap(value)
                else:
                    o[name] = value  # Keep new
            # for every attribute, create a property
            elif name not in {'__wrapped__'}:
                def set_it(self, v):
                    setattr(self, name, v)

                def get_it(self):
                    return getattr(self, name)

                def del_it(self):
                    delattr(self, name)

                    # print 'property', name, type(value), value
                    # o[name] = property(get_it, set_it, del_it, 'The %s property' % name)
            else:
                pass

    t = type(cls.__name__, (object,), o)
    t.__module__ = cls.__module__
    return t


LOCAL_DSN = "user=postgres password=postgres host=127.0.0.1 port=5432 dbname=test"


class UtilTest(unittest.TestCase):
    def setUp(self):
        import psycopg2
        self.state = defaultdict(int)
        self.cached = (psycopg2.connect, psycopg2.extensions.connection, psycopg2.extensions.cursor)

    def tearDown(self):
        import psycopg2
        (psycopg2.connect, psycopg2.extensions.connection, psycopg2.extensions.cursor) = self.cached

    def test_historically_named_timing(self):
        Timing.push_timer()
        time.sleep(0.1)
        Timing.push_timer()
        time.sleep(0.1)
        self.assertAlmostEqual(0.1, Timing.pop_timer()[0], delta=0.03)
        self.assertAlmostEqual(0.2, Timing.pop_timer()[0], delta=0.03)

    def test_stack_timing(self):
        times = 10

        Timing.push_timer()
        time.sleep(0.1)

        for i in range(times):
            Timing.push_timer()
            time.sleep(0.1)
            t, _ = Timing.pop_timer()
            self.assertAlmostEqual(0.1, t, delta=0.03)

        elapsed_time, net_time = Timing.pop_timer()

        self.assertAlmostEqual(0.1 + times * 0.1, elapsed_time, delta=0.03)
        self.assertAlmostEqual(0.1, net_time, delta=0.03)

    def test_default_class(self):
        class AttrEcho(object):
            def __init__(self):
                pass

            def foo(*args):
                return 1

        ae = AttrEcho()
        self.assertEqual(ae.foo(1), 1)

    def test_basic_class(self):
        class AttrEcho(object):
            def __init__(self):
                pass

            def __getattribute__(self, item):
                return item

        ae = AttrEcho()
        self.assertEqual(ae.foo, 'foo')
        self.assertEqual(ae.bar, 'bar')

    def test_basic_type(self):
        def __getattribute__(self, item):
            return item

        AttrEchoType = type('AttrEchoType', (object,), {'__getattribute__': __getattribute__})

        ae = AttrEchoType()
        self.assertEqual(ae.foo, 'foo')
        self.assertEqual(ae.bar, 'bar')

    def test_adv_type(self):
        def __getattribute__(self, item):
            if item in {'__wrapped__'}:
                return object.__getattribute__(self, item)
            else:
                return getattr(self.__wrapped__, item)

        class AttrEcho(object):
            def __init__(self):
                self.foo = 'foo'
                self.bar = 'bar'

        AttrEchoType = type('AttrEchoType', (object,), {'__getattribute__': __getattribute__})

        ae = AttrEchoType()
        ae.__wrapped__ = AttrEcho()
        self.assertEqual(ae.foo, 'foo')
        self.assertEqual(ae.bar, 'bar')

    def test_all_adv_type(self):
        class AttrEcho(object):
            def __init__(self):
                self.foo = 'foo'
                self.bar = 'bar'

            def get_self(self):
                return self

            def get_foo(self):
                return self.foo

            def get_bar(self):
                return self.bar

            def always_one(self):
                return 1

            def echo(self, value):
                return value

        wrapped_class = AttrEcho

        AttrEchoType = self.wrap_instance(wrapped_class)

        ae = AttrEchoType()
        self.assertEqual(ae.foo, 'foo')
        self.assertEqual(ae.bar, 'bar')
        self.assertEqual(ae.get_foo(), 'foo')
        self.assertEqual(ae.get_bar(), 'bar')
        self.assertNotEqual(ae.get_self(), ae)
        self.assertEqual(ae.always_one(), 1)
        self.assertEqual(ae.echo(123), 123)

    def wrap_instance(self, wrapped_class):
        def __init__(self, *args, **kwargs):
            self.__wrapped__ = wrapped_class(*args, **kwargs)

        def __getattribute__(self, name):
            if name == '__wrapped__':
                return object.__getattribute__(self, name)
            else:
                return getattr(self.__wrapped__, name)

        def __setattr__(self, name, value):
            if name == '__wrapped__':
                object.__setattr__(self, '__wrapped__', value)
            else:
                return setattr(self.__wrapped__, name, value)

        def __delattr__(self, name):
            if name == '__wrapped__':
                object.__delattr__(self, '__wrapped__')
            else:
                return delattr(self.__wrapped__, name)

        o = {k: v for k, v in inspect.getmembers(wrapped_class) if k != '__new__' and inspect.isfunction(v)}
        o['__init__'] = __init__
        o['__getattribute__'] = __getattribute__
        o['__setattr__'] = __setattr__
        o['__delattr__'] = __delattr__
        AttrEchoType = type('AttrEchoType', (object,), o)
        return AttrEchoType

    def test_all_adv_type_native(self):
        import psycopg2
        wrapped_class = psycopg2.extensions.connection

        wrapped_connection = self.wrap_instance(wrapped_class)

        conn = wrapped_connection(LOCAL_DSN)
        self.assertIsNotNone(conn)

        cursor = conn.cursor()
        self.assertIsNotNone(cursor)
        cursor.execute("SELECT 1")
        val = cursor.fetchone()
        self.assertEqual((1,), val)
        cursor.execute("SELECT 1, 2")
        val = cursor.fetchone()
        self.assertEqual((1, 2), val)

    def test_subclass_native_class(self):
        import psycopg2

        class MyConnection(psycopg2.extensions.connection):
            def __init__(self, *args, **keywords):
                super(MyConnection, self).__init__(*args, **keywords)

            def cursor(self, *args, **keywords):
                c = super(MyConnection, self).cursor(*args, **keywords)
                return c

        conn = MyConnection(LOCAL_DSN)
        cur = conn.cursor()
        cur.execute("SELECT 1")

    def test_replace_native_class(self):
        import psycopg2

        class MyConnection(psycopg2.extensions.connection):
            def __init__(self, *args, **keywords):
                super(MyConnection, self).__init__(*args, **keywords)

            def cursor(self, *args, **keywords):
                c = super(MyConnection, self).cursor(*args, **keywords)
                return c

        psycopg2.extensions.connection = MyConnection

        conn = psycopg2.extensions.connection(LOCAL_DSN)
        cur = conn.cursor()
        cur.execute("SELECT 1")

    def test_replace_native_class_type(self):
        import psycopg2

        state = {}

        def cursor(self, *args, **keywords):
            state['before'] = True
            c = super(self.__class__, self).cursor(*args, **keywords)
            state['after'] = True
            return c

        psycopg2.extensions.connection = type('connection', (psycopg2.extensions.connection,), {'cursor': cursor})

        conn = psycopg2.extensions.connection(LOCAL_DSN)
        cur = conn.cursor()
        self.assertTrue(state['before'])
        self.assertTrue(state['after'])
        cur.execute("SELECT 1")
        self.assertEqual((1,), cur.fetchone())
        cur.execute("SELECT 1, 2")
        self.assertEqual((1, 2), cur.fetchone())

    def test_override_native_class_type(self):
        import psycopg2

        state = {}

        def wrap(f):
            def decorator(self, *args, **keywords):
                state['before'] = True
                c = f(self, *args, **keywords)
                state['after'] = True
                return c

            return decorator

        def override_class_methods(cls, method_names):
            methods = {m: wrap(getattr(cls, m)) for m in method_names}
            methods['__isproxy__'] = True  # temporary
            sub_class = type(cls.__name__, (cls,), methods)
            sub_class.__module__ = cls.__module__
            setattr(sys.modules[cls.__module__], cls.__name__, sub_class)

        override_class_methods(psycopg2.extensions.connection, ['cursor'])

        conn = psycopg2.extensions.connection(LOCAL_DSN)
        cur = conn.cursor()
        self.assertTrue(state['before'])
        self.assertTrue(state['after'])
        cur.execute("SELECT 1")
        self.assertEqual((1,), cur.fetchone())
        cur.execute("SELECT 1, 2")
        self.assertEqual((1, 2), cur.fetchone())

    def test_proxy_native_instance(self):
        import psycopg2
        from librato_python_web.instrumentor.objproxies import ObjectWrapper

        state = {}

        def wrap(f):
            def decorator(self, *args, **keywords):
                state['before'] = True
                c = f(self, *args, **keywords)
                state['after'] = True
                return ObjectWrapper(c) if hasattr(c, '__class__') else c

            return decorator

        def override_class_methods(cls, method_names):
            methods = {m: wrap(getattr(cls, m)) for m in method_names}
            methods['__isproxy__'] = True  # temporary
            sub_class = type(cls.__name__, (cls,), methods)
            sub_class.__module__ = cls.__module__
            setattr(sys.modules[cls.__module__], cls.__name__, sub_class)

        override_class_methods(psycopg2.extensions.connection, ['cursor'])

        self.assertTrue(psycopg2.extensions.connection.__isproxy__)
        conn = psycopg2.extensions.connection(LOCAL_DSN)
        cur = conn.cursor()
        self.assertTrue(state['before'])
        self.assertTrue(state['after'])

        self.assertEquals(ObjectWrapper, type(cur))
        cur.execute("SELECT 1")
        self.assertEqual((1,), cur.fetchone())
        cur.execute("SELECT 1, 2")
        self.assertEqual((1, 2), cur.fetchone())

    def test_override_proxy_native_instance(self):
        import psycopg2
        from librato_python_web.instrumentor.objproxies import ObjectWrapper

        state = defaultdict(int)

        class MeasureWrapper(ObjectWrapper):
            def __init__(self, subject, measured_methods={}):
                super(MeasureWrapper, self).__init__(subject)
                object.__setattr__(self, '__measured_methods__', set(measured_methods))

            def __getattr__(self, attr, oga=object.__getattribute__):
                if not attr.startswith('__') and attr in object.__getattribute__(self, '__measured_methods__'):
                    try:
                        t = time.clock()
                        return super(MeasureWrapper, self).__getattr__(attr, oga)
                    finally:
                        net_t = time.clock() - t
                        state[attr] += net_t
                else:
                    return super(MeasureWrapper, self).__getattr__(attr, oga)

        def wrap(f, measured_methods=[]):
            def decorator(self, *args, **keywords):
                c = f(self, *args, **keywords)
                return MeasureWrapper(c, measured_methods) if hasattr(c, '__class__') else c

            return decorator

        def override_class_methods(cls, method_names):
            methods = {m: wrap(getattr(cls, m), ['execute', 'fetchone']) for m in method_names}
            methods['__isproxy__'] = True  # temporary
            sub_class = type(cls.__name__, (cls,), methods)
            sub_class.__module__ = cls.__module__
            setattr(sys.modules[cls.__module__], cls.__name__, sub_class)

        override_class_methods(psycopg2.extensions.connection, ['cursor'])

        self.assertTrue(psycopg2.extensions.connection.__isproxy__)
        conn = psycopg2.extensions.connection(LOCAL_DSN)
        cur = conn.cursor()

        self.assertEquals(MeasureWrapper, type(cur))
        cur.execute("SELECT 1")
        self.assertEqual((1,), cur.fetchone())
        cur.execute("SELECT 1, 2")
        self.assertEqual((1, 2), cur.fetchone())

        self.assertLess(0, state['execute'])
        self.assertLess(0, state['fetchone'])

    def test_instrumented_proxy_native_instance(self):
        import psycopg2
        from objproxies import ObjectWrapper

        class MeasureWrapper(ObjectWrapper):
            def __init__(self, subject, measured_methods, metric_name, state_name, enable_if, disable_if):
                super(MeasureWrapper, self).__init__(subject)

                # initialize all wrapped methods
                instrumented = {}
                for m in [m for m in inspect.getmembers(subject) if measured_methods is None or
                          m[0] in measured_methods]:
                    name = m[0]
                    factory = contextmanager_wrapper_factory(telemetry_context_manager(metric_name % name),
                                                             {}, state_name, enable_if, disable_if)
                    instrumented[name] = factory(m[1])
                object.__setattr__(self, '__instrumented__', instrumented)

            def __getattr__(self, attr, oga=object.__getattribute__):
                if not attr.startswith('__'):
                    instrumented = object.__getattribute__(self, '__instrumented__')
                    if attr in instrumented:
                        return instrumented.get(attr)
                return super(MeasureWrapper, self).__getattr__(attr, oga)

        def wrap(f, measured_methods, metric_name, state_name, enable_if, disable_if):
            def decorator(*args, **keywords):
                c = f(*args, **keywords)
                return MeasureWrapper(c, measured_methods, metric_name, state_name, enable_if, disable_if) \
                    if hasattr(c, '__class__') else c

            return decorator

        def override_class_methods(cls, method_names, metric_name, state_name, enable_if, disable_if):
            methods = {m: wrap(getattr(cls, m), ['execute', 'fetchone'], metric_name, state_name, enable_if,
                               disable_if) for m in method_names}
            methods['__isproxy__'] = True  # temporary?
            sub_class = type(cls.__name__, (cls,), methods)
            sub_class.__module__ = cls.__module__
            setattr(sys.modules[cls.__module__], cls.__name__, sub_class)

        telemetry_reporter = TestTelemetryReporter()
        telemetry.set_reporter(telemetry_reporter)

        # Override native class factory methods to wrapped returned objects
        override_class_methods(psycopg2.extensions.connection, ['cursor'], 'data.psycopg2.%s.', 'data', None, 'model')

        self.assertTrue(psycopg2.extensions.connection.__isproxy__)
        conn = psycopg2.extensions.connection(LOCAL_DSN)
        cur = conn.cursor()

        self.assertEquals(MeasureWrapper, type(cur))
        cur.execute("SELECT 1")
        self.assertEqual((1,), cur.fetchone())
        cur.execute("SELECT 1, 2")
        self.assertEqual((1, 2), cur.fetchone())

        self.assertIn('data.psycopg2.execute.latency', telemetry_reporter.records)
        self.assertIn('data.psycopg2.fetchone.latency', telemetry_reporter.records)

    def test_instrument_native_connect(self):
        import psycopg2

        instrumentor = Psycopg2Instrumentor()
        instrumentor.run()

        conn = psycopg2.connect(LOCAL_DSN)
        self._instrument_native_instance(conn)

    def test_instrument_native_class(self):
        import psycopg2

        instrumentor = Psycopg2Instrumentor()
        instrumentor.run()

        conn = psycopg2.extensions.connection(LOCAL_DSN)
        self._instrument_native_instance(conn)

    def _instrument_native_instance(self, conn):
        telemetry_reporter = TestTelemetryReporter()
        telemetry.set_reporter(telemetry_reporter)

        cur = conn.cursor()

        cur.execute("SELECT 1")
        self.assertEqual((1,), cur.fetchone())
        cur.execute("SELECT 1, 2")
        self.assertEqual((1, 2), cur.fetchone())

        self.assertIn('data.psycopg2.execute.latency', telemetry_reporter.records)
        self.assertIn('data.psycopg2.fetchone.latency', telemetry_reporter.records)

    def test_fako(self):
        class Simple(object):
            def __init__(self):
                self.foo = 1
                self.bar = "barvalue"

            def zap(self, target):
                return "zapped %s" % target

        class Fako(OverrideWrapper):
            def __init__(self, subject, overrides):
                super(Fako, self).__init__(subject, overrides)

            def __new__(cls, *args, **kwargs):
                cls = args[0].__class__
                t = type(cls.__name__, (Fako,), {'__doc__': cls.__doc__})
                return object.__new__(t)

        simple = Simple()
        self.assertEquals(1, simple.foo)
        self.assertEquals('barvalue', simple.bar)
        self.assertEquals('zapped me', simple.zap('me'))
        self.assertEquals(Simple, type(simple))

        simple = Fako(simple, {})
        self.assertEquals(1, simple.foo)
        self.assertEquals('barvalue', simple.bar)
        self.assertEquals('zapped me', simple.zap('me'))

if __name__ == '__main__':
    unittest.main()
