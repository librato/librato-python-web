from flask import Flask, jsonify
from librato_python_web.instrumentor.context import _get_state

app = Flask(__name__)


@app.route('/')
def get_state():
    return jsonify(_get_state())

if __name__ == '__main__':
    app.run()
