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
import functools
import time
from peak.util.proxies import ObjectWrapper
import six
import sys

from librato_python_web.instrumentor import context
from librato_python_web.instrumentor.custom_logging import getCustomLogger
from librato_python_web.instrumentor.util import wraps, is_class_available, get_class_by_name, wrap_method

logger = getCustomLogger(__name__)


def run_instrumentors(instrumentors, libs):
    """
    :param instrumentors:
    :param libs:
    """
    for alias in instrumentors:
        if alias not in libs:
            logger.info("Skipping %s", alias)
            continue

        try:
            logger.info("Instrumenting %s", alias)
            instrumentor = instrumentors[alias]
            try:
                for class_name in instrumentor.required_class_names:
                    if not is_class_available(class_name):
                        logger.info('required instrumentor class not available %s', class_name)
                        break
                else:
                    # All required classes were available
                    logger.info('running instrumentor: %s', instrumentor.__name__)
                    instrumentor().run()
            except:
                # if something goes wrong, keep going, don't destroy the app!
                logger.exception('problem initializing instrumentor: %s', instrumentor)
        except:
            # if something goes wrong, keep going, don't destroy the app!
            logger.exception('problem initializing instrumentor: %s', alias)


def instrument_methods(method_wrappers):
    """
    Instruments the methods as specified by the method_wrappers dict. Keys indicate the method path and values provide
    the function that wraps the method.
    :param method_wrappers: dictionary of paths to
    """
    for method_path, method_wrapper in six.iteritems(method_wrappers):
        (fully_qualified_class_name, method_name) = method_path.rsplit('.', 1)
        try:
            class_def = get_class_by_name(fully_qualified_class_name)
            if class_def:
                logger.debug('instrumenting method %s', method_path)
                wrap_method(class_def, method_name, method_wrapper)
            else:
                logger.info('%s not instrumented because not found', fully_qualified_class_name)
        except ImportError:
            logger.debug('could not instrument %s.%s', method_path, method_name)
            logger.info('%s not instrumented because not found', fully_qualified_class_name)
        except AttributeError:
            logger.warn('could not instrument %s.%s', method_path, method_name)


def override_classes(overridden_classes, wrapped):
    """
    Override static classes by creating a subclass (via type) that contains overridden methods. Typically this is
    applied to native classes so that their methods can be overridden to wrap returned instances.
    :param overridden_classes: dict of qualified class names as keys and
    """
    for fully_qualified_class_name, targeted_methods in six.iteritems(overridden_classes):
        try:
            cls = get_class_by_name(fully_qualified_class_name)
            if cls:
                logger.debug('instrumenting class %s', fully_qualified_class_name)
                wrap_class_methods(cls, targeted_methods, wrapped)
            else:
                logger.info('%s not overridden because not found', fully_qualified_class_name)
        except ImportError:
            logger.debug('could not override %s', fully_qualified_class_name)
            logger.info('%s not overridden because not found', fully_qualified_class_name)


def wrap_returned_instances(original_method, overrides):
    """
    Creates a new method that calls the original_method and, if an instance is returned, creates a proxy wrapper for
    them that uses the new_methods (other calls are proxied to the original instance).
    :param original_method: the original method
    :param overrides: new methods on instances returned from this method
    :return: the wrapped version of the original method
    """
    def decorator(*args, **keywords):
        """
        :return: proxied version of instances returned
        """
        ret = original_method(*args, **keywords)
        return OverrideWrapper(ret, {k: functools.partial(v, ret) for k, v in overrides.iteritems()}) \
            if hasattr(ret, '__class__') else ret
    return decorator


def wrap_class_methods(cls, targeted_methods, rules):
    overrides = {}
    for targeted_method, method_config in six.iteritems(targeted_methods):
        """Each wrapped method is modified to return an wrapped object with methods instrumented according to rules"""
        original_method = getattr(cls, targeted_method)
        return_type = method_config.get('returns')
        if return_type:
            # Create a custom wrapper based upon the return type of the method
            return_cls = get_class_by_name(return_type)
            pf_len = len(return_type)+1
            return_type_proxy_methods = {k[pf_len:]: v(object.__getattribute__(return_cls, k[pf_len:]))
                                         for k, v in six.iteritems(rules) if k.startswith(return_type) and
                                         hasattr(return_cls, k[pf_len:])}
            overrides[targeted_method] = wrap_returned_instances(original_method, return_type_proxy_methods)
        else:
            logger.error('method %s missing returns value', targeted_method)
    sub_class = type(cls.__name__, (cls,), overrides)
    sub_class.__module__ = cls.__module__
    setattr(sys.modules[cls.__module__], cls.__name__, sub_class)


def _build_key(mappings, args, keywords):
    """
    :param mappings:
    :param args:
    :param keywords:
    :return: list of key-value pairs for naming
    """
    values = []
    for key in mappings or []:
        expression = mappings.get(key)
        value = _eval(args, keywords, expression)
        if value is not None:
            values.append((key, value))
    return values


