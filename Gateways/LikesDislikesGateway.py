from gc import collect
from google.cloud import firestore
import asyncio
import time
import json
from ProjectConf.AsyncioPlugin import run_coroutine

'''
################################################
LikesDislikes Key Format
LikesDislikes:{userId}:{collectionNameChild}:{swipeStatusBetweenUsers}:{}
e.g. LikesDislikes:{userId}:Given:Likes
e.g. LikesDislikes:{userId}:Given:SuperLikes
e.g. LikesDislikes:{userId}:Given:Dislikes
The data stored with key is a list of ProfileIds who have liked, disliked or superliked
################################################
'''

# Store likesdislikes data in firestore: We store this swipe at multiple places which will allows easy logic building
async def LikesDislikes_async_store_likes_dislikes_superlikes_for_user(currentUserId=None, swipedUserId=None, swipeStatusBetweenUsers=None, async_db=None, redisClient=None, logger=None):
    try:
        # Set the update flag for MatchingEngine
        task1 = asyncio.create_task(LikesDislikes_async_store_likesdislikes_updated(currentUserId=currentUserId, async_db=async_db, logger=logger))
        # Store given swipe task
        task2 = asyncio.create_task(LikesDislikes_async_store_swipe_task(firstUserId=currentUserId, 
                                                                        secondUserId=swipedUserId,
                                                                        collectionNameChild="Given", 
                                                                        swipeStatusBetweenUsers=swipeStatusBetweenUsers,
                                                                        async_db=async_db, redisClient=redisClient, logger=logger))
        # Store recevied swipe task
        task3 = asyncio.create_task(LikesDislikes_async_store_swipe_task(firstUserId=swipedUserId , 
                                                                        secondUserId=currentUserId,
                                                                        collectionNameChild="Received", 
                                                                        swipeStatusBetweenUsers=swipeStatusBetweenUsers,
                                                                        async_db=async_db, redisClient=redisClient, logger=logger))
                                                                    
        return asyncio.gather(*[task1, task2, task3])
    except Exception as e:
        logger.error(f"Failed to store the async likesdislikes swipe in firestore/redis")
        logger.exception(e)
        return []

# Store data in likesdislikes collection of the user who have the swipe
# done for ease of read & build easy logics around different business use cases
async def LikesDislikes_async_store_swipe_task(firstUserId=None, secondUserId=None, collectionNameChild=None, swipeStatusBetweenUsers=None, 
                                                async_db=None, redisClient=None, logger=None):
    '''
    Store the given swipe in firestore and redis
    '''
    try:
        redisBaseKey = f"LikesDislikes:{firstUserId}:{collectionNameChild}:{swipeStatusBetweenUsers}"
        storeData = {"swipe": swipeStatusBetweenUsers, "timestamp": time.time(), 'matchVerified': False}
        await async_db.collection('LikesDislikes').document(firstUserId).collection(collectionNameChild).document(secondUserId).set(storeData)
        redisClient.lpush(redisBaseKey,secondUserId)
        logger.info(f"{redisBaseKey} successfully stored {secondUserId} in firestore/redis")
        return True
    except Exception as e:
        logger.error(f"{redisBaseKey} failed stored {secondUserId} in firestore/reds")
        logger.exception(e)
        return False

# Set the update flag for MatchingEngine
async def LikesDislikes_async_store_likesdislikes_updated(currentUserId=None, async_db=None, logger=None):
    '''
    IMPT: 
    Sets the wasUpdated field to True in firestore only under the Profile collection
    There is a firestore listener on wasUpdated which is used by Matching Algorithm to process matches
    '''
    await async_db.collection('LikesDislikes').document(currentUserId).set({"wasUpdated": True})


