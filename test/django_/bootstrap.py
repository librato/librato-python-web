
import os
from librato_python_web.instrumentor.bootstrap import init

os.environ['LIBRATO_INTEGRATION'] = 'django'
init()
