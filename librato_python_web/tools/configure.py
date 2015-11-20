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


import logging
import logging.config
import agent_config

from compose import s_, timeshift_, sum_, subtract_, scale_, derive_, divide_, multiply_, DUMMY_PREFIX, METRIC_PREFIX
from librato.spaces import Api


logger = logging.getLogger(__name__)

SPACE_NAME = '{}:Python {} Application'


RESPONSE_TIME_QUERY = sum_(s_("web*response.latency.mean"))
THROUGHPUT_QUERY = derive_(sum_(s_("web*requests.count")))
ERROR_PERCENTAGE_QUERY = scale_(
    divide_(
        derive_(
            sum_(
                s_("web.status.4xx.count", function="sum"),
                s_("web.status.5xx.count", function="sum"))),
        THROUGHPUT_QUERY),
    "100")

CHART_SPECS = [
    {
        'name': 'Response Time',
        'y_label': 'milliseconds',
        'chart_type': 'line',
        'metrics': [
            {
                'name': 'Current',
                'composite': RESPONSE_TIME_QUERY,
                'summary_function': 'average',
                'color': '#ff8501'
            },
            {
                'name': '24 hours ago',
                'composite': timeshift_("1d", RESPONSE_TIME_QUERY),
                'summary_function': 'average',
                'color': '#0880ae'
            },
            {
                'name': 'Week ago',
                'composite': timeshift_("1w", RESPONSE_TIME_QUERY),
                'summary_function': 'average',
                'color': '#50a3c3'
            }
        ]
    },
    {
        'name': 'Response Time Components',
        'y_label': 'milliseconds',
        'chart_type': 'stacked',
        'metrics': [
            {
                'name': 'gunicorn',
                'composite': divide_(
                    subtract_(
                        sum_(
                            multiply_(
                                s_("gunicorn.request.duration.mean"),
                                s_("gunicorn.request.duration.count", function="sum"))),
                        sum_(
                            multiply_(
                                s_("wsgi.response.latency.mean"),
                                s_("wsgi.response.latency.count", function="sum")))),
                    sum_(s_("web.response.latency.count", function="sum"))),
                'summary_function': 'sum',
                'color': '#f04950'
            },
            {
                'name': 'wsgi',
                'composite': divide_(
                    subtract_(
                        sum_(
                            multiply_(
                                s_("wsgi.response.latency.mean"),
                                s_("wsgi.response.latency.count"))),
                        sum_(
                            multiply_(
                                s_("web.response.latency.mean"),
                                s_("web.response.latency.count")))),
                    sum_(s_("web.response.latency.count", function="sum"))),
                'summary_function': 'sum',
                'color': '#2b89ad'
            },
            {
                'name': 'web app',
                'composite': divide_(
                    sum_(
                        multiply_(
                            s_("app.response.latency.mean"),
                            s_("app.response.latency.count"))),
                    sum_(s_("web.response.latency.count"))),
                'summary_function': 'sum',
                'color': '#ff8501'
            },
            {
                'name': 'data',
                'composite': divide_(
                    sum_(
                        multiply_(
                            s_("data.*.latency.mean"),
                            s_("data.*.latency.count"))),
                    sum_(s_("web.response.latency.count"))),
                'summary_function': 'sum',
                'color': '#a85802'
            },
            {
                'name': 'external',
                'composite': divide_(
                    sum_(
                        multiply_(
                            s_("external.*.response.latency.mean"),
                            s_("external.*.response.latency.count"))),
                    sum_(s_("web.response.latency.count"))),
                'summary_function': 'sum',
                'color': '#0880ae'
            },
            {
                'name': 'model',
                'composite': divide_(
                    sum_(
                        multiply_(
                            s_("model.*.latency.mean"),
                            s_("model.*.latency.count"))),
                    sum_(s_("web.response.latency.count"))),
                'summary_function': 'sum',
                'color': '#d67002'
            }
        ]
    },
    {
        'name': 'Throughput (rpm)',
        'y_label': 'rpm',
        'chart_type': 'line',
        'metrics': [
            {
                'name': 'Current',
                'composite': THROUGHPUT_QUERY,
                'summary_function': 'sum',
                'color': '#ff8501'
            },
            {
                'name': '24 hours ago',
                'composite': timeshift_("1d", THROUGHPUT_QUERY),
                'summary_function': 'sum',
                'color': '#0880ae'
            },
            {
                'name': 'Week ago',
                'composite': timeshift_("1w", THROUGHPUT_QUERY),
                'summary_function': 'sum',
                'color': '#50a3c3'
            }
        ]
    },
    {
        'name': 'Throughput (rpm) by Status Codes',
        'y_label': 'rpm',
        'chart_type': 'stacked',
        'metrics': [
            {
                'name': '2xx',
                'composite': derive_(sum_(s_("web.status.2xx.count"))),
                'summary_function': 'sum',
                'color': '#0880ae'
            },
            {
                'name': '3xx',
                'composite': derive_(sum_(s_("web.status.3xx.count"))),
                'summary_function': 'sum',
                'color': '#ff7e63'
            },
            {
                'name': '4xx',
                'composite': derive_(sum_(s_("web.status.4xx.count"))),
                'summary_function': 'sum',
                'color': '#ff5a37'
            },
            {
                'name': '5xx',
                'composite': derive_(sum_(s_("web.status.5xx.count"))),
                'summary_function': 'sum',
                'color': '#ff2d01'
            }
        ]
    },
    {
        'name': 'Logging Components',
        'y_label': 'epm',
        'chart_type': 'stacked',
        'metrics': [
            {
                'name': 'Warnings',
                'composite': derive_(sum_(s_("logging.warning.requests.count"))),
                'summary_function': 'sum',
                'color': '#d69900'
            },
            {
                'name': 'Errors',
                'composite': derive_(sum_(s_("logging.error.requests.count"))),
                'summary_function': 'sum',
                'color': '#ff2d01'
            },
            {
                'name': 'Exceptions',
                'composite': derive_(sum_(s_("logging.exception.requests.count"))),
                'summary_function': 'sum',
                'color': '#a81d00'
            }
        ]
    },
    {
        'name': 'Error Percentage',
        'y_label': 'percentage',
        'chart_type': 'line',
        'min_': 0.0,
        'max_': 100.0,
        'metrics': [
            {
                'name': 'Current',
                'composite': ERROR_PERCENTAGE_QUERY,
                'summary_function': 'sum',
                'color': '#ff2d01'
            },
            {
                'name': '24 hours ago',
                'composite': timeshift_("1d", ERROR_PERCENTAGE_QUERY),
                'summary_function': 'sum',
                'color': '#ff5a37'
            },
            {
                'name': 'Week ago',
                'composite': timeshift_("1w", ERROR_PERCENTAGE_QUERY),
                'summary_function': 'sum',
                'color': '#ff7e63'
            }
        ]
    }
]


