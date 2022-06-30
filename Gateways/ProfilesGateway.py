import asyncio
from dataclasses import asdict
import traceback
import json
import time
import flask
from redis.client import Redis
from Gateways.GeoserviceEXTs.GeoserviceGatewayEXT import Profile
from Utilities.DictOps import ignore_none
from Gateways.GeoserviceGateway import GeoService_store_profiles


async def ProfilesGateway_write_one_profile_to_cache(profile: dict = None, redisClient: Redis = None, logger=None,
                                                     async_db=None):
    try:
        # Redis - Store the profile in redis for recommendation engine
        _ = await GeoService_store_profiles(profile=profile,
                                            redisClient=redisClient,
                                            logger=logger)
        return profile
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        logger.error(f"{profile['id']}: Failed to load profile in cache")
        return


async def ProfilesGateway_write_one_profile_to_cache_after_firebase_read(profileId: str = None,
                                                                         redisClient: Redis = None, logger=None,
                                                                         async_db=None):
    try:
        profileDoc = await async_db.collection('Profiles').document(profileId).get()
        profile = profileDoc.to_dict()
        if profile:
            profile["id"] = profileDoc.id
            _ = await ProfilesGateway_write_one_profile_to_cache(profile=profile, redisClient=redisClient,
                                                                 logger=logger,
                                                                 async_db=async_db)
            return profile
        else:
            # System should never receive an unrecognized ID
            logger.error(f"{profileId}: Unable to find profile in FireStore")
            return
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        logger.error(f"{profileId}: Failed to fetch profile from FireStore")
        return


# function accepts multiple Profile IDs
async def ProfilesGateway_load_profiles_to_cache_from_firebase(profileIdsNotInCache=None, redisClient=None, logger=None,
                                                               async_db=None):
    logger.warning(f'{len(profileIdsNotInCache)} GeoService profiles not found in cache')
    logger.warning(f'Loading profile from firestore {profileIdsNotInCache}')
    newProfilesCached = await asyncio.gather(
        *[ProfilesGateway_write_one_profile_to_cache_after_firebase_read(profileId=profileId, redisClient=redisClient,
                                                                         logger=logger, async_db=async_db) for profileId
          in profileIdsNotInCache])
    newProfilesCached = [profile for profile in newProfilesCached if profile is not None]
    return newProfilesCached


def ProfilesGateway_get_profiles_not_in_cache(profileIdList=None, redisClient=None):
    allGeoServiceProfileIdsInCache = [key for key in redisClient.scan_iter(f"GeoService:*")]
    allCachedProfileIds = [profileId.split(":")[-1] for profileId in allGeoServiceProfileIdsInCache]
    return list(set(profileIdList) - set(allCachedProfileIds))


def ProfilesGateway_get_cached_profile_ids(redisClient=None, cacheFilterName=None):
    profileIdsInCache = [profile_id.replace(f"{cacheFilterName}:", "") for profile_id in profileIdsInCache]
    return profileIdsInCache


async def ProfilesGateway_get_profile_by_ids(redisClient: Redis = None, profileIdList=None, logger=None, async_db=None):
    """
    Accepts list of profile ids & returns a list of profiles data
    Checks for profiles not present in Redis, fetches them and stores into Redis

    :param profileIdList: list of profile Ids
    :type profileIdList: list
    :param redisClient: Redis client instance
    :type redisClient: Redis
    :param logger: Logger instance for custom logging
    :param async_db: Firestore Async DB client instance
    :return: A list of profile data
    """
    try:
        all_profiles_data = []
        fetched_profiles_ids = set()
        for profile_id in profileIdList:
            profile = Profile.decode_data_from_redis(redisClient.hgetall(f"profile:{profile_id}"))
            if profile.id:
                all_profiles_data.append(asdict(profile, dict_factory=ignore_none))
                fetched_profiles_ids.add(profile_id)
        keys_not_in_cache = list(set(profileIdList).difference(fetched_profiles_ids)) \
            if len(fetched_profiles_ids) != len(profileIdList) else []
        if not len(all_profiles_data):
            logger.warning(f'0 profiles were returned for following profiles: {",".join(profileIdList)}')
        if len(keys_not_in_cache) > 0:
            new_profiles_cached = await ProfilesGateway_load_profiles_to_cache_from_firebase(
                profileIdsNotInCache=keys_not_in_cache,
                redisClient=redisClient, logger=logger,
                async_db=async_db)
            all_profiles_data.extend(new_profiles_cached)
        return all_profiles_data
    except Exception as e:
        logger.error(f'An error occurred in fetching profiles for ids: {",".join(profileIdList)}')
        logger.exception(e)
        return False
