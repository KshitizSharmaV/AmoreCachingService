import asyncio
import json
import time
from google.cloud import firestore
from redis.client import Redis
from ProjectConf.FirestoreConf import async_db
from Gateways.RecentChatsGateway import RecentChats_Unmatch_Delete_Chat

async def MatchUnmatch_unmatch_two_users(current_user_id: str = None, other_user_id: str = None, redis_client: Redis = None):
    """
    Asynchronously performs following firestore tasks:
        - Query firestore for current_user_id's match record for the other_user_id and fetch it.
        - Delete the above record from firestore.
        - Set the data from above record in Unmatch subcollection of current_user.
        - Delete the RecentChats record of other_user from the current_user's records and vice-versa.
    :param current_user_id: Current User's UID
    :param other_user_id: Other User's UID
    :return:
    """
    task_likes_dislikes_current_user = asyncio.create_task(MatchUnmatch_unmatch_single_user(current_user_id, other_user_id, redis_client))
    task_likes_dislikes_other_user = asyncio.create_task(MatchUnmatch_unmatch_single_user(other_user_id, current_user_id, redis_client))
    task_recent_chats_current_user = asyncio.create_task(RecentChats_Unmatch_Delete_Chat(current_user_id, other_user_id, redis_client))
    task_recent_chats_other_user = asyncio.create_task(RecentChats_Unmatch_Delete_Chat(other_user_id, current_user_id, redis_client))
    return await asyncio.gather(*[task_likes_dislikes_current_user, 
                                task_likes_dislikes_other_user, 
                                task_recent_chats_current_user,
                                task_recent_chats_other_user])

async def MatchUnmatch_unmatch_single_user(user_id_1: str = None, user_id_2: str = None, redis_client: Redis = None):
    """
    Unmatch performed in following order
        - Get the LikeDislikes Match Collection for first user
        - If exists
            - Delete the above record from match collection
            - Write the record to Unmatch collection for user
    :param user_id_1: Current User's UID
    :param user_id_2: Other User's UID
    :return:
    """
    match_ref = async_db.collection('LikesDislikes').document(user_id_1).collection("Match").document(user_id_2)
    match_doc = await match_ref.get()
    if match_doc.exists:
        match_doc = match_doc.to_dict()
        await match_ref.delete()
        unmatch_ref = async_db.collection('LikesDislikes').document(user_id_1).collection("Unmatch").document(user_id_2)
        await unmatch_ref.set(match_doc)
    return
        

async def MatchUnmatch_fetch_userdata_from_firebase_or_redis(userId=None, childCollectionName=None, redisClient=None, logger=None):
    '''
    Send back match unmatch for user
    If redis key MatchUmatch:{userId}:{childCollectionName} Exist
        Load profiles from redis and send back
    Else:
        Load profiles from firestore
    params: userId
    params: childCollectionName: Match or Unmatch
    '''
    try:
        redisBaseKey = f"MatchUmatch:{userId}:{childCollectionName}"
        # Check if LikesDislikes for profile already exist in cache
        if redisClient.scard(redisBaseKey) > 0:
            profileIds = await MatchUmatch_fetch_data_from_redis(userId=userId, 
                                                            childCollectionName=childCollectionName, 
                                                            redisClient=redisClient, 
                                                            logger=logger)
            logger.info(f"Fetching {len(profileIds)} MatchUmatch for {redisBaseKey} from redis")
            return profileIds
        else:
            # If not fetch data from firestore & save it in cache
            docs = async_db.collection("LikesDislikes").document(userId).collection(childCollectionName).order_by(u'timestamp', direction=firestore.Query.DESCENDING)
            profileIds = await MatchUnmatch_store_likes_dislikes_match_unmatch_to_redis(docs=docs, userId=userId,
                                                                    childCollectionName=childCollectionName,
                                                                    redisClient=redisClient, 
                                                                    logger=logger)
            logger.info(f"{redisBaseKey} match unmatch gate got {len(profileIds)} from firestore")
            return profileIds
    except Exception as e:
        logger.error(f"LikesDislikes:{userId}:{childCollectionName} Failure to fetch likes dislikes data from firestore/cache")
        logger.exception(e)
        return []
    pass

async def MatchUmatch_fetch_data_from_redis(userId=None, childCollectionName=None, redisClient=None, logger=None):
    '''
    Fetch match unmatch data from redis 
        : param userId: user id
        : param childCollectionName: Match or Unmatch
    '''
    try:
        redisBaseKey = f"MatchUmatch:{userId}:{childCollectionName}"
        # Redis function 'smembers' will give you the length of set inside redis key
        profileIds = list(redisClient.smembers(redisBaseKey))
        logger.info(f"Fetched {len(profileIds)} from cache:{redisBaseKey}")
        return profileIds
    except Exception as e:
        logger.error(f"Unable to fetch LikesDislikes data from cache {redisBaseKey}")
        logger.exception(e)
        return []


async def MatchUnmatch_store_likes_dislikes_match_unmatch_to_redis(docs=None, userId=None, childCollectionName=None, redisClient=None, logger=None):
    '''
    MatchUmatch:{userId}:{childCollectionName} store Match or Unmatch in firestore for user
        : param userId: user id
        : param docs: LikesDislikes collection, subcollection(Match/Unmatch) documents to iterate 
        : param childCollectionName: Match or Unmatch
    '''
    try:
        redisBaseKey = f"MatchUmatch:{userId}:{childCollectionName}"
        profileIds = []
        async for doc in docs.stream():
            profileIds.append(doc.id)
            redisClient.sadd(redisBaseKey,doc.id)
            logger.info(f"{doc.id} was pushed to stack {redisBaseKey}")
        return profileIds
    except Exception as e:
        logger.error(f"MatchUmatch:{userId}:{childCollectionName} Failure to store data to cache")
        logger.exception(e)
        return []