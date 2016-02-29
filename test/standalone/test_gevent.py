
from librato_python_web.instrumentor import bootstrap

bootstrap.init()

import gevent
from gevent import monkey
monkey.patch_all()

import requests
import werkzeug.serving

# Ensure the patched libs are in use
assert 'gevent' in requests.adapters.socket.socket.__module__, "Requests used unpatched socket"
assert 'gevent' in werkzeug.serving.socket.socket.__module__, "Werkzeug used unpatched socket"
