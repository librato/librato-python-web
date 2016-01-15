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


import cherrypy
from cherrypy import tools


class HelloWorld(object):
    @cherrypy.expose
    def index(self):
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return "Hello world!"

    @cherrypy.expose
    @tools.json_out()
    def redirect(self):
        raise cherrypy.HTTPRedirect("http://www.yahoo.com")

    @cherrypy.expose
    def notfound(self):
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        raise cherrypy.NotFound("Verify this text!")

    @cherrypy.expose
    def error(self):
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        raise cherrypy.HTTPError(status=505, message="Internal error!")

    @cherrypy.expose
    def exception(self):
        raise Exception("Unexpected app exception")


if __name__ == '__main__':
    cherrypy.quickstart(HelloWorld())
