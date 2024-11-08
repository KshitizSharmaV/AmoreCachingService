import asyncio
from datetime import datetime
import time
from google.cloud import firestore

from Gateways.MatchUnmatchGatewayEXT import RecentChats_Unmatch_Delete_Chat, \
    MatchUnmatch_unlink_single_user
from ProjectConf.FirestoreConf import async_db
from Gateways.LikesDislikesGatewayEXT import LikesDislikes_fetch_users_given_swipes
from Gateways.ProfilesGateway import ProfilesGateway_get_profile_by_ids
from Gateways.NotificationGateway import Notification_design_and_multicast
from ProjectConf.RedisConf import redis_client
from Utilities.LogSetup import configure_logger

logger = configure_logger(__name__)


async def MatchUnmatch_get_match_unmatch_nomatch_for_user(userId: str):
    """
    Get match unmatch and nomatch for a user id

    Params:
        userId
    
    Returns:
        List of ids
    """
    return await asyncio.gather(
        *[MatchUnmatch_fetch_userdata_from_firebase_or_redis(userId=userId, childCollectionName=cc_name) for cc_name in
          ["Match", "Unmatch", "NoMatch"]])


async def MatchUnmatch_store_match_or_nomatch(currentUserId=None, swipedUserId=None, match_status: str = None):
    """
    Write Match Unmatch to firestore and redi
    
    Params:
        currentUserId 
        swipedUserId
        match_status

    Returns:
        Boolean value
    """
    try:
        # Write to Firestore
        query_current = async_db.collection("LikesDislikes").document(currentUserId).collection(match_status).document(
            swipedUserId)
        await query_current.set({"id": swipedUserId, "timestamp": time.time()})
        query_other = async_db.collection("LikesDislikes").document(swipedUserId).collection(match_status).document(
            currentUserId)
        await query_other.set({"id": currentUserId, "timestamp": time.time()})
        logger.info(f"Stored {match_status} in Firestore for current: {currentUserId} and swiped: {swipedUserId}")
        redis_client.sadd(f"MatchUnmatch:{currentUserId}:{match_status}", swipedUserId)
        redis_client.sadd(f"MatchUnmatch:{swipedUserId}:{match_status}", currentUserId)
        logger.info(f"Stored {match_status} in Redis for current: {currentUserId} and swiped: {swipedUserId}")
        return True
    except Exception as e:
        logger.error(f"Unable to store NoMatch {currentUserId} {swipedUserId}")
        logger.exception(e)
        return False


async def MatchUnmatch_write_to_recent_chats(currentUserId=None, swipedUserId=None):
    """
    Once two users are matched, this function writes to RecentChats for users to start chattng

    Param:
        currentUserId
        swipedUserId

    Returns:
        Bool
    """
    try:
        # Fetch the user data for current user and swiped user id
        currentUserData = await ProfilesGateway_get_profile_by_ids(profileIdList=[currentUserId])
        currentUserData = currentUserData.pop()
        swipedUserData = await ProfilesGateway_get_profile_by_ids(profileIdList=[swipedUserId])
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
        return True
    except Exception as e:
        logger.error(f"Unable to write in recent chats after match {currentUserId} {swipedUserId}")
        logger.exception(e)
        return False


async def MatchUnmatch_send_message_notification(user_id=None):
    """
    Send match notification

    Param: 
        user_id: String
    
    Return: Bool
    """
    try:
        date_str = datetime.today().strftime('%Y%m%d')
        pay_load = {
            'title': "You have a new Match 😍 !! ",
            'body': "Let's break the 🧊 🔨",
            'analytics_label': "Match" + date_str,
            'badge_count': 1,
            'notification_image': None,
            'aps_category': 'Match',
            'data': {'data': None}
        }
        await Notification_design_and_multicast(user_id=user_id, pay_load=pay_load, dry_run=False)
        return True
    except Exception as e:
        logger.error(f"Unable to send Match/Unmatch notification for {user_id}")
        logger.exception(e)
        return False


async def MatchUnmatch_check_match_between_users(currentUserId=None, swipedUserId=None, currentUserSwipe=None):
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
        likesGivenBySwipedUser, dislikesGivenBySwipedUser, superlikesGivenBySwipedUser = await LikesDislikes_fetch_users_given_swipes(
            user_id=swipedUserId)

        # If the swipe given is Likes or Superlikes
        if currentUserSwipe == "Likes" or currentUserSwipe == "Superlikes":

            # Check if swipedUserId has also swiped on currentUserId
            if currentUserId in (likesGivenBySwipedUser + superlikesGivenBySwipedUser):
                logger.info(f'{currentUserId} & {swipedUserId} swiped on each other, its a Match')

                # Write Match to firestore and redis
                await MatchUnmatch_store_match_or_nomatch(currentUserId=currentUserId, swipedUserId=swipedUserId,
                                                          match_status="Match")
                await MatchUnmatch_write_to_recent_chats(currentUserId=currentUserId, swipedUserId=swipedUserId)
                await MatchUnmatch_send_message_notification(user_id=currentUserId)
                await MatchUnmatch_send_message_notification(user_id=swipedUserId)
                logger.info(f"Match successfully written in redis/firestore for {swipedUserId} & {currentUserId}")

            elif currentUserId in dislikesGivenBySwipedUser:
                # current user likes but receiver dislikes -- if exists: -- No Match
                await MatchUnmatch_store_match_or_nomatch(currentUserId=currentUserId, swipedUserId=swipedUserId,
                                                          match_status="NoMatch")
            else:
                # Waiting for other user to swipe
                logger.info(f"{swipedUserId} didn't either swiped on {currentUserId} OR gave a dislike")

        else:
            # current User gave a dislike -- no need to calculate a match
            logger.info(f"{currentUserId} gave {swipedUserId} a dislike ")
            # Dislike -- check given of received user -- if current user exists in it: No Match
            if currentUserId in set(likesGivenBySwipedUser + superlikesGivenBySwipedUser + dislikesGivenBySwipedUser):
                await MatchUnmatch_store_match_or_nomatch(currentUserId=currentUserId, swipedUserId=swipedUserId,
                                                          match_status="NoMatch")
            # Else: waiting on received user to swipe

        return True
    except Exception as e:
        logger.error(f"Unable to calculate the match {currentUserId} {swipedUserId}")
        logger.exception(e)
        return False


