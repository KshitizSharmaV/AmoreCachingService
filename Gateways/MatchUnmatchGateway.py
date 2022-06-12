import asyncio
import json
import time
from google.cloud import firestore
from redis.client import Redis

from ProjectConf.FirestoreConf import async_db
from Gateways.RecentChatsGateway import RecentChats_Unmatch_Delete_Chat
from Gateways.LikesDislikesGatewayEXT import LikesDislikes_delete_record_from_redis, LikesDislikes_async_store_swipe_task

    
async def MatchUnmatch_unmatch_two_users(current_user_id: str = None, other_user_id: str = None, redisClient: Redis = None, logger=None):
    """
    Asynchronously performs following firestore tasks:
        - Query firestore for  current_user_id's match record for the other_user_id and fetch it.
        - Delete the above record from firestore.
        - Set the data from above record in Unmatch subcollection of current_user.
        - Delete the RecentChats record of other_user from the current_user's records and vice-versa.
    :param current_user_id: Current User's UID
    :param other_user_id: Other User's UID
    :return:
    """
    # sender
    task_likes_dislikes_current_user = asyncio.create_task(MatchUnmatch_unmatch_single_user(current_user_id, other_user_id, redisClient, logger))
    # receiver
    task_likes_dislikes_other_user = asyncio.create_task(MatchUnmatch_unmatch_single_user(other_user_id, current_user_id, redisClient, logger))
    task_recent_chats_current_user = asyncio.create_task(RecentChats_Unmatch_Delete_Chat(current_user_id, other_user_id, redisClient, logger))
    task_recent_chats_other_user = asyncio.create_task(RecentChats_Unmatch_Delete_Chat(other_user_id, current_user_id, redisClient, logger))
    return await asyncio.gather(*[task_likes_dislikes_current_user, 
                                task_likes_dislikes_other_user, 
                                task_recent_chats_current_user,
                                task_recent_chats_other_user])


async def MatchUnmatch_unmatch_single_user(user_id_1: str = None, user_id_2: str = None, redisClient: Redis = None, logger=None):
    try:
        """
        Unmatch performed in following order
            - Get the LikeDislikes Match Collection for first user
            - If exists
                - Step 1
                - Delete the above record from match collection
                - Write the record to Unmatch collection for user
                - Delete Match from redis
                - Write to Unmatch in redis
                - Step 2
                - Delete superlike/like in given of user in redis
                - Call LikesDislikes_async_store_swipe_task
                    - Update superlike/like to dislike in given of user in firestore
                    - Function will also re-write to redis cache
                - Step 3
                - Delete superlike/like in received of user in redis
                - Call LikesDislikes_async_store_swipe_task
                    - Update superlike/like to dislike in received of user in firestore
                    - Function will also re-write to redis cache
                
        :param user_id_1: Current User's UID
        :param user_id_2: Other User's UID
        :return:
        """
        match_ref = async_db.collection('LikesDislikes').document(user_id_1).collection("Match").document(user_id_2)
        match_doc = await match_ref.get()
        if match_doc.exists:
            # Step 1: Delete from Match and re-write to Unmatch for the profile ids
            # Write in other firestore collection for user
            match_doc = match_doc.to_dict()
            await match_ref.delete()
            unmatch_ref = async_db.collection('LikesDislikes').document(user_id_1).collection("Unmatch").document(user_id_2)
            await unmatch_ref.set(match_doc)
            # Delete Match from redis 
            wasDeleteSuccessful = await MatchUnmatch_delete_record_from_redis(user_id_1=user_id_1, 
                                                user_id_2 = user_id_2,
                                                childCollectionName="Match", 
                                                redisClient=redisClient, 
                                                logger=logger)
            # Write Unmatch to redis
            redisClient.sadd(f"MatchUnmatch:{user_id_1}:Unmatch",user_id_2)

            # Step 2: Delete from Likes or Superlikes in Given & Change to Dislikes
            # First try to delete from Given:Likes
            wasDeleteSuccess = await LikesDislikes_delete_record_from_redis(userId=user_id_1, idToBeDeleted=user_id_2, childCollectionName="Given", swipeStatusBetweenUsers="Likes", redisClient=redisClient,logger=logger)
            # If Id wasn't deleted above delete from Given:Superlikes
            if not wasDeleteSuccess:
                wasDeleteSuccess = await LikesDislikes_delete_record_from_redis(userId=user_id_1, idToBeDeleted=user_id_2, childCollectionName="Given", swipeStatusBetweenUsers="Superlikes", redisClient=redisClient, logger=logger)
            # Store the given swipe in firestore and redis
            _ = await LikesDislikes_async_store_swipe_task(firstUserId=user_id_1, 
                                                secondUserId=user_id_2, 
                                                childCollectionName="Given", 
                                                swipeStatusBetweenUsers="Dislikes", 
                                                redisClient=redisClient, 
                                                logger=logger)

            # Step 3: Delete from Likes or Superlikes in Received & Change to Dislikes
            # First try to delete from Received:Likes
            wasDeleteSuccess = await LikesDislikes_delete_record_from_redis(userId=user_id_2, idToBeDeleted=user_id_1, childCollectionName="Received", swipeStatusBetweenUsers="Likes", redisClient=redisClient,logger=logger)
            # If Id wasn't deleted above delete from Received:Superlikes
            if not wasDeleteSuccess:
                wasDeleteSuccess = await LikesDislikes_delete_record_from_redis(userId=user_id_2, idToBeDeleted=user_id_1, childCollectionName="Received", swipeStatusBetweenUsers="Superlikes", redisClient=redisClient, logger=logger)
            # Store the received swipe in firestore and redis
            _ = await LikesDislikes_async_store_swipe_task(firstUserId=user_id_2, 
                                                secondUserId=user_id_1, 
                                                childCollectionName="Received", 
                                                swipeStatusBetweenUsers="Dislikes", 
                                                redisClient=redisClient, 
                                                logger=logger)

            logger.info(f"Succesfully unmatched users {user_id_1} {user_id_2}")
        else:
            logger.warning(f"Unable to firestore match records {user_id_1} {user_id_2} in firestore")
        return True
    except Exception as e:
        logger.error(f"Unable to unmatch users {user_id_1} {user_id_2}")
        logger.exception(e)
        return False
    


