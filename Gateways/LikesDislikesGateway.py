from gc import collect
from google.cloud import firestore
import asyncio
import time
import json

# Get Likesdislikes data from firestore
async def async_get_likes_dislikes_match_unmatch_for_user_from_firebase(userId=None, collectionNameChild=None, async_db=None, redisClient=None, logger=None):
    try:
        # userId: Likes Dislikes of the user requesting data
        # collectionNameChild: Given, Match, Received, Unmatch
        docs = async_db.collection("LikesDislikes").document(userId).collection(collectionNameChild)
        profileIds = await async_store_likes_dislikes_match_unmatch_to_redis(docs=docs, userId=userId, collectionNameChild=collectionNameChild, redisClient=redisClient, logger=logger)
        return profileIds
    except Exception as e:
        logger.error(f"LikesDislikes:{userId}:{collectionNameChild} Failure to fetch likes dislikes data from firstore")
        logger.exception(e)

# Store Likesdislikes data to cache
async def async_store_likes_dislikes_match_unmatch_to_redis(docs=None, userId=None, collectionNameChild=None, redisClient=None, logger=None):
    try:
        profileIds = []
        async for doc in docs.stream():
            profileId = doc.id
            profileIds.append(profileId)     
            dictDoc = doc.to_dict()   
            jsonObject_dumps = json.dumps(dictDoc, indent=4, sort_keys=True, default=str)
            # LikesDislikes:QvV4OoZmZ3QWHhMNaZrr7lkqmLF3:Received:sCZ7nWrH1uR4QfAGj6Ndz4Cp3Vv2:Likes
            # LikesDislikes:UserId:subCollectionName:ProfileId:Likes
            # LikesDislikes:UserId:subCollectionName:ProfileId:DisLikes
            # LikesDislikes:UserId:subCollectionName:ProfileId:SuperLikes
            # LikesDislikes:UserId:subCollectionName:ProfileId:Match
            # LikesDislikes:UserId:subCollectionName:ProfileId:UnMatch
            # collectionNameChild is Match, Unmatch for swipeStatusBetweenUsers 
            swipeStatusBetweenUsers = dictDoc["swipe"] if "swipe" in dictDoc else collectionNameChild 
            redisClient.set(f"LikesDislikes:{userId}:{collectionNameChild}:{profileId}:{swipeStatusBetweenUsers}", jsonObject_dumps)
            logger.info(f"LikesDislikes:{userId}:{collectionNameChild}:{profileId}:{swipeStatusBetweenUsers}: data was stored to cache")
        return profileIds
    except Exception as e:
        logger.error(f"LikesDislikes:{userId}:{collectionNameChild}: Failure to store data to cache")
        logger.exception(e)
        return

# Get LikesDislikes profile Ids from cache
async def async_get_profileIds_likes_dislikes_match_unmatch_from_redis(userId=None, collectioNameChild=None, profileId=None, swipeStatusBetweenUsers=None,redisClient=None, logger=None):
    try:
        if profileId is None:
            profileIds =  [key for key in redisClient.scan_iter(f"LikesDislikes:{userId}:{collectioNameChild}:*:{swipeStatusBetweenUsers}")]
        elif swipeStatusBetweenUsers is None:
            profileIds =  [key for key in redisClient.scan_iter(f"LikesDislikes:{userId}:{collectioNameChild}:{profileId}:*")]
        logger.info(f"Successfully fetched likesdislikes data from cache:{userId}:{collectioNameChild}:{profileId}:{swipeStatusBetweenUsers}")
        return [profileId.split(":")[-1] for profileId in profileIds]
    except Exception as e:
        logger.error(f"Unable to fetch likesdislikes data from cache:{userId}:{collectioNameChild}:{profileId}:{swipeStatusBetweenUsers}")
        logger.exception(e)
        return
        

# Store likesdislikes data in firestore: We store this swipe at multiple places which will allows easy logic building
async def async_store_likes_dislikes_superlikes_for_user(currentUserId=None, swipedUserId=None, swipeInfo=None,async_db=None):
    task1 = asyncio.create_task(async_store_likesdislikes_updated(currentUserId=currentUserId, async_db=async_db))
    task2 = asyncio.create_task(async_store_given_swipe_task(currentUserId=currentUserId, swipedUserId=swipedUserId, swipeInfo=swipeInfo, async_db=async_db))
    task3 = asyncio.create_task(async_store_received_swipe_task(currentUserId=currentUserId, swipedUserId=swipedUserId, swipeInfo=swipeInfo, async_db=async_db))
    return asyncio.gather(*[task1, task2, task3])

# Set the update flag for MatchingEngine
async def async_store_likesdislikes_updated(currentUserId=None, async_db=None):
    await async_db.collection('LikesDislikes').document(currentUserId).set({"wasUpdated": True})

# Store data in likesdislikes collection of the user who have the swipe
# done for ease of read & build easy logics around different business use cases
async def async_store_given_swipe_task(currentUserId=None, swipedUserId=None, swipeInfo=None,async_db=None):
    storeData = {"swipe": swipeInfo, "timestamp": time.time(), 'matchVerified': False}
    await async_db.collection('LikesDislikes').document(currentUserId).collection("Given").document(swipedUserId).set(storeData)
    
# Store data in likesdislikes collection of the profile who received the swipe
# done for ease of read & build easy logics around different business use cases
async def async_store_received_swipe_task(currentUserId=None, swipedUserId=None, swipeInfo=None,async_db=None):
    data = {"swipe": swipedUserId, "timestamp": time.time()}
    await async_db.collection('LikesDislikes').document(swipedUserId).collection("Received").document(currentUserId).set()

# Unmatch from a user
async def async_store_unmatch_task_likes_dislikes(userId1=None, userId2=None, async_db=None):
    match_ref = async_db.collection('LikesDislikes').document(userId1).collection("Match").document(userId2)
    match_doc = await match_ref.get()
    if match_doc.exists:
        match_doc = match_doc.to_dict()
        await match_ref.delete()
        unmatch_ref = async_db.collection('LikesDislikes').document(userId1).collection("Unmatch").document(userId2)
        await unmatch_ref.set(match_doc)