def LikesDislikes_fetch_Userdata_from_firebase_or_redis(userId=None, collectionNameChild=None, swipeStatusBetweenUsers=None, db=None,redisClient=None, logger=None):
    '''
    Function is called from appGet to fetch Likesdislikes for a user
    Function returns list of profileIds under Given, Match, Received, Unmatch either from cache or firebase
    Function is also responsible for loading likesdislikes under a category for user
    collectionNameChild: Given, Match, Received, Unmatch

    First check if the LikesDislikes:{UserId}:Given already exists in the cache
    If exist send it back, since LikesDislikes is a write through cache, it's the most updated data
    If doesn't exist fetch data from firestore and save the data to cache
    '''
    try:
        redisBaseKey = f"LikesDislikes:{userId}:{collectionNameChild}:{swipeStatusBetweenUsers}"
        # Check if Likesdislikes for profile already exist in cache
        if redisClient.llen(redisBaseKey) > 0:
            profileIds = LikesDislikes_fetch_data_from_redis(userId=userId, 
                                                            collectioNameChild=collectionNameChild, 
                                                            swipeStatusBetweenUsers=swipeStatusBetweenUsers,
                                                            redisClient=redisClient, 
                                                            logger=logger)
            return profileIds
        else:
            # If not fetch data from firestore & save it in cache
            docs = db.collection("LikesDislikes").document(userId).collection(collectionNameChild). \
                where(u'swipe', u'==', swipeStatusBetweenUsers).order_by(u'timestamp', direction=firestore.Query.DESCENDING)
            profileIds = LikesDislikes_store_likes_dislikes_match_unmatch_to_redis(docs=docs, userId=userId,
                                                                    collectionNameChild=collectionNameChild,
                                                                    redisClient=redisClient, logger=logger)
            return profileIds
    except Exception as e:
        logger.error(f"LikesDislikes:{userId}:{collectionNameChild} Failure to fetch likes dislikes data from firstore")
        logger.exception(e)
        return []



def LikesDislikes_store_likes_dislikes_match_unmatch_to_redis(docs=None, userId=None, collectionNameChild=None, redisClient=None, logger=None):
    '''
    Data stored in these redis key is a list of ProfileIds
    LikedDislikes Redis Key is a key which store list of ProfileIds
    Accepts firestore stream object of LikesDislikes and save it to cache
    Once you fetch the LikesDislikes for user from firestore, call this function to save data in redis
    '''
    try:
        redisBaseKey = f"LikesDislikes:{userId}:{collectionNameChild}"
        profileIds = []
        for doc in docs.stream():
            profileId = doc.id
            profileIds.append(profileId)
            dictDoc = doc.to_dict()
            jsonObject_dumps = json.dumps(dictDoc, indent=4, sort_keys=True, default=str)
            # Fetch if the Other User received a Like, SuperLike or Dislike inside a Given, Received collection
            swipeStatusBetweenUsers = dictDoc["swipe"] if "swipe" in dictDoc else collectionNameChild
            completeRedisKey = f"{redisBaseKey}:{swipeStatusBetweenUsers}"
            # Push multiple values through the HEAD of the list
            redisClient.lpush(completeRedisKey,profileId)
            logger.info(f"{profileId} was pushed to stack {completeRedisKey}")
        return profileIds
    except Exception as e:
        logger.error(f"LikesDislikes:{userId}:{collectionNameChild} Failure to store data to cache")
        logger.exception(e)
        return []


def LikesDislikes_fetch_data_from_redis(userId=None, collectioNameChild=None, swipeStatusBetweenUsers=None, redisClient=None, logger=None):
    '''
    Pass in the User ID and the parameters you want LikesDislikes to filter on
    Returns a list of Profile Ids for that user under a category 
    '''
    try:
        redisBaseKey = f"LikesDislikes:{userId}:{collectioNameChild}:{swipeStatusBetweenUsers}"
        profileIds = []
        # Redis function 'llen' will give you the length of list items inside redis key
        _ = [profileIds.append(redisClient.lindex(redisBaseKey,i)) for i in range(0, redisClient.llen(redisBaseKey))]
        logger.info(f"Fetched {len(profileIds)} from cache:{redisBaseKey}")
        return profileIds
    except Exception as e:
        logger.error(f"Unable to fetch likesdislikes data from cache {redisBaseKey}")
        logger.exception(e)
        return []



# Function not in use
# # Unmatch from a user
# # Not in use
# async def async_store_unmatch_task_likes_dislikes(userId1=None, userId2=None, async_db=None):
#     '''
#     Unmatches 2 users in firestore
#     TODO : also modify the redis - KTZ
#     '''
#     match_ref = async_db.collection('LikesDislikes').document(userId1).collection("Match").document(userId2)
#     match_doc = await match_ref.get()
#     if match_doc.exists:
#         match_doc = match_doc.to_dict()
#         await match_ref.delete()
#         unmatch_ref = async_db.collection('LikesDislikes').document(userId1).collection("Unmatch").document(userId2)
#         await unmatch_ref.set(match_doc)
