import logging
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create a console handler
ch = logging.StreamHandler(sys.stderr)
ch.setLevel(logging.DEBUG)

# create a formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(ch)



