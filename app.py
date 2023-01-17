import flask
import sys
from flask import Flask
from ProjectConf.FirestoreConf import cred
import logging
import json
from appGet import app_get
from appSet import app_set
# Imports the Cloud Logging client library
import google.cloud.logging

app = Flask(__name__)

app.register_blueprint(app_get)
app.register_blueprint(app_set)

@app.before_first_request
def setup_logging():
    if not app.debug:
        # Instantiates a client
        client = google.cloud.logging.Client(credentials=cred.get_credential())

        # Retrieves a Cloud Logging handler based on the environment
        # you're running in and integrates the handler with the
        # Python logging module. By default this captures all logs
        # at INFO level and higher
        client.setup_logging()
        # In production mode, add log handler to sys.stderr.
        app.logger.setLevel(logging.INFO)
        app.logger.addHandler(logging.StreamHandler())

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
    app.run(host="127.0.0.1", port=5050, debug=True)
    app.logger.info("Starting Caching Service")






