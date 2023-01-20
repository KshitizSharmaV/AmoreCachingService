import flask
import sys
from flask import Flask
import logging.config
import json
from appGet import app_get
from appSet import app_set
from Utilities.LogSetup import logger

app = Flask(__name__)

app.register_blueprint(app_get)
app.register_blueprint(app_set)

# @app.before_first_request
# def setup_logging():
#     if not app.debug:
#         # In production mode, add log handler to sys.stderr.
#         app.logger.addHandler(logging.StreamHandler(sys.stderr))
#         app.logger.setLevel(logging.INFO)

import json
@app.route("/test", methods=["Get"])
def test():
    try:
        logger.info("Test For Amore Caching Service")
        return json.dumps({"status":True, "service":"Amore Caching Service"})
    except Exception as e:
        logger.exception("Failed to get Amore Caching Service Started")
        logger.exception(e)
    return flask.abort(401, 'An error occured in API /test')


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5050, debug=True)
    logger.info("Starting Caching Service")






