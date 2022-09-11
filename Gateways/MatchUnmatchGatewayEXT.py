""""
Matching Engine Translated Here
"""
import asyncio
from datetime import datetime
import time
from redis import Redis
from google.cloud import firestore
from ProjectConf.FirestoreConf import async_db
from Gateways.ProfilesGateway import ProfilesGateway_get_profile_by_ids
from Gateways.LikesDislikesGatewayEXT import LikesDislikes_fetch_users_given_swipes


async def MatchUnmatch_get_match_unmatch_nomatch_for_user(userId: str, redisClient: Redis, logger):
    return await asyncio.gather(*[
        MatchUnmatch_fetch_userdata_from_firebase_or_redis(userId=userId, childCollectionName=cc_name,
                                                           redisClient=redisClient, logger=logger) for cc_name
        in ["Match", "Unmatch", "NoMatch"]])


async def MatchUnmatch_store_match_or_nomatch(currentUserId=None, swipedUserId=None, match_status: str = None,
                                              redisClient=None, logger=None):
    try:
        # Write to Firestore
        query_current = async_db.collection("LikesDislikes").document(currentUserId).collection(match_status).document(
            swipedUserId)
        await query_current.set({"id": swipedUserId, "timestamp": time.time()})

        query_other = async_db.collection("LikesDislikes").document(swipedUserId).collection(match_status).document(
            currentUserId)
        await query_other.set({"id": currentUserId, "timestamp": time.time()})

        logger.info(f"Stored {match_status} in Firestore for current: {currentUserId} and swiped: {swipedUserId}")

        # Write Match to redis
        redisClient.sadd(f"MatchUnmatch:{currentUserId}:{match_status}", swipedUserId)

        redisClient.sadd(f"MatchUnmatch:{swipedUserId}:{match_status}", currentUserId)

        logger.info(f"Stored {match_status} in Redis for current: {currentUserId} and swiped: {swipedUserId}")
    except Exception as e:
        logger.error(f"Unable to store NoMatch {currentUserId} {swipedUserId}")
        logger.exception(e)


async def MatchUnmatch_write_to_recent_chats(currentUserId=None, swipedUserId=None, redisClient=None, logger=None):
    try:
        # Fetch the user data for current user and swiped user id
        currentUserData = await ProfilesGateway_get_profile_by_ids(redisClient=redisClient,
                                                                   profileIdList=[currentUserId], logger=logger,
                                                                   async_db=async_db)
        currentUserData = currentUserData.pop()
        swipedUserData = await ProfilesGateway_get_profile_by_ids(redisClient=redisClient,
                                                                  profileIdList=[swipedUserId], logger=logger,
                                                                  async_db=async_db)
        swipedUserData = swipedUserData.pop()

        # Write match to recent chats
        query = async_db.collection("RecentChats").document(currentUserId).collection("Messages").document(
            swipedUserId)
        await query.set({"fromId": currentUserId,
                         "toId": swipedUserId,
                         "timestamp": datetime.now(),
                         "lastText": "",
                         "user": {
                             "firstName": swipedUserData["firstName"],
                             "lastName": swipedUserData["lastName"],
                             "image1": swipedUserData["image1"],
                             "id": swipedUserId
                         },
                         "otherUserUpdated": True,
                         "directMessageApproved": True})

        query = async_db.collection("RecentChats").document(swipedUserId).collection("Messages").document(
            currentUserId)
        await query.set({"fromId": swipedUserId,
                         "toId": currentUserId,
                         "timestamp": datetime.now(),
                         "lastText": "",
                         "user": {
                             "firstName": currentUserData["firstName"],
                             "lastName": currentUserData["lastName"],
                             "image1": currentUserData["image1"],
                             "id": currentUserId
                         },
                         "otherUserUpdated": True,
                         "directMessageApproved": True})
    except Exception as e:
        logger.error(f"Unable to write in recent chats after match {currentUserId} {swipedUserId}")
        logger.exception(e)


