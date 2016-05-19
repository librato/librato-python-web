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

import sys

from librato_python_web.instrumentor.custom_logging import getCustomLogger
from librato_python_web.instrumentor.instrument import instrument_methods

logger = getCustomLogger(__name__)


class BaseInstrumentor(object):
    def __init__(self, wrapped=None, state=None):
        self.wrapped_methods = wrapped

        # Subclasses should override major_versions to specify supported Python versions.
        # Default is all versions.
        self.major_versions = None

    def set_wrapped(self, wrapped):
        self.wrapped_methods = wrapped if wrapped is not None else {}

    def can_run(self):
        # Confirm that required modules and attributes exist
        if hasattr(self, 'modules'):
            for name in self.modules:
                if name not in sys.modules:
                    logger.info("Skipping for now - required module %s not loaded yet", name)
                    return False
                mod_ = sys.modules[name]

                for attr_ in self.modules[name]:
                    if hasattr(mod_, attr_):
                        logger.info("Found required attribute %s in %s", attr_, name)
                    else:
                        logger.info("Skipping %s for now - missing required attr %s", name, attr_)
                        return False

        return True

    def run(self):
        major_version = sys.version_info[0]
        if self.major_versions and major_version not in self.major_versions:
            logger.warn("Disabling %s since it doesn't support python %s.x", self.__class__, major_version)
            return

        instrument_methods(self.wrapped_methods)
