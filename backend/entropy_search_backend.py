import sys
import multiprocessing
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from mimas.spectra.similarity import tools_fast

from entropy_search_server import EntropySearchServer

######################################################
app = Flask(__name__)
CORS(app)
server = EntropySearchServer()

@app.route("/entropy_search_parameter", methods=['POST'])
def mass_search():
    parameter = json.loads(request.data)
    server.start_search(parameter)
    print("Start search!")
    return jsonify({"output": server.get_output()})


@app.route("/get_result", methods=['POST'])
def get_result():
    return jsonify({"is_finished": server.is_finished(), "output": server.get_output()})


@app.route("/stop", methods=['POST'])
def stop():
    server.stop()
    return jsonify({"state": "ok"})


if __name__ == "__main__":
    if sys.platform.startswith('win'):
        # On Windows calling this function is necessary.
        multiprocessing.freeze_support()
    print("Start!")
    app.run(host='127.0.0.1', port=8765)
    print("Finished!")
