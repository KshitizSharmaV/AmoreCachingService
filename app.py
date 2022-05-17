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
from ProjectConf.ReddisConf import redisClient

app = Flask(__name__)

with app.app_context():
    from appGet import app_get
    from appSet import app_set

LOGGING_CONFIG = { 
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': { 
        'standard': { 
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': { 
        'default': { 
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
    },
    'loggers': { 
        '': {  # root logger
            'handlers': ['default'],
            'level': 'WARNING',
            'propagate': False
        },
        'my.packg': { 
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        },
        '__main__': {  # if __name__ == '__main__'
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False
        },
    } 
}

logging.config.dictConfig(LOGGING_CONFIG)
app.logger.info('Config')

import json
@app.route("/test", methods=["Get"])
def test():
    try:
        app.logger.info("Test For Amore Caching Service")
        redisClient.incr('hits')
        getter = redisClient.get('hits')
        if type(getter) is str:
            counter = getter
        else:
            counter = str(getter, 'utf-8')
        return "This webpage has been viewed "+counter+" time(s)"
        # return json.dumps({"status":True, "service":"Amore Caching Service"})
    except Exception as e:
        app.logger.exception("Failed to get Amore Caching Service Started")
        app.logger.exception(e)
    return flask.abort(401, 'An error occured in API /test')


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
    app.logger.info("Starting Caching Service")






