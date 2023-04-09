import asyncio

from ProjectConf.FirestoreConf import async_db
from Gateways.LikesDislikesGatewayEXT import LikesDislikes_update_like_superlike_dislike, \
    LikesDislikes_async_store_swipe_task
from ProjectConf.RedisConf import redis_client
from Utilities.LogSetup import configure_logger

logger = configure_logger(__name__)


async def MatchUnmatch_remove_match_for_one_user(user_id_1: str = None, user_id_2: str = None):
    """
    - Get the LikeDislikes Match Collection for first user, If exists
        1. Delete the above record from match collection
        2. Write the record to Unmatch collection for user
        3. Delete Match from redis
        4. Write to Unmatch in redis
    """
    try:
        match_ref = async_db.collection('LikesDislikes').document(user_id_1).collection("Match").document(user_id_2)
        match_doc = await match_ref.get()
        if match_doc.exists:
            # Step 1: Delete from Match and re-write to Unmatch for the profile ids
            # Write in other firestore collection for user
            match_doc = match_doc.to_dict()
            await match_ref.delete()
            unmatch_ref = async_db.collection('LikesDislikes').document(user_id_1).collection("Unmatch").document(
                user_id_2)
            await unmatch_ref.set(match_doc)
            # Delete Match from redis
            _ = await MatchUnmatch_delete_record_from_redis(user_id_1=user_id_1,
                                                            user_id_2=user_id_2,
                                                            childCollectionName="Match")
            # Write Unmatch to redis
            redis_client.sadd(f"MatchUnmatch:{user_id_1}:Unmatch", user_id_2)
            logger.info(f"Succesfully unmatched users {user_id_1} from {user_id_2}")
        else:
            logger.warning(f"Unable to firestore match records {user_id_1} {user_id_2} in firestore")
    except Exception as e:
        logger.error(f"Unable to unmatch for one user {user_id_1} {user_id_2}")
        logger.exception(e)
        return False


async def MatchUnmatch_unlink_single_user(user_id_1: str = None, user_id_2: str = None,
                                          report_matched_user: bool = False):
    """
    Unlinking performed in following order
    Case 1: If users are matched (Messaging View), report_matched_user = true
        - Delete Match from Firestore and Redis, Write Unmatch on both, for both sides
            - repeat for second user
        - Update superlike/like to dislike in given of user in redis/firestore to Dislike
        - Update superlike/like to dislike in received of other user in redis/firestore
    Case 2: If users are not matched (Reported from Swipe view), report_matched_user = false
        - No need to update swipes since no swipe has been given, directly store dislike

    :param user_id_1: Current User's UID
    :param user_id_2: Other User's UID
    :param report_matched_user: bool: Whether reported a matched user or not
    :return: bool
    """
    try:
        if report_matched_user:
            task1 = asyncio.create_task(
                MatchUnmatch_remove_match_for_one_user(user_id_1=user_id_1, user_id_2=user_id_2))
            task2 = asyncio.create_task(
                MatchUnmatch_remove_match_for_one_user(user_id_1=user_id_2, user_id_2=user_id_1))
            await asyncio.gather(*[task1, task2])

        # Step 2: Convert superlike/like in given of user in redis/firestore to Dislike
        if report_matched_user:
            task1 = asyncio.create_task(
                LikesDislikes_update_like_superlike_dislike(firstUserId=user_id_1, secondUserId=user_id_2,
                                                            childCollectionName="Given",
                                                            from_swipe_status=['Likes', 'Superlikes'],
                                                            to_swipe_status='Dislikes'))
        else:
            task1 = asyncio.create_task(LikesDislikes_async_store_swipe_task(firstUserId=user_id_1,
                                                                             secondUserId=user_id_2,
                                                                             childCollectionName="Given",
                                                                             swipeStatusBetweenUsers="Dislikes"))

        # Step 3: Convert superlike/like in received of other user in redis/firestore to Dislike
        if report_matched_user:
            task2 = asyncio.create_task(
                LikesDislikes_update_like_superlike_dislike(firstUserId=user_id_2, secondUserId=user_id_1,
                                                            childCollectionName="Received",
                                                            from_swipe_status=['Likes', 'Superlikes'],
                                                            to_swipe_status='Dislikes'))
        else:
            task2 = asyncio.create_task(LikesDislikes_async_store_swipe_task(firstUserId=user_id_2,
                                                                             secondUserId=user_id_1,
                                                                             childCollectionName="Received",
                                                                             swipeStatusBetweenUsers="Dislikes"))
        await asyncio.gather(*[task1, task2])
        logger.info(f"Succesfully dislike by {user_id_1} for un-matching/reporting {user_id_2}")
        return True
    except Exception as e:
        logger.error(f"Unable to unmatch users {user_id_1} {user_id_2}")
        logger.exception(e)
        return False


async def MatchUnmatch_delete_record_from_redis(user_id_1=None, user_id_2=None, childCollectionName=None):
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


async def RecentChats_Unmatch_Delete_Chat(user_id_1: str = None, user_id_2: str = None):
    """
    Delete the recent chat from firestore
    :param user_id_1: Current User's UID
    :param user_id_2: Other User's UID
    :return:
    """
    try:
        recent_chat_ref = async_db.collection('RecentChats').document(user_id_1).collection("Messages").document(
            user_id_2)
        await recent_chat_ref.delete()
        logger.info(f"Delete the recent chat from firestore for {user_id_1} {user_id_2}")
        return True
    except Exception as e:
        logger.error(e)
        logger.error(f"Unable to delete the recent chat from firestore {user_id_1} {user_id_2}")
        return False
