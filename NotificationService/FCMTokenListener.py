import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

import traceback
import os
import threading
import time
import logging
from time import strftime
from datetime import datetime
from dataclasses import asdict, dataclass
from logging.handlers import TimedRotatingFileHandler
from ProjectConf.FirestoreConf import db, async_db
from ProjectConf.AsyncioPlugin import run_coroutine
from google.cloud import firestore
from Gateways.NotificationGateway import Notification_store_fcm_token_in_redis
from ProjectConf.RedisConf import redisClient

# Log Settings
LOG_FILENAME = datetime.now().strftime("%H%M_%d%m%Y") + ".log"
if not os.path.exists('Logs/FCMTokenListener/'):
    os.makedirs('Logs/FCMTokenListener/')
logHandler = TimedRotatingFileHandler(f"Logs/FCMTokenListener/{LOG_FILENAME}",when="midnight")
logFormatter = logging.Formatter(f'%(asctime)s %(levelname)s %(threadName)s : %(message)s')
logHandler.setFormatter(logFormatter)
logger = logging.getLogger(f'Logs/FCMTokenListener/{LOG_FILENAME}')
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)


# Handles fcmtoken update in firestore
def fcm_token_update_handler(user_id=None):
    try:
        # We fetch only the new recent chats by Checking if otherUserUpdated is not True
        fcmTokens_stream = db.collection("FCMTokens").document(user_id).collection("Devices").stream()
        logger.info(f'Itering over device whose FCM tokens were updated')
        for document in fcmTokens_stream:
            # Encode the notification for redis and store it in there
            fcm_data = document.to_dict()
            # Get the device id
            fcm_data['deviceId'] = document.id
            fcm_data['userId'] = user_id
            # Get time in seconds 
            fcm_data['timestamp'] = fcm_data['timestamp'].timestamp()
            print(fcm_data)
            print(type(fcm_data))

            # If the record already exists the record will be overwritten
            future = run_coroutine(Notification_store_fcm_token_in_redis(fcm_data=fcm_data, redis_client=redisClient, logger=logger))
            result = future.result()
        # Set the wasUpdated = False, because we processed the change
        db.collection("FCMTokens").document(user_id).update({'wasUpdated':False})
        return
    except Exception as e:
        logger.error(f"{user_id}: Error occrured while processing the fcm token update in fcm_token_update_handler")
        logger.error(traceback.format_exc())
        return False               

# Here each change that is listened to is processed
# each change can be of 3 types Added, Modified or Removed, these are 3 properties of firebase itself
# we only want to action when a new message is sent
def fcm_token_update_check(change=None):
    try:
        if change.type.name == 'ADDED':
            logger.info(f'{change.document.id}: fcm token was added')
            fcm_token_update_handler(user_id=change.document.id)
        elif change.type.name == 'MODIFIED':
            logger.info(f'{change.document.id}: fcm token was modified')
        elif change.type.name == 'REMOVED':
            logger.info(f'{change.document.id}: fcm toke was removed/overwritten')
    except Exception as e:
        logger.error(f"{change.document.id}: Error occrured in the FCMTokenListener")
        logger.error(traceback.format_exc())
        return False

# this function will be called every time firebase hears a change on a document in FCMTokens
def fcm_token_update_listener(col_snapshot, changes, read_time):
    _ = [fcm_token_update_check(change=change) for change in changes]


callback_done = threading.Event()
if __name__ == '__main__':
    query_watch = None
    try:
        logger.info("FCMTokenListener Service Triggered")
        # Query the documents inside RecentChats collection where wasUpdated == true
        col_query = db.collection(u'FCMTokens').where(u'wasUpdated', '==', True)
        # Watch the collection query
        query_watch = col_query.on_snapshot(fcm_token_update_listener)
        while True:
            time.sleep(1)
    except Exception as e:
        logger.error("Main: Error occured in triggering FCMTokenListener Service")
        logger.error(traceback.format_exc())
        logger.warning("Main:Un-suscribed from FCMTokenListener Service")
    finally:
        # Unsuscribe from all the listeners
        print("Finally was executed")
        logger.error("Error: FCMTokenListener Service was Unsubscribed")
        query_watch.unsubscribe()
    callback_done.set()
