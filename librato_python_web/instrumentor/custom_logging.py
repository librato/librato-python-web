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

""" Custom logger which lets us avoid a dependency on the standard logging module """

import sys
import traceback as tb
from six import print_

DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40
CRITICAL = 50


class _globals(object):
    """ Global vars """
    level = WARNING


class CustomLogger(object):
    """" Custome logger class which mimics the logging module """

    def __init__(self, name):
        """ Constructor """
        self._name = name

    def _stdout(self, level, fmt, *args, **kwargs):
        """ Formats message and writes it to standard output """
        mesg = fmt % args
        print("[{}] {} - {}".format(level, self._name, mesg))

    def _stderr(self, level, fmt, *args, **kwargs):
        """ Formats message and writes it to standard error """
        mesg = fmt % args
        print_("[{}] {} - {}".format(level, self._name, mesg), file=sys.stderr)

    def debug(self, fmt, *args, **kwargs):
        """ Logs a debug message """
        if _globals.level <= DEBUG:
            self._stdout("DEBUG", fmt, *args, **kwargs)

    def info(self, fmt, *args, **kwargs):
        """ Logs an informational message """
        if _globals.level <= INFO:
            self._stdout("INFO", fmt, *args, **kwargs)

    def warning(self, fmt, *args, **kwargs):
        """ Logs a warning """
        if _globals.level <= WARNING:
            self._stdout("WARNING", fmt, *args, **kwargs)

    def warn(self, fmt, *args, **kwargs):
        """ Logs a warning """
        return self.warning(fmt, *args, **kwargs)

    def error(self, fmt, *args, **kwargs):
        """ Logs an error message """
        if _globals.level <= ERROR:
            self._stderr("ERROR", fmt, *args, **kwargs)

    def exception(self, fmt, *args, **kwargs):
        """ Logs an exception """
        self._stderr("EXCEPTION", fmt, *args, **kwargs)
        tb.print_exc()

    def critical(self, fmt, *args, **kwargs):
        """ Logs a critical message """
        if _globals.level >= CRITICAL:
            self._stderr("CRITICAL", fmt, *args, **kwargs)


def setDefaultLevel(level):
    """ Sets the default level for custom logger instances """
    _globals.level = level


def getCustomLogger(name):
    """ Factory method """
    return CustomLogger(name)
