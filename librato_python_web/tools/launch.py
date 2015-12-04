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


import atexit
import logging
import os
import subprocess
import sys
from threading import Thread
from time import sleep
from . import agent_config
import signal


STATSD_ARGS = ["librato-statsd-server"]
logger = logging.getLogger(__name__)


class _globals:
    subproc = None


def enable_instrumentation():
    """ Setup environment variables that control the python instrumentor """
    logger.info("Enabling python instrumentation")
    os.environ['LIBRATO_INSTRUMENT_PYTHON'] = "1"


def set_instrumentation_port(_port):
    logger.info("Setting statsd port to %s", _port)
    os.environ['LIBRATO_INSTRUMENTATION_PORT'] = str(_port)


def launch_statsd():
    """ Launch and monitor statsD asynchronously """

    def cleanup_subproc():
        try:
            if _globals.subproc:
                logging.info("Terminating StatsD (pid %s)", _globals.subproc.pid)

                subproc = _globals.subproc
                _globals.subproc = None

                subproc.terminate()
        except:
            logger.exception("Error terminating subprocess")

    def supervisor():
        """ Thread that does the real work """

        while True:
            try:
                logging.info("launching StatsD as: %s", STATSD_ARGS)
                _globals.subproc = subprocess.Popen(STATSD_ARGS)
                rc = _globals.subproc.wait()

                logging.info("StatsD terminated with code %s", rc)
                _globals.subproc = None
                sleep(.1)
            except:
                logger.exception("Error running: %s", STATSD_ARGS)
            finally:
                cleanup_subproc()

    try:
        atexit.register(cleanup_subproc)

        thr = Thread(target=supervisor)
        thr.daemon = True
        thr.start()

        logging.info("Started supervisor thread")
    except:
        logger.exception("Error starting StatsD supervisor thread")


def usage(code=0):
    print("Usage: {} [--info | --debug] command ...".format(sys.argv[0]))
    print("       {} --help".format(sys.argv[0]))
    sys.exit(code)


def control_c_handler(signal, frame):
    try:
        if _globals.subproc:
            logging.info("Forcibly terminating StatsD (pid %s)", _globals.subproc.pid)

            subproc = _globals.subproc
            _globals.subproc = None

            subproc.terminate()
            sys.exit(0)
    except:
        logger.exception("Error terminating subprocess")


def main():
    options = agent_config.load_config([])  # Note that the we are ignoring the command args

    log_level = logging.DEBUG if options.debug else logging.WARNING
    logging.basicConfig(level=log_level, format='%(asctime)s [%(levelname)s] %(message)s')

    signal.signal(signal.SIGINT, control_c_handler)

    (isvalid, errors) = agent_config.validate_config(options)
    if not isvalid:
        logger.error("Invalid Configuration:\n  %s", "\n  ".join(errors))
        sys.exit(2)

    if len(sys.argv) >= 2 and sys.argv[1].startswith('-'):
        opt = sys.argv[1]
        if opt == '--info':
            log_level = logging.INFO
        elif opt == '--debug':
            log_level = logging.DEBUG
        elif opt in ['--help', '-h', '--usage', '-?']:
            usage()
        else:
            print("Unknown option {}".format(opt))
            usage(1)

        args = sys.argv[2:]
    else:
        if sys.argv[1].startswith('-'):
            usage()
        args = sys.argv[1:]

    if args:
        logging.basicConfig(level=log_level)
        enable_instrumentation()
        set_instrumentation_port(options.port)
        launch_statsd()
        logging.info("launching: %s", args)
        subprocess.call(args)
        logging.info("finished")

if __name__ == "__main__":
    main()
