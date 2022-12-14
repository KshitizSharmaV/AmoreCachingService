import asyncio
from redis.client import Redis

from ProjectConf.FirestoreConf import async_db
from Gateways.RecentChatsGateway import RecentChats_Unmatch_Delete_Chat
from Gateways.LikesDislikesGatewayEXT import LikesDislikes_delete_record_from_redis, LikesDislikes_async_store_swipe_task
from ProjectConf.RedisConf import redis_client
    
async def MatchUnmatch_unmatch_two_users(current_user_id: str = None, other_user_id: str = None, logger=None):
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
    task_likes_dislikes_current_user = asyncio.create_task(MatchUnmatch_unmatch_single_user(current_user_id, other_user_id, logger))
    # receiver
    task_likes_dislikes_other_user = asyncio.create_task(MatchUnmatch_unmatch_single_user(other_user_id, current_user_id, logger))
    task_recent_chats_current_user = asyncio.create_task(RecentChats_Unmatch_Delete_Chat(current_user_id, other_user_id, logger))
    task_recent_chats_other_user = asyncio.create_task(RecentChats_Unmatch_Delete_Chat(other_user_id, current_user_id, logger))
    return await asyncio.gather(*[task_likes_dislikes_current_user, 
                                task_likes_dislikes_other_user, 
                                task_recent_chats_current_user,
                                task_recent_chats_other_user])


async def MatchUnmatch_unmatch_single_user(user_id_1: str = None, user_id_2: str = None,  logger=None):
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
                                                childCollectionName="Match", 
                                                logger=logger)
            # Write Unmatch to redis
            redis_client.sadd(f"MatchUnmatch:{user_id_1}:Unmatch",user_id_2)

            # Step 2: Delete from Likes or Superlikes in Given & Change to Dislikes
            # First try to delete from Given:Likes
            wasDeleteSuccess = await LikesDislikes_delete_record_from_redis(userId=user_id_1, idToBeDeleted=user_id_2, childCollectionName="Given", swipeStatusBetweenUsers="Likes", logger=logger)
            # If Id wasn't deleted above delete from Given:Superlikes
            if not wasDeleteSuccess:
                wasDeleteSuccess = await LikesDislikes_delete_record_from_redis(userId=user_id_1, idToBeDeleted=user_id_2, childCollectionName="Given", swipeStatusBetweenUsers="Superlikes", logger=logger)
            # Store the given swipe in firestore and redis
            _ = await LikesDislikes_async_store_swipe_task(firstUserId=user_id_1, 
                                                secondUserId=user_id_2, 
                                                childCollectionName="Given", 
                                                swipeStatusBetweenUsers="Dislikes", 
                                                logger=logger)

            # Step 3: Delete from Likes or Superlikes in Received & Change to Dislikes
            # First try to delete from Received:Likes
            wasDeleteSuccess = await LikesDislikes_delete_record_from_redis(userId=user_id_2, idToBeDeleted=user_id_1, childCollectionName="Received", swipeStatusBetweenUsers="Likes", logger=logger)
            # If Id wasn't deleted above delete from Received:Superlikes
            if not wasDeleteSuccess:
                wasDeleteSuccess = await LikesDislikes_delete_record_from_redis(userId=user_id_2, idToBeDeleted=user_id_1, childCollectionName="Received", swipeStatusBetweenUsers="Superlikes", logger=logger)
            # Store the received swipe in firestore and redis
            _ = await LikesDislikes_async_store_swipe_task(firstUserId=user_id_2, 
                                                secondUserId=user_id_1, 
                                                childCollectionName="Received", 
                                                swipeStatusBetweenUsers="Dislikes", 
                                                logger=logger)

            logger.info(f"Succesfully unmatched users {user_id_1} {user_id_2}")
        else:
            logger.warning(f"Unable to firestore match records {user_id_1} {user_id_2} in firestore")
        return True
    except Exception as e:
        logger.error(f"Unable to unmatch users {user_id_1} {user_id_2}")
        logger.exception(e)
        return False


async def MatchUnmatch_delete_record_from_redis(user_id_1=None, user_id_2= None, childCollectionName=None, logger=None):
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