def _eval(args, keywords, expressions):
    """
    Returns the value of the given expressions as applied against the args and keywords.

    Expressions are pipe-delimited values which represent alternatives. Numeric values are used a indicies
    :param args: the array of method arguments
    :param keywords: the dictionary of keywords
    :param expressions:
    :return:
    """
    final_failure = Exception
    if expressions is None:
        return None
    for expression in expressions.split('|') if isinstance(expressions, basestring) else [expressions]:
        try:
            if isinstance(expression, (int, long)):
                value = args[expression]
            elif expression.startswith('self'):
                v = {'self': args[0]}
                for k in expression.split('.'):
                    v = v.get(k) if hasattr(v, 'get') else getattr(v, k)
                    if v is None:
                        raise 'Missing value %s encountered in %s' % (k, expression)
                value = v
            elif expression[0].isdigit():
                v = args
                for k in expression.split('.'):
                    if k.isdigit():
                        v = v[int(k)]
                    else:
                        v = v.get(k) if hasattr(v, 'get') else getattr(v, k)
                    if v is None:
                        raise 'Missing value %s encountered in %s' % (k, expression)
                value = v
            else:
                value = keywords[expression]
            return value
        except (IndexError, KeyError) as e:
            # fall through to here when missing value causes an error, let loop try other possibilities if any
            final_failure = e
    raise final_failure


def _should_be_instrumented(state, enable_if, disable_if):
    """
    Returns False if the method should not be instrumented given the current state. Any value can be None to indicate
    no change.

    :param state: the new state
    :param enable_if: enable instrumentation iff this state is present
    :param disable_if: disable instrumentation iff this state is present
    :return: True if rules indicate this should be instrumented, false otherwise
    """
    if enable_if and not context.has_state(enable_if):
        logger.debug('skipping %s instrumentation, lacks enable_if=%s', state, enable_if)
        return False

    if disable_if and context.has_state(disable_if):
        logger.debug('skipping %s instrumentation, has disable_if=%s', state, disable_if)
        return False

    if state and context.has_state(state):
        logger.debug('skipping instrumentation, state=%s already present', state)
        return False
    return True


def function_wrapper_factory(wrapper_function, state=None, enable_if='web', disable_if=None):
    """
    Generates a function that wraps a function so that it uses the context_manager around it.

    :param wrapper_function: the function used to wrap functions provided to the factory
    :param state: the state associated with the wrapped method
    :param enable_if: instrumentation is only enabled when this state is present
    :param disable_if: instrumentation is disabled when this state is present
    :return: the function wrapper
    """

    def decorator(f):
        """
        Functions are only wrapped when instrumentation is required, based on run-time context
        :param f: the function to wrap
        """

        @wraps(f)
        def wrapper(*args, **keywords):
            if _should_be_instrumented(state, enable_if, disable_if):
                try:
                    context.push_state(state)
                    return wrapper_function(f)(*args, **keywords)
                finally:
                    context.pop_state(state)
            else:
                return f(*args, **keywords)

        return wrapper

    return decorator


def generator_wrapper_factory(recorder, state=None, enable_if='web', disable_if=None):
    """
    Generates a function that wraps a function so that it uses the context_manager around it.

    :param recorder: the function used to wrap functions provided to the factory
    :param state: the state associated with the wrapped method
    :param enable_if: instrumentation is only enabled when this state is present
    :param disable_if: instrumentation is disabled when this state is present
    :return: the function wrapper
    """

    def decorator(generator):
        """
        Creates a generator that wraps the given generator and instruments it depending on the context when
        its called.
        :param generator: the generator to wrap
        """

        @wraps(generator)
        def wrapper(*args, **keywords):
            # determined at run time, since this depends on the invocation context
            if _should_be_instrumented(state, enable_if, disable_if):
                # wrap the initialization
                elapsed = 0
                context.push_state(state)
                t = time.time()
                try:
                    gen = generator(*args, **keywords)
                finally:
                    elapsed += time.time() - t
                    context.pop_state(state)
                try:
                    while True:
                        # wrap each successive value generation
                        context.push_state(state)
                        t = time.time()
                        try:
                            v = gen.next()
                        finally:
                            elapsed += time.time() - t
                            context.pop_state(state)
                        yield v
                finally:
                    # finish metrics (GeneratorExit or otherwise)
                    recorder(elapsed)
            else:
                for x in generator(*args, **keywords):
                    yield x

        return wrapper

    return decorator


def contextmanager_wrapper_factory(context_manager, mapping=None, state=None, enable_if='web', disable_if=None):
    """
    Generates a function that wraps a function so that it uses the context_manager around it and harvests
    the given prefix, keys, and suffix as context.

    :param context_manager: the contextmanager (optional, in which case context is pushed/popped around the call)
    :param mapping: the keys and expression values used to look up values from the method target and/or arguments
    :param state: the state associated with the wrapped method
    :param enable_if: instrumentation is only enabled when this state is present
    :param disable_if: instrumentation is disabled when this state is present
    :return: the function wrapper
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **keywords):
            if _should_be_instrumented(state, enable_if, disable_if):
                tag_pairs = _build_key(mapping, args, keywords)
                try:
                    context.push_state(state)
                    context.push_tags(tag_pairs)
                    with context_manager(*args, **keywords):
                        return f(*args, **keywords)
                finally:
                    context.pop_tags(tag_pairs)
                    context.pop_state(state)
            else:
                return f(*args, **keywords)

        return wrapper

    return decorator


class OverrideWrapper(ObjectWrapper):
    def __init__(self, subject, instrumented):
        super(OverrideWrapper, self).__init__(subject)
        object.__setattr__(self, '__instrumented__', instrumented)

    def __getattr__(self, attr, oga=object.__getattribute__):
        if not attr.startswith('__'):
            instrumented = object.__getattribute__(self, '__instrumented__')
            if attr in instrumented:
                return instrumented.get(attr)
        return super(OverrideWrapper, self).__getattr__(attr, oga)
