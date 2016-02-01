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


# Helper methods to model Librato composite query dsl
METRIC_PREFIX = "!XyZZy!"
DUMMY_PREFIX = "DUMMY-PREFIX"
DYNAMIC_SOURCE = "%"
DEFAULT_PERIOD = 60


def s_(metric, source=DYNAMIC_SOURCE, period=None, function=None):
    if period and function:
        return 's("{}.{}", "{}", {{period: "{}", function: "{}"}})'.format(METRIC_PREFIX, metric, source, period,
                                                                           function)
    elif period:
        return 's("{}.{}", "{}", {{period: "{}"}})'.format(METRIC_PREFIX, metric, source, period)
    elif function:
        return 's("{}.{}", "{}", {{function: "{}"}})'.format(METRIC_PREFIX, metric, source, function)
    else:
        return 's("{}.{}", "{}")'.format(METRIC_PREFIX, metric, source)


def timeshift_(shift, series):
    return 'timeshift("{}", {})'.format(shift, series)


def sum_(*args):
    return 'sum([{}])'.format(', '.join(args))


def subtract_(series1, series2):
    return 'subtract([{}, {}])'.format(series1, series2)


def multiply_(*args):
    return 'multiply([{}])'.format(', '.join(args))


def divide_(series1, series2):
    return 'divide([{}, {}])'.format(series1, series2)


def scale_(series, factor):
    return 'scale({}, {{factor: "{}"}})'.format(series, factor)


def derive_(series, detect_reset="true"):
    return 'derive({}, {{detect_reset: "{}"}})'.format(series, detect_reset)


def mean_(*args):
    return 'mean([{}])'.format(', '.join(args))


def rate_(metric, source=DYNAMIC_SOURCE, period=DEFAULT_PERIOD, duration=DEFAULT_PERIOD):
    return 'rate(sum([derive(s("{}.{}", "{}", {{period:"{}"}}), {{detect_reset: "true"}})]), {{duration:"{}"}})'.format(
        METRIC_PREFIX, metric, source, period, duration)
