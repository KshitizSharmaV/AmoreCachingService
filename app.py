from genericpath import exists
import flask
from flask import Flask, jsonify, request
import traceback
import time
from datetime import datetime
import logging.config
import os
from logging.handlers import TimedRotatingFileHandler
import json
# from bson import json_util
import asyncio

app = Flask(__name__)

with app.app_context():
    from appGet import app_get
    from appSet import app_set

@app.before_first_request
def setup_logging():
    if not app.debug:
        # In production mode, add log handler to sys.stderr.
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)

import json
@app.route("/test", methods=["Get"])
def test():
    try:
        app.logger.info("Test For Amore Caching Service")
        return json.dumps({"status":True, "service":"Amore Caching Service"})
    except Exception as e:
        app.logger.exception("Failed to get Amore Caching Service Started")
        app.logger.exception(e)
    return flask.abort(401, 'An error occured in API /test')


if __name__ == '__main__':
    # app.run(host="0.0.0.0", debug=True)
    app.run(host="127.0.0.1", port=5050, debug=True)
    app.logger.info("Starting Caching Service")






