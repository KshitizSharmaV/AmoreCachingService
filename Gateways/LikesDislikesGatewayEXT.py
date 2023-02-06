from ProjectConf.FirestoreConf import async_db
from google.cloud import firestore
import time
import asyncio
from ProjectConf.RedisConf import redis_client
from Utilities.LogSetup import configure_logger

logger = configure_logger(__name__)
async def LikesDislikes_fetch_userdata_from_firebase_or_redis(userId=None, childCollectionName=None,
                                                              swipeStatusBetweenUsers=None,
                                                              no_of_last_records=None):
    '''
    LikesDislikes:{userId}:{childCollectionName}:{swipeStatusBetweenUsers}:{}
    Function is called from appGet to fetch Likesdislikes for a user
    Function returns list of profileIds under Given, Match, Received, Unmatch either from cache or firebase
    Function is also responsible for loading likesdislikes under a category for user
    childCollectionName: Given, Match, Received, Unmatch

    First check if the LikesDislikes:{UserId}:Given already exists in the cache
    If exist send it back, since LikesDislikes is a write through cache, it's the most updated data
    If doesn't exist fetch data from firestore and save the data to cache
    '''
    try:
        profileIds = []
        redisBaseKey = f"LikesDislikes:{userId}:{childCollectionName}:{swipeStatusBetweenUsers}"
        # Check if Likesdislikes for profile already exist in cache
        if redis_client.zcard(redisBaseKey) > 0:
            logger.info(f"Fetching LikesDislikes for {redisBaseKey} from redis")
            profileIds = await LikesDislikes_fetch_data_from_redis(userId=userId,
                                                                   childCollectionName=childCollectionName,
                                                                   swipeStatusBetweenUsers=swipeStatusBetweenUsers,
                                                                   no_of_last_records=no_of_last_records)
        else:
            # If not fetch data from firestore & save it in cache
            logger.info(f"Fetching LikesDislikes for {redisBaseKey} from firestore")
            docs = async_db.collection("LikesDislikes").document(userId).collection(childCollectionName). \
                where(u'swipe', u'==', swipeStatusBetweenUsers).order_by(u'timestamp',
                                                                         direction=firestore.Query.DESCENDING)
            # Pull all records, regardless of no_of_last_records parameter, since we're populating the redis for the first time
            profileIds = await LikesDislikes_store_likes_dislikes_match_unmatch_to_redis(docs=docs, userId=userId,
                                                                                         childCollectionName=childCollectionName)
        profileIds = profileIds[:no_of_last_records] if no_of_last_records else profileIds
        return profileIds
    except Exception as e:
        logger.error(
            f"LikesDislikes:{userId}:{childCollectionName} Failure to fetch likes dislikes data from firestore/cache")
        logger.exception(e)
        return []


async def LikesDislikes_fetch_data_from_redis(userId=None, childCollectionName=None, swipeStatusBetweenUsers=None, no_of_last_records=None):
    '''
    Pass in the User ID and the parameters you want LikesDislikes to filter on

    Args:
        userId
        childCollectionName
        swipeStatusBetweenUsers
        no_of_last_records
    
    Returns:
        Returns a list of Profile Ids for that user under a category 
    '''
    try:
        redisBaseKey = f"LikesDislikes:{userId}:{childCollectionName}:{swipeStatusBetweenUsers}"
        # Pull top given number of LikesDislikes based on timestamp (descending)
        if no_of_last_records:
            profileIds = redis_client.zrevrange(redisBaseKey, 0, no_of_last_records)
        else:
            profileIds = redis_client.zrevrange(redisBaseKey, 0, -1)
        logger.info(f"Fetched {len(profileIds)} from cache:{redisBaseKey}")
        return profileIds
    except Exception as e:
        logger.error(f"Unable to fetch likesdislikes data from cache {redisBaseKey}")
        logger.exception(e)
        return []


