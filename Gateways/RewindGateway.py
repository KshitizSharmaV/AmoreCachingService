import asyncio
import json
import time
from redis.client import Redis
from ProjectConf.FirestoreConf import async_db, db
from google.cloud import firestore
from Gateways.LikesDislikesGatewayEXT import LikesDislikes_delete_record_from_redis
from logging import Logger

async def Rewind_task_function(current_user_id: str = None, swiped_user_id: str = None, swipeStatusBetweenUsers=None, logger=None):
    """
    Rewind a user's swipe
        - remove the given swipe from collection
        - remove the received swipe from collection
        - return the profile back to client
    :param current_user_id: Current User's UID
    :param other_user_id: Other User's UID
    :return
    """
    try:
        given_swipe_task = asyncio.create_task(Rewind_given_swipe_task(current_user_id=current_user_id, 
                                                                    swiped_user_id=swiped_user_id, 
                                                                    swipeStatusBetweenUsers=swipeStatusBetweenUsers, 
                                                                    logger=logger))
        
        received_swipe_task = asyncio.create_task(Rewind_received_swipe_task(current_user_id=current_user_id, 
                                                                    swiped_user_id=swiped_user_id, 
                                                                    swipeStatusBetweenUsers=swipeStatusBetweenUsers, 
                                                                    logger=logger))
        return await asyncio.gather(*[given_swipe_task, received_swipe_task])
    except Exception as e:
        logger.error(f"Unable to delete likesdislikes for {current_user_id} {swiped_user_id} {swipeStatusBetweenUsers}")
        logger.exception(e)
        return False

async def Rewind_given_swipe_task(current_user_id: str = None, swiped_user_id: str = None, swipeStatusBetweenUsers=None, logger: Logger = None):
    """
    Rewind a given swipe
        - remove the given swipe from collection
    :param current_user_id: Current User's UID
    :param swiped_user_id: Other User's UID
    :return
    """
    try:
        await async_db.collection('LikesDislikes').document(current_user_id).collection("Given").document(swiped_user_id).delete()
        await LikesDislikes_delete_record_from_redis(userId=current_user_id, 
                                            idToBeDeleted=swiped_user_id, 
                                            childCollectionName="Given", 
                                            swipeStatusBetweenUsers=swipeStatusBetweenUsers, 
                                            logger=logger)
        return True
    except Exception as e:
        logger.exception(e)
        return False

async def Rewind_received_swipe_task(current_user_id: str = None, swiped_user_id: str = None, swipeStatusBetweenUsers=None, logger: Logger = None):
    """
    Rewind a received swipe
        - remove the received swipe from collection
    :param current_user_id: Current User's UID
    :param swiped_user_id: Other User's UID
    :return
    """
    try:
        await async_db.collection('LikesDislikes').document(swiped_user_id).collection("Received").document(current_user_id).delete()
        await LikesDislikes_delete_record_from_redis(userId=swiped_user_id, 
                                            idToBeDeleted=current_user_id, 
                                            childCollectionName="Received", 
                                            swipeStatusBetweenUsers=swipeStatusBetweenUsers, 
                                            logger=logger)
        return True
    except Exception as e:
        logger.exception(e)
        return False
    return

def get_last_given_swipe_from_firestore(current_user_id):
    last_swipe_doc = db.collection('LikesDislikes').document(current_user_id).collection('Given').order_by(u'timestamp', direction=firestore.Query.DESCENDING).limit(1)
    last_swipe_doc = last_swipe_doc.stream()
    last_swipe_doc = [doc for doc in last_swipe_doc][0]
    last_swiped_id = last_swipe_doc.id
    last_swiped_info = last_swipe_doc.to_dict()['swipe']
    return last_swiped_id, last_swiped_info
