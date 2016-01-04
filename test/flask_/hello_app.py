from flask import Flask, abort

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/dir/')
def dir_listing():
    return ['foo', 'bar']


@app.route('/notfound/')
def notfound():
    abort(404, "Verify this text!")


@app.route('/error/')
def error():
    abort(505, "Internal error!")


@app.route('/exception/')
def exception():
    raise Exception("Unexpected app exception")


if __name__ == '__main__':
    app.run()
