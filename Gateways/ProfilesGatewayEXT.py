from Gateways.ProfileQueryModel import serialise_deserialise_date_in_profile
from ProjectConf.RedisConf import redis_client
from redis.commands.json.path import Path
from Utilities.LogSetup import configure_logger

logger = configure_logger(__name__)


async def Profiles_store_profiles(profile=None):
    """
    Store Profile in Redis Cache.
        - Write/Update current Profile data in Redis

    :param profile: Profile Dict/JSON
    
    :return: Status of store action as Boolean
    """
    try:
        key = f"profile:{profile['id']}"
        profile = serialise_deserialise_date_in_profile(profile_json=profile, serialise=True)
        redis_client.json().set(key, Path.root_path(), profile)
        logger.info(f"Profile stored/updated in cache with key: {key}")
        return True
    except Exception as e:
        logger.exception(f"{profile['id']}: Recommendation caching failed")
        logger.exception(f"{profile}")
        logger.exception(e)
        return False


def Profiles_calculate_geo_hash_from_radius(radius=None):
    """
    'geohash1' : 5000 km
    'geohash2' : 1500 km
    'geohash3' : 200 km
    'geohash4' : 50 km
    'geohash5' : 5 km
    """
    if radius <= 5:
        return "geohash5"
    elif radius <= 50:
        return "geohash4"
    elif radius <= 200:
        return "geohash3"
    elif radius <= 1500:
        return "geohash2"
    else:
        return "geohash1"

