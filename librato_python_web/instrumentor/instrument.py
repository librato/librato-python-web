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
import inspect
import time
import sys

import six

from librato_python_web.instrumentor.objproxies import ObjectWrapper
from librato_python_web.instrumentor import context
from librato_python_web.instrumentor.custom_logging import getCustomLogger
from librato_python_web.instrumentor.util import wraps, is_class_available, get_class_by_name, wrap_method

logger = getCustomLogger(__name__)


def run_instrumentors(instrumentors, libs):
    """
    Applies instrumentation to the given libs, using the given instrumentors.

    :param libs: list of libraries to be instrumented
    :param instrumentors: dictionary of instrumentors, where keys are names and values are instances
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
    Instruments the methods as specified by the method_wrappers dict. Key is the method path and value is the function
    that wraps the method.

    :param method_wrappers: dictionary of qualified method names to wrapper methods
    """
    for qualified_method_name, method_wrapper in six.iteritems(method_wrappers):
        (fully_qualified_class_name, method_name) = qualified_method_name.rsplit('.', 1)
        try:
            class_def = get_class_by_name(fully_qualified_class_name)
            if class_def:
                logger.debug('instrumenting method %s', qualified_method_name)
                wrap_method(class_def, method_name, method_wrapper)
            else:
                logger.warn('%s not instrumented because not found', fully_qualified_class_name)
        except ImportError:
            logger.debug('could not instrument %s', qualified_method_name)
            logger.warn('%s not instrumented because not found', fully_qualified_class_name)
        except AttributeError:
            logger.warn('could not instrument %s', qualified_method_name)
            logger.exception('details')


def override_classes(overridden_classes, wrapped):
    """
    Override static classes by creating a subclass (via type) that contains overridden methods. Typically this is
    applied to native classes so that their methods can be overridden to wrap returned instances.

    :param overridden_classes: dict of qualified class names as keys and list of targeted method names as values
    """
    for fully_qualified_class_name, targeted_methods in six.iteritems(overridden_classes):
        try:
            cls = get_class_by_name(fully_qualified_class_name)
            if cls:
                logger.debug('instrumenting class %s', fully_qualified_class_name)
                wrap_methods(cls, targeted_methods, wrapped)
            else:
                logger.warn('%s not overridden because not found', fully_qualified_class_name)
        except ImportError:
            logger.debug('could not override %s', fully_qualified_class_name)
            logger.warn('%s not overridden because not found', fully_qualified_class_name)


def wrap_returned_instances(original_method, overrides):
    """
    Returns a new method that calls the original_method and, if an instance is returned, creates a proxy that uses the
    new_methods (other calls are proxied to the original instance).

    :param original_method: the method that is wrapped to return a wrapped instance
    :param overrides: dictionary of new methods on instances returned from this method, where keys are method names
    and values are wrapper methods
    :return: the wrapped version of the original method
    """

    def decorator(*args, **keywords):
        """
        :return: proxied version of instances
        """
        ret = original_method(*args, **keywords)
        if hasattr(ret, '__class__'):
            # Partial ensures that wrapper method gets original method as first argument --
            # partial(func, *args, **keywords)
            instrumented = {k: functools.partial(v, ret) for k, v in six.iteritems(overrides)}

            # Create a dynamic proxy for a wrapped instance in which the instrumented methods are
            return OverrideWrapper(ret, instrumented)
        else:
            # Return non-instances unmodified
            return ret

    return decorator


def wrap_methods(target, targeted_methods, rules):
    """
    Wraps the target_methods on the target according to the rules.

    The target can be a module or a class.

    The target should not be a native class. To override methods on a native instance, wrap the method(s) that return
     it using wrap_returned_instances.

    :param target: the class or module whose methods are being overwritten
    :param targeted_methods: dict of targeted_method names and the configuration dict for the method (the only item of
       interest is the 'returns' key, which identifies the qualified class type of the returned instance
    :param rules: dict of qualified method names to wrapper methods
    """
    overrides = {}
    for targeted_method, method_config in six.iteritems(targeted_methods):
        """Each wrapped method is modified to return an wrapped object with methods instrumented according to rules"""
        return_type = method_config.get('returns')
        if return_type:
            # Create a custom wrapper based upon the return type of the method
            overrides[targeted_method] = wrapped_returned_instance(target, targeted_method, return_type, rules)
        else:
            logger.error('method %s missing returns value', targeted_method)
    if inspect.ismodule(target):
        for method_name, method_wrapper in six.iteritems(overrides):
            setattr(target, method_name, method_wrapper)
    else:
        sub_class = type(target.__name__, (target,), overrides)
        sub_class.__module__ = target.__module__
        setattr(sys.modules[target.__module__], target.__name__, sub_class)


def wrapped_returned_instance(cls, targeted_method, return_type, rules):
    """
    Returns a method that wraps a method presuming the given return_type. The wrapped method returns an instance so
    that it returns a proxied instance. The proxy overrides methods specified by the given rules dict, which uses
    qualified method names as keys and

    :param cls: the method's class
    :param targeted_method: the method to be wrapped
    :param return_type: the method's return type
    :param rules: the rules applied to the return type
    :return: a wrapped version of targeted_method whose returned value is proxied and applies the given rules
    """
    original_method = getattr(cls, targeted_method)
    wrapper_methods = get_wrapper_methods_for_type(rules, return_type)
    return wrap_returned_instances(original_method, wrapper_methods)


