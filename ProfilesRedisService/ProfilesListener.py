import sys
import os.path

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

#################################################
###### Engine : Matching Engine
# Trigger this file to run Matching engine
#################################################
import os
import threading
import traceback
import time
import logging
from datetime import datetime
from ProjectConf.FirestoreConf import db
from ProjectConf.RedisConf import redisClient
from ProjectConf.AsyncioPlugin import run_coroutine
from logging.handlers import TimedRotatingFileHandler
from Gateways.GeoserviceEXTs.GeoserviceGatewayEXT import Profile
from Gateways.GeoserviceGateway import GeoService_store_profiles

# Log Settings
LOG_FILENAME = datetime.now().strftime("%H%M_%d%m%Y") + ".log"
if not os.path.exists('Logs/ProfilesRedisService/'):
    os.makedirs('Logs/ProfilesRedisService/')
logHandler = TimedRotatingFileHandler(f'Logs/ProfilesRedisService/{LOG_FILENAME}', when="midnight")
logFormatter = logging.Formatter(f'%(asctime)s %(levelname)s %(threadName)s : %(message)s')
logHandler.setFormatter(logFormatter)
logger = logging.getLogger(f'Logs/ProfilesRedisService/{LOG_FILENAME}')
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)


def on_create_or_update_profile(document):
    try:
        profile_data = Profile.encode_data_for_redis(document.to_dict())
        profile_data['id'] = document.id
        future = run_coroutine(GeoService_store_profiles(profile=profile_data, redisClient=redisClient, logger=logger))
        result = future.result()
    except Exception as e:
        logger.exception(e)
        logger.error("Error occurred while creating/updating redis Profiles Listener")
        logger.error(traceback.format_exc())


def on_delete_profile(document):
    try:
        deletion_hash_name = f"profile:{document.id}"
        redisClient.delete(deletion_hash_name)
    except Exception as e:
        logger.exception(e)
        logger.error("Error occurred while deleting redis Profiles Listener")
        logger.error(traceback.format_exc())


def profiles_action_on_change(change=None):
    try:
        if change.type.name == 'ADDED':
            logger.info(f'{change.document.id}: listener new profile was added')
            on_create_or_update_profile(document=change.document)
        elif change.type.name == 'MODIFIED':
            logger.info(f'{change.document.id}: listener profile was modified')
            on_create_or_update_profile(document=change.document)
        elif change.type.name == 'REMOVED':
            logger.info(f'{change.document.id}: listener profile was removed')
            on_delete_profile(document=change.document)
    except Exception as e:
        logger.exception(e)
        logger.error("Error occurred in profiles listener, change listener")
        logger.error(traceback.format_exc())
        return False

    # this function will be called every time firebase hears a change on a document in LikesDislikes


def profiles_listener(col_snapshot, changes, read_time):
    _ = [profiles_action_on_change(change=change) for change in changes]


callback_done = threading.Event()
if __name__ == '__main__':
    query_watch = None
    try:
        logger.info("Profiles Listener Engine Triggered")
        # Query the documents inside Profile collection
        col_query = db.collection(u'Profiles')
        # Watch the collection query
        query_watch = col_query.on_snapshot(profiles_listener)
        while True:
            time.sleep(1)
    except Exception as e:
        logger.exception(e)
        logger.error("Main: Error occurred in triggering Profiles Redis Service")
        logger.error(traceback.format_exc())
    finally:
        # Unsubscribe from all the listeners
        print("Finally was executed")
        logger.error("Error: Profiles Redis Service was unsubscribed from listener")
        query_watch.unsubscribe()
    callback_done.set()
