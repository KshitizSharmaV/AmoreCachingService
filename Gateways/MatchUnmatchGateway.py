import asyncio
from redis.client import Redis
from datetime import datetime
import time
from google.cloud import firestore

from ProjectConf.FirestoreConf import async_db

from Gateways.RecentChatsGateway import RecentChats_Unmatch_Delete_Chat
from Gateways.LikesDislikesGatewayEXT import LikesDislikes_delete_record_from_redis, LikesDislikes_async_store_swipe_task, LikesDislikes_fetch_users_given_swipes
from Gateways.ProfilesGateway import ProfilesGateway_get_profile_by_ids
from Gateways.NotificationGateway import Notification_design_and_multicast

from ProjectConf.RedisConf import redis_client

from Utilities.LogSetup import configure_logger

logger = configure_logger(__name__)

async def MatchUnmatch_get_match_unmatch_nomatch_for_user(userId: str):
    return await asyncio.gather(*[
        MatchUnmatch_fetch_userdata_from_firebase_or_redis(userId=userId, childCollectionName=cc_name) for cc_name
        in ["Match", "Unmatch", "NoMatch"]])


async def MatchUnmatch_store_match_or_nomatch(currentUserId=None, swipedUserId=None, match_status: str = None):
    try:
        # Write to Firestore
        query_current = async_db.collection("LikesDislikes").document(currentUserId).collection(match_status).document(swipedUserId)
        await query_current.set({"id": swipedUserId, "timestamp": time.time()})

        query_other = async_db.collection("LikesDislikes").document(swipedUserId).collection(match_status).document(currentUserId)
        await query_other.set({"id": currentUserId, "timestamp": time.time()})

        logger.info(f"Stored {match_status} in Firestore for current: {currentUserId} and swiped: {swipedUserId}")

        # Write Match to redis
        redis_client.sadd(f"MatchUnmatch:{currentUserId}:{match_status}", swipedUserId)

        redis_client.sadd(f"MatchUnmatch:{swipedUserId}:{match_status}", currentUserId)

        logger.info(f"Stored {match_status} in Redis for current: {currentUserId} and swiped: {swipedUserId}")
    except Exception as e:
        logger.error(f"Unable to store NoMatch {currentUserId} {swipedUserId}")
        logger.exception(e)


async def MatchUnmatch_write_to_recent_chats(currentUserId=None, swipedUserId=None):
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
    except Exception as e:
        logger.error(f"Unable to write in recent chats after match {currentUserId} {swipedUserId}")
        logger.exception(e)


async def MatchUnmatch_send_message_notification(user_id=None):
    date_str = datetime.today().strftime('%Y%m%d')
    pay_load = {
        'title':"You have a new Match 😍 !! ",
        'body':"Let's break the 🧊 🔨",
        'analytics_label': "Match" + date_str,
        'badge_count':1,
        'notification_image':None,
        'aps_category':'Match',
        'data':{'data':None}
    }
    await Notification_design_and_multicast(user_id=user_id, pay_load=pay_load, dry_run=False)
    return 

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
        likesGivenBySwipedUser, dislikesGivenBySwipedUser, superlikesGivenBySwipedUser = await LikesDislikes_fetch_users_given_swipes(user_id=swipedUserId)

        # If the swipe given is Likes or Superlikes
        if currentUserSwipe == "Likes" or currentUserSwipe == "Superlikes":

            # Check if swipedUserId has also swiped on currentUserId
            if currentUserId in (likesGivenBySwipedUser + superlikesGivenBySwipedUser):
                logger.info(f'{currentUserId} & {swipedUserId} swiped on each other, its a Match')

                # Write Match to firestore and redis
                await MatchUnmatch_store_match_or_nomatch(currentUserId=currentUserId, swipedUserId=swipedUserId, match_status="Match")
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
            docs = async_db.collection("LikesDislikes").document(userId).collection(childCollectionName).order_by(u'timestamp', direction=firestore.Query.DESCENDING)
            profileIds = await MatchUnmatch_store_match_unmatch_to_redis(docs=docs, userId=userId,childCollectionName=childCollectionName)
            logger.info(f"{redisBaseKey} fetched {len(profileIds)} profiles from firestore")
            return profileIds
    except Exception as e:
        logger.error(f"LikesDislikes:{userId}:{childCollectionName} Failure to fetch likes dislikes data from firestore/cache")
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
    task_likes_dislikes_current_user = asyncio.create_task(MatchUnmatch_unmatch_single_user(current_user_id, other_user_id))
    # receiver
    task_likes_dislikes_other_user = asyncio.create_task(MatchUnmatch_unmatch_single_user(other_user_id, current_user_id))
    task_recent_chats_current_user = asyncio.create_task(RecentChats_Unmatch_Delete_Chat(current_user_id, other_user_id))
    task_recent_chats_other_user = asyncio.create_task(RecentChats_Unmatch_Delete_Chat(other_user_id, current_user_id))
    return await asyncio.gather(*[task_likes_dislikes_current_user, 
                                task_likes_dislikes_other_user, 
                                task_recent_chats_current_user,
                                task_recent_chats_other_user])


