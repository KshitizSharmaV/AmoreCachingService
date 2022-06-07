import time
import asyncio
from firebase_admin import firestore
from google.cloud.firestore import AsyncClient
from redis.client import Redis
from Gateways.LikesDislikesGateway import LikesDislikes_async_store_likes_dislikes_superlikes_for_user


# after unmatch call this function, to remove profiles from recentchats too
async def unmatch_task_recent_chats(profileId1=None, profileId2=None, async_db=None):
    recent_chat_ref = async_db.collection('RecentChats').document(profileId1).collection("Messages").document(
        profileId2)
    await recent_chat_ref.delete()


async def match_two_profiles_for_direct_message(current_user_id: str = None, other_user_id: str = None,
                                          async_db: AsyncClient = None, logger=None, redis_client: Redis = None):
    """
    - Task 1: Add superlike records in LikesDislikes.<userID>.Given.<userID> for both users
    - Task 2: Add superlike records in RedisCache
    - LikesDislikes_async_store_likes_dislikes_superlikes_for_user(): Task 1 and Task 2
    Storing 'Like' for each other for each user will trigger matching engine and match them automatically.

    :param current_user_id: Current User's ID
    :param other_user_id: Other User's ID
    :param async_db: Firestore Async Client for the project
    :param logger: Custom app logger instance
    :param redis_client: Redis client instance

    :return: Gathered tasks as coroutine
    """
    try:
        logger.info(f"match on dm request {current_user_id} and {other_user_id}")
        current_user_like_record_task = asyncio.create_task(
            LikesDislikes_async_store_likes_dislikes_superlikes_for_user(currentUserId=current_user_id,
                                                                         swipedUserId=other_user_id,
                                                                         swipeStatusBetweenUsers='Superlikes',
                                                                         async_db=async_db,
                                                                         redisClient=redis_client, logger=logger))
        logger.info(f"match on dm request CHECKPOINT 1")
        other_user_like_record_task = asyncio.create_task(
            LikesDislikes_async_store_likes_dislikes_superlikes_for_user(currentUserId=other_user_id,
                                                                         swipedUserId=current_user_id,
                                                                         swipeStatusBetweenUsers='Superlikes',
                                                                         async_db=async_db,
                                                                         redisClient=redis_client, logger=logger))
        return asyncio.gather(*[current_user_like_record_task, other_user_like_record_task])
    except Exception as e:
        logger.error(f"Failed to Match Direct Message Profiles {current_user_id} and {other_user_id}")
        logger.exception(e)
        return
