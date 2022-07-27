from ProjectConf.FirestoreConf import async_db
from google.cloud import firestore
import time
from redis import Redis

async def LikesDislikes_fetch_userdata_from_firebase_or_redis(userId=None, childCollectionName=None, swipeStatusBetweenUsers=None, redisClient=None, logger=None):
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
        redisBaseKey = f"LikesDislikes:{userId}:{childCollectionName}:{swipeStatusBetweenUsers}"
        # Check if Likesdislikes for profile already exist in cache
        if redisClient.scard(redisBaseKey) > 0:
            logger.info(f"Fetching LikesDislikes for {redisBaseKey} from redis")
            profileIds = await LikesDislikes_fetch_data_from_redis(userId=userId, 
                                                            childCollectionName=childCollectionName, 
                                                            swipeStatusBetweenUsers=swipeStatusBetweenUsers,
                                                            redisClient=redisClient, 
                                                            logger=logger)
            return profileIds
        else:
            # If not fetch data from firestore & save it in cache
            logger.info(f"Fetching LikesDislikes for {redisBaseKey} from firestore")
            docs = async_db.collection("LikesDislikes").document(userId).collection(childCollectionName). \
                where(u'swipe', u'==', swipeStatusBetweenUsers).order_by(u'timestamp', direction=firestore.Query.DESCENDING)
            profileIds = await LikesDislikes_store_likes_dislikes_match_unmatch_to_redis(docs=docs, userId=userId,
                                                                    childCollectionName=childCollectionName,
                                                                    redisClient=redisClient, logger=logger)
            return profileIds
    except Exception as e:
        logger.error(f"LikesDislikes:{userId}:{childCollectionName} Failure to fetch likes dislikes data from firestore/cache")
        logger.exception(e)
        return []

async def LikesDislikes_fetch_data_from_redis(userId=None, childCollectionName=None, swipeStatusBetweenUsers=None, redisClient=None, logger=None):
    '''
    Pass in the User ID and the parameters you want LikesDislikes to filter on
    Returns a list of Profile Ids for that user under a category 
    '''
    try:
        redisBaseKey = f"LikesDislikes:{userId}:{childCollectionName}:{swipeStatusBetweenUsers}"
        # Redis function 'smembers' will give you the length of set inside redis key
        profileIds = list(redisClient.smembers(redisBaseKey))
        logger.info(f"Fetched {len(profileIds)} from cache:{redisBaseKey}")
        return profileIds
    except Exception as e:
        logger.error(f"Unable to fetch likesdislikes data from cache {redisBaseKey}")
        logger.exception(e)
        return []

async def LikesDislikes_store_likes_dislikes_match_unmatch_to_redis(docs=None, userId=None, childCollectionName=None, redisClient=None, logger=None):
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
            swipeStatusBetweenUsers = dictDoc["swipe"] if "swipe" in dictDoc else childCollectionName
            completeRedisKey = f"{redisBaseKey}:{swipeStatusBetweenUsers}"
            # Push multiple values through the HEAD of the list
            redisClient.sadd(completeRedisKey,profileId)
            logger.info(f"{profileId} was pushed to stack {completeRedisKey}")
        return profileIds
    except Exception as e:
        logger.error(f"LikesDislikes:{userId}:{childCollectionName} Failure to store data to cache")
        logger.exception(e)
        return []

async def LikesDislikes_delete_record_from_redis(userId=None, idToBeDeleted=None, childCollectionName=None, swipeStatusBetweenUsers=None, redisClient=None,logger=None):
    '''
    MatchUnmatch:{userId}:{childCollectionName} store Match or Unmatch in firestore for user
        : param userId: Redis Key To be deleted from
        : param idToBeDeleted: id to be deleted
        : param childCollectionName: Match or Unmatch
        : swipeStatusBetweenUsers: Likes, Superlikes or Dislikes
    '''
    try:
        redisBaseKey = f"LikesDislikes:{userId}:{childCollectionName}:{swipeStatusBetweenUsers}"
        allUserMatchOrUnmatches = list(redisClient.smembers(redisBaseKey))
        if idToBeDeleted in allUserMatchOrUnmatches:
            redisClient.srem(redisBaseKey, idToBeDeleted)
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
async def LikesDislikes_async_store_swipe_task(firstUserId=None, secondUserId=None, childCollectionName=None,
                                               swipeStatusBetweenUsers=None, upgradeLikeToSuperlike=None,
                                               redisClient: Redis = None, logger=None):
    '''
    Store the given swipe in firestore and redis
    '''
    try:
        redisBaseKey = f"LikesDislikes:{firstUserId}:{childCollectionName}:{swipeStatusBetweenUsers}"
        storeData = {"swipe": swipeStatusBetweenUsers, "timestamp": time.time(), 'matchVerified': False}
        await async_db.collection('LikesDislikes').document(firstUserId).collection(childCollectionName).document(
            secondUserId).set(storeData)
        if upgradeLikeToSuperlike:
            redisClient.srem(f"LikesDislikes:{firstUserId}:{childCollectionName}:Likes", secondUserId)
            logger.info(f"Removed Like from {firstUserId} for {secondUserId}")
        redisClient.sadd(redisBaseKey, secondUserId)
        logger.info(f"Added {swipeStatusBetweenUsers} from {firstUserId} for {secondUserId}")
        logger.info(f"{redisBaseKey} successfully stored {secondUserId} in firestore/redis")
        return True
    except Exception as e:
        logger.error(f"{redisBaseKey} failed stored {secondUserId} in firestore/reds")
        logger.exception(e)
        return False
