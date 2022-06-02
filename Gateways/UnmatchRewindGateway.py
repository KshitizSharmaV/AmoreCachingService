import asyncio
import json
import time
from redis.client import Redis
from ProjectConf.FirestoreConf import async_db, db
from logging import Logger


async def unmatch_task_function(current_user_id: str = None, other_user_id: str = None, redis_client: Redis = None):
    """
    Asynchronously performs following firestore tasks:
        - Query firestore for current_user_id's match record for the other_user_id and fetch it.
        - Delete the above record from firestore.
        - Set the data from above record in Unmatch subcollection of current_user.
        - Delete the RecentChats record of other_user from the current_user's records and vice-versa.
    :param current_user_id: Current User's UID
    :param other_user_id: Other User's UID
    :return:
    """
    task_likes_dislikes_current_user = asyncio.create_task(
        unmatch_task_likes_dislikes(current_user_id, other_user_id, redis_client))
    task_likes_dislikes_other_user = asyncio.create_task(
        unmatch_task_likes_dislikes(other_user_id, current_user_id, redis_client))
    # Can be modified to show unmatched chats/chat listings in a more sophisticated manner.
    task_recent_chats_current_user = asyncio.create_task(
        unmatch_task_recent_chats(current_user_id, other_user_id, redis_client))
    task_recent_chats_other_user = asyncio.create_task(
        unmatch_task_recent_chats(other_user_id, current_user_id, redis_client))
    return await asyncio.gather(
        *[task_likes_dislikes_current_user, task_likes_dislikes_other_user, task_recent_chats_current_user,
          task_recent_chats_other_user])


async def unmatch_task_likes_dislikes(user_id_1: str = None, user_id_2: str = None, redis_client: Redis = None):
    match_ref = async_db.collection('LikesDislikes').document(user_id_1).collection("Match").document(user_id_2)
    match_doc = await match_ref.get()
    if match_doc.exists:
        match_doc = match_doc.to_dict()
        await match_ref.delete()
        keys_to_be_removed_from_redis = [key for key in
                                         redis_client.scan_iter(f"LikesDislikes:{user_id_1}:Match:{user_id_2}*")]
        if len(keys_to_be_removed_from_redis) > 0:
            _ = redis_client.delete(*keys_to_be_removed_from_redis)
        unmatch_ref = async_db.collection('LikesDislikes').document(user_id_1).collection("Unmatch").document(user_id_2)
        await unmatch_ref.set(match_doc)
        unmatch_store_success = redis_client.set(f"LikesDislikes:{user_id_1}:Unmatch:{user_id_2}",
                                                 json.dumps(match_doc))
        return unmatch_store_success


async def unmatch_task_recent_chats(user_id_1: str = None, user_id_2: str = None, redis_client: Redis = None):
    recent_chat_ref = async_db.collection('RecentChats').document(user_id_1).collection("Messages").document(user_id_2)
    await recent_chat_ref.delete()
    keys_to_be_removed_from_redis = [key for key in
                                     redis_client.scan_iter(f"RecentChats:{user_id_1}:Messages:{user_id_2}*")]
    if len(keys_to_be_removed_from_redis) > 0:
        no_of_keys_removed_from_redis = redis_client.delete(*keys_to_be_removed_from_redis)
    else:
        no_of_keys_removed_from_redis = 0
    return no_of_keys_removed_from_redis


async def rewind_given_swipe_task(current_user_id: str = None, swiped_user_id: str = None, redis_client: Redis = None,
                                  logger: Logger = None):
    db.collection('LikesDislikes').document(current_user_id).collection("Given").document(swiped_user_id).delete()
    keys_to_be_removed = [key for key in
                          redis_client.scan_iter(f"LikesDislikes:{current_user_id}:Given:{swiped_user_id}*")]
    logger.info(
        f"Current user id: {current_user_id}, swiped user id: {swiped_user_id}, keys to be removed: {keys_to_be_removed}")
    no_of_keys_removed_from_redis = redis_client.delete(*keys_to_be_removed)
    return no_of_keys_removed_from_redis


async def rewind_received_swipe_task(current_user_id: str = None, swiped_user_id: str = None,
                                     redis_client: Redis = None):
    db.collection('LikesDislikes').document(swiped_user_id).collection("Received").document(
        current_user_id).delete()
    keys_to_be_removed = [key for key in
                          redis_client.scan_iter(f"LikesDislikes:{swiped_user_id}:Received:{current_user_id}*")]
    no_of_keys_removed_from_redis = redis_client.delete(*keys_to_be_removed)
    return no_of_keys_removed_from_redis


async def rewind_task_function(current_user_id: str = None, swiped_user_id: str = None, redis_client: Redis = None,
                               logger=None):
    given_swipe_task = asyncio.create_task(
        rewind_given_swipe_task(current_user_id, swiped_user_id, redis_client, logger))
    received_swipe_task = asyncio.create_task(rewind_received_swipe_task(current_user_id, swiped_user_id, redis_client))
    return await asyncio.gather(*[given_swipe_task, received_swipe_task])


def report_profile_task(current_user_id=None, reported_profile_id=None, reason_given=None, description_given=None,
                        redis_client: Redis = None):
    """
    Report Profile Task:
        - Finds profile of the reported User from Cache. If not available, fetches from Firestore
        - Store Reported Profile in Firestore
        - Store Reported Profile in Cache with following key and value:
            key = Reported:geohash1....geohash:ProfileID
            val = Geoservice: geohash1....geohash:ProfileID

    :param current_user_id: Current User's ID
    :param reported_profile_id: Reported User's ID
    :param reason_given: Reason given for reporting the profile
    :param description_given: Detailed description for reporting the profile
    :param redis_client: Redis client instance

    :return: Boolean indicating status of storing record in redis
    """
    redis_query = redis_client.mget(f"Geoservice*{reported_profile_id}").pop()
    if redis_query:
        reported_profile = json.loads(redis_query)
    else:
        reported_profile = db.collection("Profiles").document(reported_profile_id).get()
        reported_profile = reported_profile.to_dict()
    db.collection('ReportedProfile').document(reported_profile_id).collection(current_user_id).document(
        "ReportingDetails").set({"reportedById": current_user_id,
                                 "idBeingReported": reported_profile_id,
                                 "reasonGiven": reason_given,
                                 "descriptionGiven": description_given,
                                 "timestamp": time.time()
                                 })
    religion = reported_profile['religion'] if 'religion' in reported_profile.keys() else "Other"
    key = f"Reported:{reported_profile['geohash1']}:{reported_profile['geohash2']}:{reported_profile['geohash3']}:" \
          f"{reported_profile['geohash4']}:{reported_profile['geohash5']}:{reported_profile['geohash']}:" \
          f"{reported_profile['genderIdentity']}:{religion}:{reported_profile['age']}:{reported_profile_id}"
    val = f"GeoService:{reported_profile['geohash1']}:{reported_profile['geohash2']}:{reported_profile['geohash3']}:" \
          f"{reported_profile['geohash4']}:{reported_profile['geohash5']}:{reported_profile['geohash']}:" \
          f"{reported_profile['genderIdentity']}:{religion}:{reported_profile['age']}:{reported_profile_id}"
    report_profile_success = redis_client.set(f"{key}", json.dumps(val))
    return report_profile_success