async def MatchUnmatch_check_match_between_users(currentUserId=None, swipedUserId=None, currentUserSwipe=None,
                                                 redisClient=None, logger=None):
    '''
    Check the match between both users
        : If the swipe given is like or superlike
            : Fetch the Likes or Superlikes Given by the Swiped id
            : If swipedUserId has also swiped a 'Like' or '' on currentUserId
                : Write to Match collection for both users in firestore
                : Get profile data from redis/firestore - Need information to write to RecentChat in firestore
                : Write to Recent Chats collection for both users in firestore
                : Update redis with new matches for both users
        : Else:
            : User gave a dislike no need to calculate a match
    '''
    try:
        likesGivenBySwipedUser, dislikesGivenBySwipedUser, superlikesGivenBySwipedUser = \
            await LikesDislikes_fetch_users_given_swipes(user_id=swipedUserId, redis_client=redisClient, logger=logger)

        # If the swipe given is Likes or Superlikes
        if currentUserSwipe == "Likes" or currentUserSwipe == "Superlikes":

            # Check if swipedUserId has also swiped on currentUserId
            if currentUserId in (likesGivenBySwipedUser + superlikesGivenBySwipedUser):
                logger.info(f'{currentUserId} & {swipedUserId} swiped on each other, its a Match')

                # Write Match to firestore and redis
                await MatchUnmatch_store_match_or_nomatch(currentUserId=currentUserId, swipedUserId=swipedUserId,
                                                          match_status="Match", redisClient=redisClient,
                                                          logger=logger)

                await MatchUnmatch_write_to_recent_chats(currentUserId=currentUserId, swipedUserId=swipedUserId,
                                                         redisClient=redisClient, logger=logger)

                logger.info(f"Match successfully written in redis/firestore for {swipedUserId} & {currentUserId}")

            elif currentUserId in dislikesGivenBySwipedUser:
                # current user likes but receiver dislikes -- if exists: -- No Match
                await MatchUnmatch_store_match_or_nomatch(currentUserId=currentUserId, swipedUserId=swipedUserId,
                                                          match_status="NoMatch", redisClient=redisClient,
                                                          logger=logger)
            else:
                # Waiting for other user to swipe
                logger.info(f"{swipedUserId} didn't either swiped on {currentUserId} OR gave a dislike")

        else:
            # current User gave a dislike -- no need to calculate a match
            logger.info(f"{currentUserId} gave {swipedUserId} a dislike ")
            # Dislike -- check given of received user -- if current user exists in it: No Match
            if currentUserId in set(likesGivenBySwipedUser + superlikesGivenBySwipedUser + dislikesGivenBySwipedUser):
                await MatchUnmatch_store_match_or_nomatch(currentUserId=currentUserId, swipedUserId=swipedUserId,
                                                          match_status="NoMatch", redisClient=redisClient,
                                                          logger=logger)
            # Else: waiting on received user to swipe

        return True
    except Exception as e:
        logger.error(f"Unable to calculate the match {currentUserId} {swipedUserId}")
        logger.exception(e)
        return False


async def MatchUnmatch_fetch_userdata_from_firebase_or_redis(userId=None, childCollectionName=None, redisClient=None,
                                                             logger=None):
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
            docs = async_db.collection("LikesDislikes").document(userId).collection(childCollectionName).order_by(
                u'timestamp', direction=firestore.Query.DESCENDING)
            profileIds = await MatchUnmatch_store_match_unmatch_to_redis(docs=docs, userId=userId,
                                                                         childCollectionName=childCollectionName,
                                                                         redisClient=redisClient,
                                                                         logger=logger)
            logger.info(f"{redisBaseKey} fetched {len(profileIds)} profiles from firestore")
            return profileIds
    except Exception as e:
        logger.error(
            f"LikesDislikes:{userId}:{childCollectionName} Failure to fetch likes dislikes data from firestore/cache")
        logger.exception(e)
        return []


async def MatchUnmatch_store_match_unmatch_to_redis(docs=None, userId=None, childCollectionName=None, redisClient=None,
                                                    logger=None):
    """
    MatchUnmatch:{userId}:{childCollectionName} store Match or Unmatch in firestore for user
        :param userId: user id
        :param docs: LikesDislikes collection, subcollection(Match/Unmatch) documents to iterate
        : param childCollectionName: Match or Unmatch
    """
    try:
        redisBaseKey = f"MatchUnmatch:{userId}:{childCollectionName}"
        profileIds = []
        async for doc in docs.stream():
            profileIds.append(doc.id)
            redisClient.sadd(redisBaseKey, doc.id)
            logger.info(f"{doc.id} was pushed to stack {redisBaseKey}")
        return profileIds
    except Exception as e:
        logger.error(f"MatchUnmatch:{userId}:{childCollectionName} Failure to store data to cache")
        logger.exception(e)
        return []


async def MatchUnmatch_fetch_data_from_redis(userId=None, childCollectionName=None, redisClient=None, logger=None):
    """
    Fetch match unmatch data from redis
        :param userId: user id
        :param childCollectionName: Match or Unmatch
    """
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


# logic to check the match between the 2 users
def MatchUnmatch_calculate_the_match(firstUserSwipe=None, secondUserSwipe=None, logger=None):
    try:
        if firstUserSwipe == "Likes":
            if secondUserSwipe == "Likes": return "Match"
            if secondUserSwipe == "Superlikes": return "Match"
            if secondUserSwipe == "Dislikes": return "NoMatch"
        elif firstUserSwipe == "Superlikes":
            if secondUserSwipe == "Like": return "Match"
            if secondUserSwipe == "Dislikes": return "NoMatch"
            if secondUserSwipe == "Superlikes": return "Match"
        elif firstUserSwipe == "Dislikes":
            if secondUserSwipe == "Superlikes": return "NoMatch"
            if secondUserSwipe == "Likes": return "NoMatch"
            if secondUserSwipe == "Dislikes": return "NoMatch"
    except Exception as e:
        logger.error(f"Unable to calcualte the match {firstUserSwipe} {secondUserSwipe}")
        logger.exception(e)
        return False