def wrap_returned_instance_decorator(return_type, rules):
    """
    Returns a decorator that wraps a method presuming the given return_type. The wrapped method returns an instance so
    that it returns a proxied instance. The proxy overrides methods specified by the given rules dict, which uses
    qualified method names as keys and

    :param return_type: the type of instance returned by the method
    :param rules: dictionary of qualified method names to instrumentors
    :return: decorator that wraps functions returning instances of the given type to return methods according to rules
    """
    wrapper_methods = get_wrapper_methods_for_type(rules, return_type)

    def decorator(original_method):
        return wrap_returned_instances(original_method, wrapper_methods)

    return decorator


def get_wrapper_methods_for_type(rules, return_type):
    """
    Returns the proxy methods from the rules for the given return type. Presumes that the rules use qualified method
    names and that the return type can be used to identify them
    :param rules: dict of qualified method names to wrapper methods
    :param return_type: qualified name of the return type of interest
    :return: dict of simple method names to wrapper methods
    """
    return_cls = get_class_by_name(return_type)
    pf_len = len(return_type) + 1  # length of prefix, which facilitates extracting method names
    # build a dictionary of simple method names to instrumentors for the given type
    return {k[pf_len:]: v(object.__getattribute__(return_cls, k[pf_len:]))
            for k, v in six.iteritems(rules) if k.startswith(return_type) and hasattr(return_cls, k[pf_len:])}


def _build_key(mappings, args, keywords):
    """
    Builds a list of key values according to the given mappings

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

    Expressions are pipe-delimited values which represent alternatives. Numeric values are used as argument indicies.
    String values are used as dot-delimited names of a keyword and its nested attributes. In addition to keywords,
    "self" is a valid keyword value (alias for the first args value). The first expression that evaluates to a valid
    value is returned.

    :param args: the array of method arguments
    :param keywords: the dictionary of keywords
    :param expressions: the pipe-delimited list of expression values that represent the expression
    :return: The first valid expression value
    """
    final_failure = Exception
    if expressions is None:
        return None
    for expression in expressions.split('|') if isinstance(expressions, six.string_types) else [expressions]:
        try:
            if isinstance(expression, six.integer_types):
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
                            v = six.next(gen)
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
                # Tags are ignored for now
                # tag_pairs = _build_key(mapping, args, keywords)
                try:
                    context.push_state(state)
                    with context_manager(*args, **keywords):
                        if hasattr(f, '__get__'):
                            self = args[0].__subject__ if hasattr(args[0], '__subject__') else args[0]
                            return f.__get__(self)(*args[1:], **keywords)
                        else:
                            return f(*args, **keywords)
                finally:
                    context.pop_state(state)
            else:
                return f(*args, **keywords)

        return wrapper

    return decorator


class OverrideWrapper(ObjectWrapper):
    """
    Proxy class for another instance whose methods are selectively overridden by "new" versions. This proxied instance
    should generally be identical to the original instance, except for overridden methods. The overrides can be wrappers
    of the original methods that provide intercept, augment or instrument the standard behavior.

    Overrides are stored as an '__overrides__' attribute on the object that is accessed using __setattr__ /
    __getattribute__.
    """

    def __init__(self, subject, overrides):
        """
        Initializes this wrapper to proxy for the given subject and override the given methods.
        :param subject: the proxied instance
        :param overrides: the overridden method descriptions dictionary
        """
        super(OverrideWrapper, self).__init__(subject)
        object.__setattr__(self, '__overrides__', overrides)

    def __new__(cls, *args, **kwargs):
        """
        A new object synthesized to look like the wrapped type but actually a subclass of OverrideWrapper.
        :param cls: this given class
        :param args: unnamed arguments (expect subject instance and overrides dict -- see __init__)
        :param kwargs: dictionary of keyworded arguments
        :return: the new instance
        """
        instance_cls = args[0].__class__  # Note: We want the instance to look like the first argument, this class
        t = type(instance_cls.__name__, (cls,), {'__doc__': instance_cls.__doc__, '__isproxy__': True})
        t.__module__ = instance_cls.__module__
        return object.__new__(t)

    def __getattr__(self, attr):
        """
        Intercepts requests for attributes (which include methods) so that overridden methods can be supplied instead of
        the wrapped method.
        Note that simply replacing the methods as a part of the type definition would not work, since the default
        behavior is to call the override method on the proxied subject, not the .
        :param attr: the requested attribute
        :return: the (possibly overridden) attribute value
        """
        # Note: An optimized mechanism for this would be welcomed, this is not as efficient as we would like.
        if not attr.startswith('__'):
            overrides = object.__getattribute__(self, '__overrides__')
            if attr in overrides:
                return overrides.get(attr)
        return super(OverrideWrapper, self).__getattr__(attr)
