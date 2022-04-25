import os
import logging
from logging.handlers import TimedRotatingFileHandler

# format the log entries
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
# TimeRotatingHandler to auto save log file with the date
if not os.path.exists("../Logs/"):
    os.makedirs("../Logs/")
handler = TimedRotatingFileHandler('../Logs/authentication.log', when='midnight', backupCount=20)
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)