async def MatchUnmatch_fetch_userdata_from_firebase_or_redis(userId=None, childCollectionName=None):
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
        if redis_client.scard(redisBaseKey) > 0:
            profileIds = await MatchUnmatch_fetch_data_from_redis(userId=userId,
                                                                  childCollectionName=childCollectionName)
            logger.info(f"{redisBaseKey} fetched {len(profileIds)} profiles from redis")
            return profileIds
        else:
            # If not fetch data from firestore & save it in cache
            docs = async_db.collection("LikesDislikes").document(userId).collection(childCollectionName).order_by(
                u'timestamp', direction=firestore.Query.DESCENDING)
            profileIds = await MatchUnmatch_store_match_unmatch_to_redis(docs=docs, userId=userId,
                                                                         childCollectionName=childCollectionName)
            logger.info(f"{redisBaseKey} fetched {len(profileIds)} profiles from firestore")
            return profileIds
    except Exception as e:
        logger.error(
            f"LikesDislikes:{userId}:{childCollectionName} Failure to fetch likes dislikes data from firestore/cache")
        logger.exception(e)
        return []


async def MatchUnmatch_store_match_unmatch_to_redis(docs=None, userId=None, childCollectionName=None):
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
            redis_client.sadd(redisBaseKey, doc.id)
            logger.info(f"{doc.id} was pushed to stack {redisBaseKey}")
        return profileIds
    except Exception as e:
        logger.error(f"MatchUnmatch:{userId}:{childCollectionName} Failure to store data to cache")
        logger.exception(e)
        return []


async def MatchUnmatch_fetch_data_from_redis(userId=None, childCollectionName=None):
    """
    Fetch match unmatch data from redis
        :param userId: user id
        :param childCollectionName: Match or Unmatch
    Return 
        List of profile
    """
    try:
        redisBaseKey = f"MatchUnmatch:{userId}:{childCollectionName}"
        # Redis function 'smembers' will give you the length of set inside redis key
        profileIds = list(redis_client.smembers(redisBaseKey))
        logger.info(f"Fetched {len(profileIds)} from cache:{redisBaseKey}")
        return profileIds
    except Exception as e:
        logger.error(f"Unable to fetch LikesDislikes data from cache {redisBaseKey}")
        logger.exception(e)
        return []


# logic to check the match between the 2 users
def MatchUnmatch_calculate_the_match(firstUserSwipe=None, secondUserSwipe=None):
    try:
        if firstUserSwipe == "Likes":
            if secondUserSwipe == "Likes": return "Match"
            if secondUserSwipe == "Superlikes": return "Match"
            if secondUserSwipe == "Dislikes": return "NoMatch"
        elif firstUserSwipe == "Superlikes":
            if secondUserSwipe == "Likes": return "Match"
            if secondUserSwipe == "Dislikes": return "NoMatch"
            if secondUserSwipe == "Superlikes": return "Match"
        elif firstUserSwipe == "Dislikes":
            if secondUserSwipe == "Superlikes": return "NoMatch"
            if secondUserSwipe == "Likes": return "NoMatch"
            if secondUserSwipe == "Dislikes": return "NoMatch"
        else:
            raise Exception("Invalid input for firstUserSwipe")
    except Exception as e:
        logger.error(f"Unable to calcualte the match {firstUserSwipe} {secondUserSwipe}")
        logger.exception(e)
        return False


async def MatchUnmatch_unmatch_two_users(current_user_id: str = None, other_user_id: str = None):
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
    task_likes_dislikes_current_user = asyncio.create_task(
        MatchUnmatch_unlink_single_user(current_user_id, other_user_id))
    # receiver
    task_likes_dislikes_other_user = asyncio.create_task(
        MatchUnmatch_unlink_single_user(other_user_id, current_user_id))
    task_recent_chats_current_user = asyncio.create_task(
        RecentChats_Unmatch_Delete_Chat(current_user_id, other_user_id))
    task_recent_chats_other_user = asyncio.create_task(RecentChats_Unmatch_Delete_Chat(other_user_id, current_user_id))
    return await asyncio.gather(*[task_likes_dislikes_current_user,
                                  task_likes_dislikes_other_user,
                                  task_recent_chats_current_user,
                                  task_recent_chats_other_user])


