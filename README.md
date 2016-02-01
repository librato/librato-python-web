librato-python-web
==================

`librato-python-web` makes it easy to track the performance of Python Django, Flask or CherryPy web apps using [Librato](https://metrics.librato.com/). No code modifications to your apps are necessary and you can fine-tune the metrics you'd like monitored. In order to ensure there is no performance impact on your application, metrics are delivered asynchronously, using a bundled Statsd instance.

## System requirements

* Python 2.7.x (>=2.7.3) or Python 3.x
* Django 1.8.6 or later, or Flask 0.10.1 or later, or CherryPy 4.0.0 or later
* Linux or OSX

## Verified combinations
* Python 2.7.3 or Python 3.4.3
* Django 1.8.6 or Flask 0.10.1 or CherryPy 4.0.0
* Ubuntu 14.04.3 LTS or OSX Yosemite 10.10.5


## Installation

* If you don't have a Librato account already, [sign up](https://metrics.librato.com/). In order to send measurements to Librato you need to provide your account credentials to `librato-python-web`.
* Log into the Librato web console and create a Django integration. Note the unique app id.
* The integration will create a new space under which your metrics will appear.
* Optionally create a virtual environment to run your instrumented app (highly recommended).
* Under your virtual environment, install and configure the agent using the shell command shown below.
  * For Django, run
```
pip install librato-python-web && librato-config --user <librato-email-address> --api-token <librato-api-token> --app-id <app-id>
```
  * For Flask, run
```
pip install librato-python-web && librato-config --integration flask --user <librato-email-address> --api-token <librato-api-token> --app-id <app-id>
```
  * For CherryPy, run
```
pip install librato-python-web && librato-config --integration cherrypy --user <librato-email-address> --api-token <librato-api-token> --app-id <app-id>
```
* Launch (or relaunch) your application in the same place where you ran the above one-liner, with the special librato-launch prefix. E.g., for Django,
```
librato-launch python manage.py runserver
```
* Charts will now start to appear on your space. A number of new metrics will also start to appear in your Librato account.

## Gunicorn
Alter the gunicorn command line to send metrics to the bundled StatsD instance. For example,
```
librato-launch gunicorn --statsd-host=127.0.0.1:8142 wsgi-module:app
```

## Copyright

Copyright (c) 2015 [Librato Inc.](http://librato.com) See LICENSE for details.
