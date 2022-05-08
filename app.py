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

# # Log Settings
LOG_FILENAME = datetime.now().strftime("%H_%M_%d_%m_%Y")+".log"
if not os.path.exists('Logs/AppLogs/'):
    os.makedirs('Logs/AppLogs/')
log_level = "DEBUG"
class LoggerConfig:
    dictConfig = {
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] {%(pathname)s:%(funcName)s:%(lineno)d} %(levelname)s - %(message)s',
        }},
        'handlers': {'default': {
                    'level': 'DEBUG',
                    'formatter': 'default',
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': f'Logs/AppLogs/{LOG_FILENAME}',
                    'maxBytes': 5000000,
                    'backupCount': 10
                }},
        'root': {
            'level': log_level,
            'handlers': ['default']
        },
    }

logging.config.dictConfig(LoggerConfig.dictConfig)
logger = logging.getLogger()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8800, debug=True)
    logger.info("Starting Caching Service")






