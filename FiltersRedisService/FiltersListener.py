import sys
import os.path

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

#################################################
###### Engine : Matching Engine
# Trigger this file to run Matching engine
#################################################
import threading
import traceback
import time
from ProjectConf.FirestoreConf import db
from ProjectConf.RedisConf import redis_client
from ProjectConf.AsyncioPlugin import run_coroutine
from Gateways.ProfilesGatewayEXT import Profiles_store_profile_filters

from Utilities.LogSetup import configure_logger
logger = configure_logger(__name__)

def on_create_or_update_profile_filters(document):
    try:
        filter_data = document.to_dict()
        profile_id = document.id
        future = run_coroutine(Profiles_store_profile_filters(profile_id=profile_id, filter_data=filter_data))
        result = future.result()
    except Exception as e:
        logger.exception(e)
        logger.error("Error occurred while creating/updating redis Profile Filters Listener")
        logger.error(traceback.format_exc())


def on_delete_profile_filter(document):
    try:
        deletion_key = f"filter:{document.id}"
        redis_client.json().delete(deletion_key)
    except Exception as e:
        logger.exception(e)
        logger.error("Error occurred while deleting redis Profile Filters Listener")
        logger.error(traceback.format_exc())


def profile_filters_action_on_change(change=None):
    try:
        if change.type.name == 'ADDED':
            logger.info(f'{change.document.id}: listener new profile filter was added')
            on_create_or_update_profile_filters(document=change.document)
        elif change.type.name == 'MODIFIED':
            logger.info(f'{change.document.id}: listener profile filter was modified')
            on_create_or_update_profile_filters(document=change.document)
        elif change.type.name == 'REMOVED':
            logger.info(f'{change.document.id}: listener profile filter was removed')
            on_delete_profile_filter(document=change.document)
    except Exception as e:
        logger.exception(e)
        logger.error("Error occurred in profile filter listener, change listener")
        logger.error(traceback.format_exc())
        return False

    # this function will be called every time firebase hears a change on a document in LikesDislikes


def profile_filters_listener(col_snapshot, changes, read_time):
    _ = [profile_filters_action_on_change(change=change) for change in changes]


callback_done = threading.Event()
if __name__ == '__main__':
    query_watch = None
    try:
        logger.info("Profile Filters Listener Engine Triggered")
        # Query the documents inside FilterAndLocation collection
        col_query = db.collection(u'FilterAndLocation')
        # Watch the collection query
        query_watch = col_query.on_snapshot(profile_filters_listener)
        while True:
            time.sleep(1)
    except Exception as e:
        logger.exception(e)
        logger.error("Main: Error occurred in triggering Profile Filters Redis Service")
        logger.error(traceback.format_exc())
    finally:
        # Unsubscribe from all the listeners
        logger.error("Finally was executed")
        logger.error("Error: Profile Filters Redis Service was unsubscribed from listener")
        query_watch.unsubscribe()
    callback_done.set()
