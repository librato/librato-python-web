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
from functools import wraps
import time

from librato_python_web.instrumentor import context
from librato_python_web.instrumentor.custom_logging import getCustomLogger

logger = getCustomLogger(__name__)


def run_instrumentors(instrumentors, libs):
    """
    :param instrumentors:
    :param libs:
    """
    for alias in instrumentors:
        if libs != '*' and alias not in libs:
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
    for method_path, method_wrapper in method_wrappers.iteritems():
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


def is_class_available(fully_qualified_class_name):
    """
    Return True if the class / module with fully_qualified_class_name is loadable.

    :param fully_qualified_class_name:
    :type fully_qualified_class_name: str
    :return: True if class is found, False otherwise
    :returns: bool
    """
    return get_module_by_name(fully_qualified_class_name) is not None or \
        get_class_by_name(fully_qualified_class_name) is not None


def get_module_by_name(fully_qualified_module_name):
    try:
        return __import__(fully_qualified_module_name)
    except ImportError:
        return None


def get_class_by_name(fully_qualified_class_name):
    """
    Return the class with fully_qualified_class_name.

    :param fully_qualified_class_name:
    :type fully_qualified_class_name: str
    :return: the specified class, None if not found
    """
    (module_path, class_name) = fully_qualified_class_name.rsplit('.', 1) if '.' in fully_qualified_class_name \
        else (fully_qualified_class_name, None)
    try:
        module_def = __import__(module_path, globals(), locals(), [class_name] if class_name else [])
        class_def = getattr(module_def, class_name) if module_def and class_name else None
    except ImportError:
        logger.info('%s not found', fully_qualified_class_name)
        class_def = None

    return class_def


def wrap_method(method_owner, method_name, method_wrapper):
    """
    Wrap the method with the method_name on the class_def using the method_wrapper.

    :param method_owner:
    :param method_name:
    :param method_wrapper:
    """
    original_method = getattr(method_owner, method_name)
    wrapped_method = method_wrapper(original_method)
    wrapped_method.original = (method_owner, method_name, original_method)
    replace_method(method_owner, method_name, wrapped_method)


def unwrap_method(method_wrapper):
    if hasattr(method_wrapper, 'original'):
        original = method_wrapper.original
        replace_method(*original)
        delattr(method_wrapper, 'original')


def replace_method(owner, method_name, method):
    """
    Replaces the given method name on the given class_def with the given method.

    :param owner: the owner of the method (class or module)
    :param method_name: the method name on the owner
    :param method: the method to use
    """
    setattr(owner, method_name, method)


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
                return wrapper_function(f)(*args, **keywords)
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
                t = time.time()
                try:
                    gen = generator(*args, **keywords)
                finally:
                    elapsed += time.time() - t
                try:
                    while True:
                        # wrap each successive value generation
                        t = time.time()
                        try:
                            v = gen.next()
                        finally:
                            elapsed += time.time() - t
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
                    if state:
                        logger.debug('pushing state %s for %s', state, f.__name__)
                        context.push_state(state)
                    for pair in tag_pairs:
                        logger.debug('pushing tag pair %s for %s', str(pair), f.__name__)
                        context.push_tag(pair[0], pair[1])
                    with context_manager(*args, **keywords):
                        return f(*args, **keywords)
                finally:
                    for _ in tag_pairs:
                        context.pop_tag()
                    if state:
                        logger.debug('popping state %s for %s', state, f.__name__)
                        context.pop_state(state)
            else:
                return f(*args, **keywords)
        return wrapper
    return decorator
