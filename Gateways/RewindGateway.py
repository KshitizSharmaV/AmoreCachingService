import asyncio
import json
import time
from redis.client import Redis
from ProjectConf.FirestoreConf import async_db, db
from logging import Logger

async def Rewind_task_function(current_user_id: str = None, swiped_user_id: str = None, redis_client: Redis = None, logger=None):
    """
    Rewind a user's swipe
        - remove the given swipe from collection
        - remove the received swipe from collection
    :param current_user_id: Current User's UID
    :param other_user_id: Other User's UID
    :return
    """
    given_swipe_task = asyncio.create_task(Rewind_given_swipe_task(current_user_id, swiped_user_id, redis_client, logger))
    received_swipe_task = asyncio.create_task(Rewind_received_swipe_task(current_user_id, swiped_user_id, redis_client))
    return await asyncio.gather(*[given_swipe_task, received_swipe_task])


async def Rewind_given_swipe_task(current_user_id: str = None, swiped_user_id: str = None, redis_client: Redis = None,logger: Logger = None):
    """
    Rewind a given swipe
        - remove the given swipe from collection
    :param current_user_id: Current User's UID
    :param swiped_user_id: Other User's UID
    :return
    """
    db.collection('LikesDislikes').document(current_user_id).collection("Given").document(swiped_user_id).delete()
    # TODO Delete the redis keys
    # keys_to_be_removed = [key for key in redis_client.scan_iter(f"LikesDislikes:{current_user_id}:Given:{swiped_user_id}*")]
    # logger.info(f"Current user id: {current_user_id}, swiped user id: {swiped_user_id}, keys to be removed: {keys_to_be_removed}")
    # no_of_keys_removed_from_redis = redis_client.delete(*keys_to_be_removed)
    return 

async def Rewind_received_swipe_task(current_user_id: str = None, swiped_user_id: str = None,redis_client: Redis = None):
    """
    Rewind a received swipe
        - remove the received swipe from collection
    :param current_user_id: Current User's UID
    :param swiped_user_id: Other User's UID
    :return
    """
    db.collection('LikesDislikes').document(swiped_user_id).collection("Received").document(current_user_id).delete()
    # TODO Delete the redis keys
    # keys_to_be_removed = [key for key in redis_client.scan_iter(f"LikesDislikes:{swiped_user_id}:Received:{current_user_id}*")]
    # logger.info(f"Current user id: {current_user_id}, swiped user id: {swiped_user_id}, keys to be removed: {keys_to_be_removed}")
    # no_of_keys_removed_from_redis = redis_client.delete(*keys_to_be_removed)
    return



