import asyncio
import json
import time
from redis.client import Redis
from ProjectConf.FirestoreConf import async_db, db
from logging import Logger

def Report_profile_task(current_user_id=None, reported_profile_id=None, reason_given=None, description_given=None,
                        redisClient: Redis = None):
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
    redis_query = redisClient.mget(f"Geoservice*{reported_profile_id}").pop()
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
    report_profile_success = redisClient.set(f"{key}", json.dumps(val))

    #  TODO
    # if already liked, delete the likesdislikes 
    return report_profile_success