async def MatchUnmatch_fetch_userdata_from_firebase_or_redis(userId=None, childCollectionName=None, redisClient=None, logger=None):
    '''
    Send back match unmatch for user
    If redis key MatchUnmatch:{userId}:{childCollectionName} Exist
        Load profiles from redis and send back
    Else:
        Load profiles from firestore
    params: userId
    params: childCollectionName: Match or Unmatch
    '''
    try:
        redisBaseKey = f"MatchUnmatch:{userId}:{childCollectionName}"
        # Check if LikesDislikes for profile already exist in cache
        if redisClient.scard(redisBaseKey) > 0:
            profileIds = await MatchUnmatch_fetch_data_from_redis(userId=userId, 
                                                            childCollectionName=childCollectionName, 
                                                            redisClient=redisClient, 
                                                            logger=logger)
            logger.info(f"{redisBaseKey} fetched {len(profileIds)} profiles from redis")
            return profileIds
        else:
            # If not fetch data from firestore & save it in cache
            docs = async_db.collection("LikesDislikes").document(userId).collection(childCollectionName).order_by(u'timestamp', direction=firestore.Query.DESCENDING)
            profileIds = await MatchUnmatch_store_match_unmatch_to_redis(docs=docs, userId=userId,
                                                                    childCollectionName=childCollectionName,
                                                                    redisClient=redisClient, 
                                                                    logger=logger)
            logger.info(f"{redisBaseKey} fetched {len(profileIds)} profiles from firestore")
            return profileIds
    except Exception as e:
        logger.error(f"LikesDislikes:{userId}:{childCollectionName} Failure to fetch likes dislikes data from firestore/cache")
        logger.exception(e)
        return []
    

async def MatchUnmatch_fetch_data_from_redis(userId=None, childCollectionName=None, redisClient=None, logger=None):
    '''
    Fetch match unmatch data from redis 
        : param userId: user id
        : param childCollectionName: Match or Unmatch
    '''
    try:
        redisBaseKey = f"MatchUnmatch:{userId}:{childCollectionName}"
        # Redis function 'smembers' will give you the length of set inside redis key
        profileIds = list(redisClient.smembers(redisBaseKey))
        logger.info(f"Fetched {len(profileIds)} from cache:{redisBaseKey}")
        return profileIds
    except Exception as e:
        logger.error(f"Unable to fetch LikesDislikes data from cache {redisBaseKey}")
        logger.exception(e)
        return []


async def MatchUnmatch_store_match_unmatch_to_redis(docs=None, userId=None, childCollectionName=None, redisClient=None, logger=None):
    '''
    MatchUnmatch:{userId}:{childCollectionName} store Match or Unmatch in firestore for user
        : param userId: user id
        : param docs: LikesDislikes collection, subcollection(Match/Unmatch) documents to iterate 
        : param childCollectionName: Match or Unmatch
    '''
    try:
        redisBaseKey = f"MatchUnmatch:{userId}:{childCollectionName}"
        profileIds = []
        async for doc in docs.stream():
            profileIds.append(doc.id)
            redisClient.sadd(redisBaseKey,doc.id)
            logger.info(f"{doc.id} was pushed to stack {redisBaseKey}")
        return profileIds
    except Exception as e:
        logger.error(f"MatchUnmatch:{userId}:{childCollectionName} Failure to store data to cache")
        logger.exception(e)
        return []


async def MatchUnmatch_delete_record_from_redis(user_id_1=None, user_id_2= None, childCollectionName=None, redisClient=None, logger=None):
    '''
    MatchUnmatch:{userId}:{childCollectionName} store Match or Unmatch in firestore for user
        : param user_id_1: user id 1
        : param user_id_2: user id 2
        : param childCollectionName: Match or Unmatch
    '''
    try:
        redisBaseKey = f"MatchUnmatch:{user_id_1}:{childCollectionName}"
        allUserMatchOrUnmatches = list(redisClient.smembers(redisBaseKey))
        if user_id_2 in allUserMatchOrUnmatches:
            redisClient.srem(redisBaseKey, user_id_2)
            logger.info(f"{user_id_2} was removed from {redisBaseKey}")
        else:
            logger.warning(f"{user_id_2} was not found in {redisBaseKey} to be deleted")
        return True
    except Exception as e:
        logger.error(f"Unable to delete {user_id_2} from key {redisBaseKey}")
        logger.exception(e)
        return False

