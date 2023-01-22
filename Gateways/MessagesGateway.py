import asyncio
from ProjectConf.FirestoreConf import async_db
from Gateways.LikesDislikesGateway import LikesDislikes_async_store_likes_dislikes_superlikes_for_user
from Utilities.LogSetup import configure_logger

logger = configure_logger(__name__)


# after unmatch call this function, to remove profiles from recentchats too
async def unmatch_task_recent_chats(profileId1=None, profileId2=None):
    recent_chat_ref = async_db.collection('RecentChats').document(profileId1).collection("Messages").document(profileId2)
    await recent_chat_ref.delete()


async def match_two_profiles_for_direct_message(current_user_id: str = None, other_user_id: str = None):
    """
    - Task 1: Add superlike records in LikesDislikes.<userID>.Given.<userID> for both users
    - Task 2: Add superlike records in RedisCache
    - LikesDislikes_async_store_likes_dislikes_superlikes_for_user(): Task 1 and Task 2
    Storing 'Like' for each other for each user will trigger matching engine and match them automatically.

    :param current_user_id: Current User's ID
    :param other_user_id: Other User's ID
    
    :return: Gathered tasks as coroutine
    """
    try:
        logger.info(f"match on dm request {current_user_id} and {other_user_id}")
        current_user_like_record_task = asyncio.create_task(
            LikesDislikes_async_store_likes_dislikes_superlikes_for_user(currentUserId=current_user_id,
                                                                         swipedUserId=other_user_id,
                                                                         swipeStatusBetweenUsers='Superlikes'))
        logger.info(f"match on dm request CHECKPOINT 1")
        other_user_like_record_task = asyncio.create_task(
            LikesDislikes_async_store_likes_dislikes_superlikes_for_user(currentUserId=other_user_id,
                                                                         swipedUserId=current_user_id,
                                                                         swipeStatusBetweenUsers='Superlikes'))
        return asyncio.gather(*[current_user_like_record_task, other_user_like_record_task])
    except Exception as e:
        logger.error(f"Failed to Match Direct Message Profiles {current_user_id} and {other_user_id}")
        logger.exception(e)
        return
