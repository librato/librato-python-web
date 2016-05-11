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

""" Instruments Gunicorn to report active and configured worker counts """

from math import floor
import time

from librato_python_web.instrumentor import telemetry
from librato_python_web.instrumentor.base_instrumentor import BaseInstrumentor
from librato_python_web.instrumentor.instrument import get_conditional_wrapper
from librato_python_web.instrumentor.custom_logging import getCustomLogger

logger = getCustomLogger(__name__)


class __globals:
    last_reported = None

logger = getCustomLogger(__name__)


def _manage_workers(func, *args, **keywords):
    response = func(*args, **keywords)

    try:
        arbiter = args[0]
        telemetry.record('gunicorn.workers', arbiter._last_logged_active_worker_count, is_timer=False,
                         reporter='gunicorn')
    except Exception as e:
        logger.exception("Instrumentation error while reporting gunicorn.workers")

    return response


def _worker_notify(func, *args, **keywords):
    response = func(*args, **keywords)

    # Increment the worker count once per minute since that is our rollup interval
    try:
        now = int(time.time())
        threshold = int(60*floor(now/60))
        if not __globals.last_reported or __globals.last_reported < threshold:
            telemetry.count("gunicorn.active_workers", 1, reporter='gunicorn')
            __globals.last_reported = now
    except Exception as e:
        logger.exception("Instrumentation error while reporting gunicorn.active_workers")

    return response


class GunicornInstrumentor(BaseInstrumentor):
    modules = {'gunicorn.arbiter': ['Arbiter'], 'gunicorn.workers.base': ['Worker']}

    def __init__(self):
        super(GunicornInstrumentor, self).__init__()

    def run(self):
        self.set_wrapped(
            {
                'gunicorn.arbiter.Arbiter.manage_workers': get_conditional_wrapper(_manage_workers, enable_if=None),
                'gunicorn.workers.base.Worker.notify': get_conditional_wrapper(_worker_notify, enable_if=None),
            }
        )
        super(GunicornInstrumentor, self).run()
