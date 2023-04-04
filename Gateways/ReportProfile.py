import time
import asyncio
from redis.commands.json.path import Path
from ProjectConf.FirestoreConf import db
from ProjectConf.RedisConf import redis_client
from Gateways.MatchUnmatchGatewayEXT import RecentChats_Unmatch_Delete_Chat
from Utilities.LogSetup import configure_logger
logger = configure_logger(__name__)

def Report_profile_task(current_user_id=None, reported_profile_id=None, reason_given=None, description_given=None):
    """
    Report Profile Task:
        - Finds profile of the reported User from Cache. If not available, fetches from Firestore
        - Store Reported Profile in Firestore
        - Store Reported Profile in Cache with following key and value:
            key = Reported:geohash1....geohash:ProfileID
    
    :param current_user_id: Current User's ID
    :param reported_profile_id: Reported User's ID
    :param reason_given: Reason given for reporting the profile
    :param description_given: Detailed description for reporting the profile
    
    :return: Boolean indicating status of storing record in redis
    """
    try:
        store_doc = {
                "reportedById": current_user_id,
                "idBeingReported": reported_profile_id,
                "reasonGiven": reason_given,
                "descriptionGiven": description_given,
                "timestamp": time.time()
            }
        db.collection('ReportedProfile').document(reported_profile_id).collection(current_user_id).document("ReportingDetails").set(store_doc)
        key = f"ReportedProfile:{reported_profile_id}:{current_user_id}"
        redis_client.json().set(key, Path.root_path(), store_doc)
        return True
    except Exception as e:
        logger.exception(f"Unable to write reported profile to firestore/redis {reported_profile_id}")
        logger.exception(e)
        return False


async def ReportProfile_remove_recent_chats(current_user_id, other_user_id):
    task_recent_chats_current_user = asyncio.create_task(
        RecentChats_Unmatch_Delete_Chat(current_user_id, other_user_id))
    task_recent_chats_other_user = asyncio.create_task(RecentChats_Unmatch_Delete_Chat(other_user_id, current_user_id))
    return await asyncio.gather(*[task_recent_chats_current_user,
                                  task_recent_chats_other_user])