from gc import collect
from google.cloud import firestore
import asyncio
import time
import json

from ProjectConf.AsyncioPlugin import run_coroutine
from ProjectConf.FirestoreConf import async_db, db
from Gateways.MatchUnmatchGatewayEXT import MatchUnmatch_check_match_between_users
from Gateways.LikesDislikesGatewayEXT import LikesDislikes_fetch_userdata_from_firebase_or_redis

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
    '''
    Store like in Given for user
    Store like in Receiver for profile receiving the swipe 
    Check for a match & if match write to firestore 
        :param currentUserId
        :param swipedUserId
        :param swipeStatusBetweenUsers
    '''
    try:
        # Store given swipe task
        task1 = asyncio.create_task(LikesDislikes_async_store_swipe_task(firstUserId=currentUserId, 
                                                                        secondUserId=swipedUserId,
                                                                        collectionNameChild="Given", 
                                                                        swipeStatusBetweenUsers=swipeStatusBetweenUsers,
                                                                        async_db=async_db, redisClient=redisClient, logger=logger))
        # Store recevied swipe task
        task2 = asyncio.create_task(LikesDislikes_async_store_swipe_task(firstUserId=swipedUserId , 
                                                                        secondUserId=currentUserId,
                                                                        collectionNameChild="Received", 
                                                                        swipeStatusBetweenUsers=swipeStatusBetweenUsers,
                                                                        async_db=async_db, redisClient=redisClient, logger=logger))
    
        task3 = asyncio.create_task(MatchUnmatch_check_match_between_users(currentUserId=currentUserId,
                                                                        swipedUserId=swipedUserId,
                                                                        currentUserSwipe=swipeStatusBetweenUsers,
                                                                        redisClient=redisClient, 
                                                                        logger=logger))
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
        redisClient.sadd(redisBaseKey,secondUserId)
        logger.info(f"{redisBaseKey} successfully stored {secondUserId} in firestore/redis")
        return True
    except Exception as e:
        logger.error(f"{redisBaseKey} failed stored {secondUserId} in firestore/reds")
        logger.exception(e)
        return False


async def LikesDislikes_get_profiles_already_seen_by_id(userId=None, collectionNameChild=None, redisClient=None, logger=None):
    '''
    Accepts the userId and return a list of profiles already seen by user
    '''
    try:
        idsAlreadySeenByUser = []
        asyncGetProfiles = await asyncio.gather(*[LikesDislikes_fetch_userdata_from_firebase_or_redis(userId=userId, 
                                                            collectionNameChild=collectionNameChild, 
                                                            swipeStatusBetweenUsers=swipeInfo,
                                                            redisClient=redisClient, 
                                                            logger=logger) 
                                                            for swipeInfo in ["Likes","Dislikes","Superlikes"]])
        _ = [idsAlreadySeenByUser.extend(profile) for profile in asyncGetProfiles if profile is not None]
        return idsAlreadySeenByUser
    except Exception as e:
        logger.error(f"Unable to fetch profiles already seen by user LikesDislikes:{userId}:{collectionNameChild}")
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
    # given_filter = f"LikesDislikes:{current_user_id}:Given"
    # ids_given_task = asyncio.create_task(get_cached_profile_coro(redisClient=redis_client, cacheFilterName=given_filter))

    # match_filter = f"LikesDislikes:{current_user_id}:Match"
    # ids_match_task = asyncio.create_task(
    #     get_cached_profile_coro(redisClient=redis_client, cacheFilterName=match_filter))
    # unmatch_filter = f"LikesDislikes:{current_user_id}:Unmatch"
    # ids_unmatch_task = asyncio.create_task(
    #     get_cached_profile_coro(redisClient=redis_client, cacheFilterName=unmatch_filter))
    # return await asyncio.gather(*[ids_unmatch_task, ids_match_task, ids_given_task])