def _create_space(api, space_name):
    spaces = api.get_spaces()
    logger.debug("Spaces: %s" % spaces)

    for s in spaces:
        if s.get('name') == space_name:
            _space = s
            logger.info('Space {} already exists'.format(space_name))
            break
    else:
        _space = api.add_space(space_name)
        logger.info("Added space: {}".format(space_name))

    return _space


def _add_chart(api, _space, name, y_label, chart_type="line", metrics=[], min_=None, max_=None):
    _space_id = _space.get('id')
    _charts = api.get_charts(_space_id)
    for c in _charts:
        if c.get('name') == name:
            _chart = c
            logger.info('Chart {} already exists'.format(name))
            break
    else:
        logger.info('Adding chart {}'.format(name))
        _chart = api.add_chart(_space_id, name, y_label, chart_type=chart_type, metrics=metrics, min_=min_, max_=max_)

    return _chart


def _add_metrics(api, _space, _chart, _metrics):
    _space_id = _space.get('id')
    _chart_id = _chart.get('id')
    for _metric in _metrics:
        logger.info('Adding metric {}'.format(_metric))
        api.add_metric(_space_id, _chart_id, _metric)


def _update(_user, _password, _app_id, _integration):
    api = Api(_user, _password)
    logger.info("Update space in Librato for account %s", _user)

    space = _create_space(api, SPACE_NAME.format(_app_id, _integration.title()))

    for spec in CHART_SPECS:
        for metrics in spec.get("metrics"):
            metrics["composite"] = metrics["composite"].replace(DUMMY_PREFIX, _app_id)
            metrics["composite"] = metrics["composite"].replace(METRIC_PREFIX, _integration)

        _add_chart(api, space, **spec)


def execute():
    options = agent_config.load_config()

    log_level = logging.DEBUG if options.debug else logging.WARNING
    logging.basicConfig(level=log_level, format='%(asctime)s [%(levelname)s] %(message)s')

    (isvalid, errors) = agent_config.validate_config(options)
    if not isvalid:
        logger.error("Invalid Configuration:\n  %s", "\n  ".join(errors))
        return 2

    agent_config.update_config_file(vars(options))

    _update(options.user, options.api_token, options.app_id, options.integration)

if __name__ == '__main__':
    execute()
