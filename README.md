librato-python-web
==================

`librato-python-web` is the Python agent for Librato's Django, Flask, CherryPy and Gunicorn turnkey integrations. It gathers essential health and performance metrics related to your web application and ships them to [Librato](https://metrics.librato.com/), where you can view them in curated or custom metrics dashboards.

## System requirements

* Python 2.7.x (>=2.7.3) or Python 3.x
* Django 1.8.6 or later, or Flask 0.10.1 or later, CherryPy 4.0.0 or later, Gunicorn 19.4.5 or later
* Linux or OSX

## Verified combinations
* Python 2.7.3 or Python 3.5.1
* Django 1.8.6 or Flask 0.10.1 or CherryPy 4.0.0 or Gunicorn 19.4.5
* Ubuntu 14.04.3 LTS or OSX Yosemite 10.10.5


## Overview

See the following KB articles for a general overview of how to create a turnkey Librato integration and configure the Python agent.

* [Django](https://www.librato.com/docs/kb/collect/integrations/django.html)
* [Flask](https://www.librato.com/docs/kb/collect/integrations/flask.html)
* [CherryPy](https://www.librato.com/docs/kb/collect/integrations/cherrypy.html)
* [Gunicorn](https://www.librato.com/docs/kb/collect/integrations/gunicorn.html)

We highly recommend running your instrumented application under a virtual environment. E.g.
```
pip install virtualenv
virtualenv my_project_folder
source my_project_folder/bin/activate
```

## Installing and configuring the agent

Install the Python agent using pip as shown below.

```
pip install librato-python-web
```

Use the provided librato-launch tool to configure the Python agent. Do this for every web application that you want to monitor. For example, the following command configures the Python agent to monitor a cherrypy application called 'cherrypy-prod-1'.

```
librato-config --app-id cherrypy-prod-1 --integration=cherrypy --user user@librato.com --api-token XXXXXXXXXXXX
```

This will create a JSON configuration file in the current directory, named agent-conf.json, which looks as follows.

```
{
   "integration": "cherrypy",
   "metrics_hostname": "metrics-api.librato.com",
   "hostname": "localhost",
   "stop": false,
   "app_id": "cherrypy-prod-1",
   "no_aggregate_counters": false,
   "pidfile": "/var/run/solarwinds-python-statsd.pid",
   "flush_interval": 10000,
   "daemonize": false,
   "user": "user@librato.com",
   "expire": 0,
   "api_token": “XXXXXXXXXXXX”,
   "debug": false,
   "pct": 95,
   "port": 8142,
   "restart": false
}
```

The --config-path option can be used to specify an alternate file location.

The --integration option optionally specifies the web framework to monitor (default is 'django').

The --app-id option (required) specifies a unique identifier for the application. The instrumentation prefixes the application id to the [source](https://www.librato.com/docs/kb/faq/glossary/whats_a_source.html) for every measurement related to the app. This allows you to filter or aggregate metrics down to the application in turnkey or custom dashboards.

Run ```librato-config --help``` to see a full list of options.


## Running your application

In order to instrument your application, prefix your runtime command with librato-launch. E.g.

```
librato-launch python manage.py runserver
```

Running under librato-launch triggers a custom module loader, which instruments classes as they get imported by the application. The loader targets web framework modules (e.g. django.*) to report web request latency, throughput and error metrics. It also instruments libraries such as mysql, postgres, elasticsearch, urllib2 and requests in order to decompose web request latency into subcomponents, such as data, external and wsgi.

librato-launch consumes the configuration file (./agent-conf.json, by default). Use --config-path to override this default location.

librato-launch spawns a StatsD process to report metrics to Librato, which uses port 8142 by default. You can customize this port using the --port option to librato-config, or by manually editing the configuration file.

## Gunicorn monitoring

To monitor Gunicorn, add the --statsd-host option as shown below.

```
librato-launch gunicorn --statsd-host=127.0.0.1:8142 ... my_module:my_app
```


## Instrumenting using code

You can't or don't want to auto-instrument your app, you can skip launch-launch and trigger instrumentation using the following code.

```
from librato_python_web.instrumentor import bootstrap

bootstrap.init(config-file-path)   # config-file-path can be omitted and defaults to './agent-conf.json'
```

Since modules are instrumented as they are loaded, it is important to call bootstrap.init() before the web framework (e.g. Django) and dependencies such as mysql or postgres are imported.

Since librato-launch is no longer in the picture, you'll need to run the StatsD server in order to report measurements to Librato. This can be done using the following command.

```
librato-statsd-server

or

librato-statsd-server --config-path <config-file-location>
```

Run ```librato-statsd-server --help``` for a complete list of options.

## Copyright

Copyright (c) 2015 [Librato Inc.](http://librato.com) See LICENSE for details.