async def MatchUnmatch_unmatch_single_user(user_id_1: str = None, user_id_2: str = None):
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
                                                childCollectionName="Match")
            # Write Unmatch to redis
            redis_client.sadd(f"MatchUnmatch:{user_id_1}:Unmatch",user_id_2)

            # Step 2: Delete from Likes or Superlikes in Given & Change to Dislikes
            # First try to delete from Given:Likes
            wasDeleteSuccess = await LikesDislikes_delete_record_from_redis(userId=user_id_1, idToBeDeleted=user_id_2, childCollectionName="Given", swipeStatusBetweenUsers="Likes")
            # If Id wasn't deleted above delete from Given:Superlikes
            if not wasDeleteSuccess:
                wasDeleteSuccess = await LikesDislikes_delete_record_from_redis(userId=user_id_1, idToBeDeleted=user_id_2, childCollectionName="Given", swipeStatusBetweenUsers="Superlikes")
            # Store the given swipe in firestore and redis
            _ = await LikesDislikes_async_store_swipe_task(firstUserId=user_id_1, 
                                                secondUserId=user_id_2, 
                                                childCollectionName="Given", 
                                                swipeStatusBetweenUsers="Dislikes")

            # Step 3: Delete from Likes or Superlikes in Received & Change to Dislikes
            # First try to delete from Received:Likes
            wasDeleteSuccess = await LikesDislikes_delete_record_from_redis(userId=user_id_2, idToBeDeleted=user_id_1, childCollectionName="Received", swipeStatusBetweenUsers="Likes")
            # If Id wasn't deleted above delete from Received:Superlikes
            if not wasDeleteSuccess:
                wasDeleteSuccess = await LikesDislikes_delete_record_from_redis(userId=user_id_2, idToBeDeleted=user_id_1, childCollectionName="Received", swipeStatusBetweenUsers="Superlikes")
            # Store the received swipe in firestore and redis
            _ = await LikesDislikes_async_store_swipe_task(firstUserId=user_id_2, 
                                                secondUserId=user_id_1, 
                                                childCollectionName="Received", 
                                                swipeStatusBetweenUsers="Dislikes")

            logger.info(f"Succesfully unmatched users {user_id_1} {user_id_2}")
        else:
            logger.warning(f"Unable to firestore match records {user_id_1} {user_id_2} in firestore")
        return True
    except Exception as e:
        logger.error(f"Unable to unmatch users {user_id_1} {user_id_2}")
        logger.exception(e)
        return False


async def MatchUnmatch_delete_record_from_redis(user_id_1=None, user_id_2= None, childCollectionName=None):
    '''
    MatchUnmatch:{userId}:{childCollectionName} store Match or Unmatch in firestore for user
        : param user_id_1: user id 1
        : param user_id_2: user id 2
        : param childCollectionName: Match or Unmatch
    '''
    try:
        redisBaseKey = f"MatchUnmatch:{user_id_1}:{childCollectionName}"
        allUserMatchOrUnmatches = list(redis_client.smembers(redisBaseKey))
        if user_id_2 in allUserMatchOrUnmatches:
            redis_client.srem(redisBaseKey, user_id_2)
            logger.info(f"{user_id_2} was removed from {redisBaseKey}")
        else:
            logger.warning(f"{user_id_2} was not found in {redisBaseKey} to be deleted")
        return True
    except Exception as e:
        logger.error(f"Unable to delete {user_id_2} from key {redisBaseKey}")
        logger.exception(e)
        return False

