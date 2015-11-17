librato-python-web
==================

`librato-python-web` makes it easy to track the performance of Python Django web apps using [Librato](https://metrics.librato.com/). No code modifications to apps are necessary and you can fine-tune the metrics you'd like monitored. Metrics are delivered asynchronously, using a bundled statsd instances, so the impact on apps will be minimal.

## System requirements

* Python 2.7.x, >=2.7.3
* Django 1.8.6 or later
* Linux

## Verified combinations
* Python 2.7.3
* Django 1.8.6
* Ubuntu 14.04.3 LTS


## Installation

* If you don't have a Librato account already, [sign up](https://metrics.librato.com/). In order to send measurements to Librato you need to provide your account credentials to `librato-python-web`.
* Log into the Librato web console and create a Django integration. Note the unique app id.
* The integration will create a new space under which your metrics will appear.
* Optionally create a virtual environment to run your instrumented app (highly recommended).
* Under your virtual environment, install and configure the agent as shown below.
```
pip install librato-python-web && librato-config --user <librato-email-address> --api-token <librato-api-token> --app-id <app-id>
```
* Launch (or relaunch) your application in the same place where you ran 1-liner, with the special librato-launch prefix. E.g.
```
librato-launch python manage.py runserver
```
* Charts will now start to appear on your space. A number of new metrics will also start to appear in your Librato account.

## Copyright

Copyright (c) 2015 [Librato Inc.](http://librato.com) See LICENSE for details.
