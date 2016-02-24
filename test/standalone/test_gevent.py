
from librato_python_web.instrumentor import bootstrap

bootstrap.init()

import gevent
from gevent import monkey
monkey.patch_all()

import requests
import django
import werkzeug.serving

# Ensure the patched libs are in use
assert requests.adapters.socket.socket.__module__ == "gevent.socket", "Requests used unpatched socket"
assert werkzeug.serving.socket.socket.__module__ == "gevent.socket", "Werkzeug used unpatched socket"
