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


from librato_python_web.instrumentor import context
from librato_python_web.instrumentor.custom_logging import getCustomLogger


logger = getCustomLogger(__name__)


def run_instrumentors(instrumentors, libs):
    """
    :param instrumentors:
    :return:
    """
    for alias in instrumentors:
        if libs != '*' and alias not in libs:
            logger.info("Skipping %s", alias)
            continue

        try:
            logger.info("Instrumenting %s", alias)
            instrumentor = instrumentors[alias]
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


def instrument_methods(method_wrappers):
    """
    Instruments the methods as specified by the method_wrappers dict. Keys indicate the method path and values provide
    the function that wraps the method.
    :param method_wrappers: dictionary of paths to
    :return:
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
    (module_name, class_name) = fully_qualified_class_name.rsplit('.', 1) if '.' in fully_qualified_class_name \
        else (fully_qualified_class_name, None)
    try:
        module_def = __import__(module_name, globals(), locals(), [class_name] if class_name else [])
        class_def = getattr(module_def, class_name) if module_def and class_name else None
    except ImportError:
        logger.info('%s not found', fully_qualified_class_name)
        class_def = None

    return class_def


def wrap_method(class_def, method_name, method_wrapper):
    """
    Wrap the method with the method_name on the class_def by the method_wrapper.

    :param class_def:
    :param method_name:
    :param method_wrapper:
    """
    original_method = getattr(class_def, method_name)
    wrapped_method = method_wrapper(class_def, original_method)
    replace_method(class_def, method_name, wrapped_method)


def replace_method(class_def, method_name, method):
    """
    Replaces the given method name on the given class_def with the given method.

    :param class_def:
    :param method_name:
    :param method:
    """
    setattr(class_def, method_name, method)


def _build_key(args, keys, keywords):
    values = []
    for a in keys or sorted(keywords.keys()):
        value = _eval(args, keywords, a)
        if value is not None:
            values.append(value)
    if len(values) > 2:
        logger.error("more than two values in _build_key: %s", str(values))
    return values


def _eval(args, keywords, expressions):
    final_failure = Exception
    if not expressions:
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

    def function_wrapper(ctx, f):
        """
        :param ctx: the context for the call, typically a class def
        :param f: the function to wrap
        """
        def wrapper(*args, **keywords):
            if _should_be_instrumented(state, enable_if, disable_if):
                return wrapper_function(f)(*args, **keywords)
            else:
                return f(*args, **keywords)
        return wrapper

    return function_wrapper


def context_function_wrapper_factory(context_manager, prefix=None, keys=None, state=None, enable_if='web',
                                     disable_if=None):
    """
    Generates a function that wraps a function so that it uses the context_manager around it and harvests
    the given prefix, keys, and suffix as context.

    TODO: replace prefix/keys with tags whose name-value pairs are used to generate tags that are pushed/popped

    :param context_manager: the contextmanager (optional, in which case context is pushed/popped around the call)
    :param prefix: the prefix (the key for the context)
    :param keys: the keys used to look up values from the method target and/or arguments
    :param state: the state associated with the wrapped method
    :param enable_if: instrumentation is only enabled when this state is present
    :param disable_if: instrumentation is disabled when this state is present
    :return: the function wrapper
    """

    def function_wrapper(ctx, f):
        def wrapper(*args, **keywords):
            if _should_be_instrumented(state, enable_if, disable_if):
                vals = _build_key(args, keys, keywords) if keys else []
                if prefix:
                    vals.insert(0, prefix)
                try:
                    if state:
                        logger.debug('pushing state %s for %s', state, f.__name__)
                        context.push_state(state)
                    if len(vals) > 1:
                        context.push_tag(vals[0], vals[1])
                    if context_manager:
                        with context_manager(*args, **keywords):
                            return f(*args, **keywords)
                    else:
                        return f(*args, **keywords)
                finally:
                    if len(vals) > 1:
                        context.pop_tag()
                    if state:
                        logger.debug('popping state %s for %s', state, f.__name__)
                        context.pop_state(state)
            else:
                return f(*args, **keywords)

        return wrapper

    return function_wrapper
