import asyncio
import traceback
import json
import time
import flask
from redis.client import Redis

from Gateways.GeoserviceGateway import GeoServices_get_redis_key_list_of_ids, GeoService_store_profiles

async def ProfilesGateway_write_one_profile_to_cache(profile=None, redisClient=None, logger=None, async_db=None):
    try:
        jsonObject_dumps = json.dumps(profile, indent=4, sort_keys=True, default=str)
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


async def ProfilesGateway_write_one_profile_to_cache_after_firebase_read(profileId=None, redisClient=None, logger=None, async_db=None):
    try:
        profileDoc = await async_db.collection('Profiles').document(profileId).get()
        profile = profileDoc.to_dict()
        if profile:
            profile["id"] = profileDoc.id
            _ = await ProfilesGateway_write_one_profile_to_cache(profile=profile, redisClient=redisClient, logger=logger,
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
async def ProfilesGateway_load_profiles_to_cache_from_firebase(profileIdsNotInCache=None, redisClient=None, logger=None, async_db=None):
    logger.warning(f'{len(profileIdsNotInCache)} GeoService profiles not found in cache')
    logger.warning(f'Loading profile from firestore {profileIdsNotInCache}')
    newProfilesCached = await asyncio.gather(
        *[ProfilesGateway_write_one_profile_to_cache_after_firebase_read(profileId=profileId, redisClient=redisClient,
                                                         logger=logger, async_db=async_db) for profileId in
          profileIdsNotInCache])
    newProfilesCached = [profile for profile in newProfilesCached if profile is not None]
    return newProfilesCached


def ProfilesGateway_get_profiles_not_in_cache(profileIdList=None, redisClient=None):
    allGeoServiceProfileIdsInCache = [key for key in redisClient.scan_iter(f"GeoService:*")]
    allCachedProfileIds = [profileId.split(":")[-1] for profileId in allGeoServiceProfileIdsInCache]
    return list(set(profileIdList) - set(allCachedProfileIds))

def ProfilesGateway_get_cached_profile_ids(redisClient=None, cacheFilterName=None):
    profileIdsInCache = [profile_id.replace(f"{cacheFilterName}:", "") for profile_id in profileIdsInCache]
    return profileIdsInCache


async def ProfilesGateway_get_profile_by_ids(redisClient=None, profileIdList=None, logger=None, async_db=None):
    '''
    Accepts list of profile ids & returns a list of profiles data
        :params profileIdList: list of profile Ids
    return: A list of profile data
    '''
    try:
        allProfilesData = []
        # Find those Profiles in the local cache
        redisGeoServicesKeys = GeoServices_get_redis_key_list_of_ids(profileIdList=profileIdList, redisClient=redisClient, logger=logger)
        if redisGeoServicesKeys:
            # logger.info(f"ProfileIdCachedKeys : {redisGeoServicesKeys}")
            profiles_array = [redisClient.mget(geoKey).pop() for geoKey in  redisGeoServicesKeys]
            # logger.info(f"profiles_array : {profiles_array}")
            # Iterate over the cached profiles cursor
            allProfilesData = [json.loads(profile) for profile in profiles_array if profile]
            # Check if profile is missing from the response data, means profile not in cache
            if len(profileIdList) != len(allProfilesData):
                # Oh oh - Looks like profile is missing from cache. 
                profileIdsNotInCache = ProfilesGateway_get_profiles_not_in_cache(profileIdList=profileIdList, redisClient=redisClient)
                newProfilesCached = await ProfilesGateway_load_profiles_to_cache_from_firebase(profileIdsNotInCache=profileIdsNotInCache,
                                                                            redisClient=redisClient, logger=logger,
                                                                            async_db=async_db)
                allProfilesData.extend(newProfilesCached)
        else:
            logger.warning(f'0 profiles were returned for following profiles: {",".join(profileIdList)}')    
            allProfilesData = await ProfilesGateway_load_profiles_to_cache_from_firebase(profileIdsNotInCache=profileIdList,
                                                                            redisClient=redisClient, logger=logger,
                                                                            async_db=async_db)
        return allProfilesData
    except Exception as e:
        logger.error(f'An error occured in fetching profiles for ids: {",".join(profileIdList)}')
        logger.exception(e)
        return False
        