async def LikesDislikes_store_likes_dislikes_match_unmatch_to_redis(docs=None, userId=None, childCollectionName=None):
    '''
    LikesDislikes:{userId}:{childCollectionName}:{swipeStatusBetweenUsers}:{}
    Store likesdislikes to redis
    LikedDislikes Redis Key is a key which store list of ProfileIds
        :param: docs - Accepts firestore stream object of LikesDislikes and save it to cache
        :param: userId - Id of the user whose Likedislikes need to be saved
        :param: childCollectionName: Match or Unmatch; Collection name in firestore
    Once you fetch the LikesDislikes for user from firestore, call this function to save data in redis
    '''
    try:
        redisBaseKey = f"LikesDislikes:{userId}:{childCollectionName}"
        profileIds = []
        async for doc in docs.stream():
            profileId = doc.id
            profileIds.append(profileId)
            dictDoc = doc.to_dict()
            # Fetch if the Other User received a Like, SuperLikes or Dislike inside a Given, Received collection
            swipe_timestamp = dictDoc.get("timestamp")
            swipeStatusBetweenUsers = dictDoc["swipe"] if "swipe" in dictDoc else childCollectionName
            completeRedisKey = f"{redisBaseKey}:{swipeStatusBetweenUsers}"
            # Push multiple values through the HEAD of the list
            # redis_client.sadd(completeRedisKey,profileId)
            # zadd(key, score, record)
            redis_client.zadd(completeRedisKey, {profileId: swipe_timestamp})
            logger.info(f"{profileId} was pushed to stack {completeRedisKey}")
        return profileIds
    except Exception as e:
        logger.error(
            f"LikesDislikes:{userId}:{childCollectionName} Failure to fetch from firestore and store data to cache")
        logger.exception(e)
        return []


async def LikesDislikes_delete_record_from_redis(userId=None, idToBeDeleted=None, childCollectionName=None, swipeStatusBetweenUsers=None):
    '''
    MatchUnmatch:{userId}:{childCollectionName} store Match or Unmatch in firestore for user
        : param userId: Redis Key To be deleted from
        : param idToBeDeleted: id to be deleted
        : param childCollectionName: Match or Unmatch
        : swipeStatusBetweenUsers: Likes, Superlikes or Dislikes
    '''
    try:
        redisBaseKey = f"LikesDislikes:{userId}:{childCollectionName}:{swipeStatusBetweenUsers}"
        allUserMatchOrUnmatches = redis_client.zrevrange(redisBaseKey, 0, -1)
        if idToBeDeleted in allUserMatchOrUnmatches:
            redis_client.zrem(redisBaseKey, idToBeDeleted)
            logger.info(f"{idToBeDeleted} was removed from {redisBaseKey}")
            return True
        else:
            logger.warning(f"{idToBeDeleted} was not found in {redisBaseKey} to be deleted")
            return False
    except Exception as e:
        logger.error(f"Unable to delete {idToBeDeleted} from key {redisBaseKey}")
        logger.exception(e)
        return False


# Store data in likesdislikes collection of the user who have the swipe
# done for ease of read & build easy logics around different business use cases
async def LikesDislikes_async_store_swipe_task(firstUserId=None, secondUserId=None, childCollectionName=None, swipeStatusBetweenUsers=None, upgradeLikeToSuperlike=None):
    '''
    Store the given swipe in firestore and redis
    '''
    try:
        redisBaseKey = f"LikesDislikes:{firstUserId}:{childCollectionName}:{swipeStatusBetweenUsers}"
        swipe_timestamp = time.time()
        storeData = {"swipe": swipeStatusBetweenUsers, "timestamp": swipe_timestamp, 'matchVerified': False}
        await async_db.collection('LikesDislikes').document(firstUserId).collection(childCollectionName).document(secondUserId).set(storeData)
        if upgradeLikeToSuperlike:
            redis_client.zrem(f"LikesDislikes:{firstUserId}:{childCollectionName}:Likes", secondUserId)
            logger.info(f"Removed Like from {firstUserId} for {secondUserId}")
        redis_client.zadd(redisBaseKey, {secondUserId: swipe_timestamp})
        logger.info(f"Added {swipeStatusBetweenUsers} from {firstUserId} for {secondUserId}")
        logger.info(f"{redisBaseKey} successfully stored {secondUserId} in firestore/redis")
        return True
    except Exception as e:
        logger.error(f"{redisBaseKey} failed stored {secondUserId} in firestore/reds")
        logger.exception(e)
        return False


async def LikesDislikes_fetch_users_given_swipes(user_id):
    """
    Fetch Likes, Dislikes and Superlikes given by the user_id

    Args: 
        user_id

    Returns:
        Returns the list of profile ids
    """
    try:
        return await asyncio.gather(
            *[LikesDislikes_fetch_userdata_from_firebase_or_redis(userId=user_id, childCollectionName="Given",
                                                                  swipeStatusBetweenUsers=swipe_info) for
              swipe_info in ['Likes', 'Dislikes', 'Superlikes']])
    except Exception as e:
        logger.error(f"Unable to fetch given swipes by user {user_id}")
        logger.exception(e)
        return False
