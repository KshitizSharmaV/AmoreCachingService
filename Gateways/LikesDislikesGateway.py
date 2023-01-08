from gc import collect
from google.cloud import firestore
import asyncio
import time
import json

from ProjectConf.AsyncioPlugin import run_coroutine
from ProjectConf.FirestoreConf import async_db, db
from Gateways.MatchUnmatchGateway import MatchUnmatch_check_match_between_users
from Gateways.LikesDislikesGatewayEXT import LikesDislikes_fetch_userdata_from_firebase_or_redis, \
    LikesDislikes_async_store_swipe_task

'''
################################################
LikesDislikes Key Format
LikesDislikes:{userId}:{childCollectionName}:{swipeStatusBetweenUsers}:{}
e.g. LikesDislikes:{userId}:Given:Likes
e.g. LikesDislikes:{userId}:Given:SuperLikes
e.g. LikesDislikes:{userId}:Given:Dislikes
The data stored with key is a list of ProfileIds who have liked, disliked or superliked
################################################
'''


# Store likesdislikes data in firestore: We store this swipe at multiple places which will allows easy logic building
async def LikesDislikes_async_store_likes_dislikes_superlikes_for_user(currentUserId=None, swipedUserId=None,
                                                                       swipeStatusBetweenUsers=None,
                                                                       upgradeLikeToSuperlike=None, 
                                                                       async_db=None,
                                                                       logger=None):
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
        task1 = asyncio.create_task(
            LikesDislikes_async_store_swipe_task(firstUserId=currentUserId, secondUserId=swipedUserId,
                                                 childCollectionName="Given",
                                                 swipeStatusBetweenUsers=swipeStatusBetweenUsers,
                                                 upgradeLikeToSuperlike=upgradeLikeToSuperlike,
                                                 logger=logger))
        # Store recevied swipe task
        task2 = asyncio.create_task(
            LikesDislikes_async_store_swipe_task(firstUserId=swipedUserId, secondUserId=currentUserId,
                                                 childCollectionName="Received",
                                                 swipeStatusBetweenUsers=swipeStatusBetweenUsers,
                                                 upgradeLikeToSuperlike=upgradeLikeToSuperlike,
                                                logger=logger))

        task3 = asyncio.create_task(MatchUnmatch_check_match_between_users(currentUserId=currentUserId,
                                                                           swipedUserId=swipedUserId,
                                                                           currentUserSwipe=swipeStatusBetweenUsers,
                                                                           logger=logger))
        return await asyncio.gather(*[task1, task2, task3])
    except Exception as e:
        logger.error(f"Failed to store the async likesdislikes swipe in firestore/redis")
        logger.exception(e)
        return False


async def LikesDislikes_get_profiles_already_seen_by_id(userId=None, childCollectionName=None,logger=None):
    '''
    Accepts the userId and return a list of profiles already seen by user
    '''
    try:
        idsAlreadySeenByUser = []
        asyncGetProfiles = await asyncio.gather(*[LikesDislikes_fetch_userdata_from_firebase_or_redis(userId=userId, 
                                                            childCollectionName=childCollectionName, 
                                                            swipeStatusBetweenUsers=swipeInfo,
                                                            logger=logger) 
                                                            for swipeInfo in ["Likes","Dislikes","Superlikes"]])
        _ = [idsAlreadySeenByUser.extend(profile) for profile in asyncGetProfiles if profile is not None]
        return idsAlreadySeenByUser
    except Exception as e:
        logger.error(f"Unable to fetch profiles already seen by user LikesDislikes:{userId}:{childCollectionName}")
        logger.exception(e)
        return []
