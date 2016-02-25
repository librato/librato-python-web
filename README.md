librato-python-web
==================

`librato-python-web` is the Python agent for Librato's Django, Flask, CherryPy Gunicorn turnkey integrations. It gathers essential health and performance metrics and ships them to [Librato](https://metrics.librato.com/), where you can view them in turnkey integration or your custom dashboards. The agent auto-instruments your code and reports a default set of metrics to Librato using using a bundled StatsD instance. You can turn on the instrumentation from code and control the libraries which are instrumented using a configuration file.

## System requirements

* Python 2.7.x (>=2.7.3) or Python 3.x
* Django 1.8.6 or later, or Flask 0.10.1 or later, CherryPy 4.0.0 or later, Gunicorn 19.4.5 or later
* Linux or OSX

## Verified combinations
* Python 2.7.3 or Python 3.5.1
* Django 1.8.6 or Flask 0.10.1 or CherryPy 4.0.0 or Gunicorn 19.4.5
* Ubuntu 14.04.3 LTS or OSX Yosemite 10.10.5


## Installation

See the following KB articles for a general overview of how to create a turnkey Librato integration and configure the Python agent. Additional details are below.

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

# Installing and configuring the agent

Install the Python agent using pip as shown below.

```
pip install librato-python-web
```

Use the provided librato-launch tool to configure the Python agent and the bundled StatsD server. You will need to
run this for every web application that you want to monitor.

As an example, the following command configures the Python agent to monitor a cherrypy application called 'cherrypy-prod-1'.

```
librato-config --app-id cherrypy-prod-1 --integration=cherrypy --user user@librato.com --api-token XXXXXXXXXXXX
```

This will create a configuration file in the current directory, which by default is called agent-conf.json. The
--config-path option can be used to specify an alternate configuration file location.

The --integration option optionally specifies the web framework to instrument (defaults is 'django'). It also determines the metric names that get sent to Librato.

The --app-id option (required) specifies a unique identifier for the application. The bundled StatsD instance prefixes the application id to the [source](https://www.librato.com/docs/kb/faq/glossary/whats_a_source.html) for all measurements for the app. This allows you to filter or aggregate metrics using the application id in turnkey or custom dashboards.

Run 'librato-config --help' to see a full list of options.

## Running your app

You can auto-instrument your application to report metrics using the librato-launch command. In order to do so, simply prefix your runtime command with librato-launch as show below. E.g.

```
librato-launch python manage.py runserver
```

librato-launch configures a custom module loader, which instruments framework modules (e.g. django.*) to report web request latency, throughput and error metrics. We also instrument the following libraries to break down web request latency into subcomponents, such as wsgi, data and external.

librato-launch consumes the configuration file (./agent-conf.json by default). Use --config-path to override this default location.

librato-launch spawns a StatsD process to report metrics over to Librato, which uses port 8142 by default. You can customize this port using the --port option to librato-config, or by manually editing the configuration file.


## Gunicorn monitoring

Alter the gunicorn command line to send metrics to the bundled StatsD instance. For example,
```
librato-launch gunicorn --statsd-host=127.0.0.1:8142 wsgi-module:app
```

## Copyright

Copyright (c) 2015 [Librato Inc.](http://librato.com) See LICENSE for details.
