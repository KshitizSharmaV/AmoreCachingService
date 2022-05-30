import asyncio
import traceback
import json
import time
import flask
from ProjectConf.AsyncioPlugin import make_sync_to_coroutine, run_coroutine
from Gateways.GeoserviceGateway import GeoService_store_profiles
from redis.client import Redis
from Gateways.GeoserviceGateway import GeoService_get_fitered_profiles_on_params, GeoServices_get_redis_key_list_of_ids

async def write_one_profile_to_cache(profile=None, redisClient=None, logger=None, async_db=None):
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


async def write_one_profile_to_cache_after_firebase_read(profileId=None, redisClient=None, logger=None, async_db=None):
    try:
        profileDoc = await async_db.collection('Profiles').document(profileId).get()
        profile = profileDoc.to_dict()
        if profile:
            profile["id"] = profileDoc.id
            _ = await write_one_profile_to_cache(profile=profile, redisClient=redisClient, logger=logger,
                                                 async_db=async_db)
            return profile
        else:
            # System should never receive an unrecognized ID
            logger.error(f"{profileId}: Unable to find profile in FirStore")
            return
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        logger.error(f"{profileId}: Failed to fetch profile from FirStore")
        return


# function accepts multiple Profile IDs
async def load_profiles_to_cache_from_firebase(profileIdsNotInCache=None, redisClient=None, logger=None, async_db=None):
    logger.warning(f'{len(profileIdsNotInCache)} GeoService profiles not found in cache')
    newProfilesCached = await asyncio.gather(
        *[write_one_profile_to_cache_after_firebase_read(profileId=profileId, redisClient=redisClient,
                                                         logger=logger, async_db=async_db) for profileId in
          profileIdsNotInCache])
    newProfilesCached = [profile for profile in newProfilesCached if profile is not None]
    return newProfilesCached


def get_profiles_not_in_cache(profileIdList=None, redisClient=None):
    allCachedProfileIds = get_cached_profile_ids(redisClient=redisClient,
                                                 cacheFilterName="GeoService")
    return list(set(profileIdList) - set(allCachedProfileIds))


def get_cached_profile_ids(redisClient=None, cacheFilterName=None):
    profileIdsInCache = [key for key in redisClient.scan_iter(f"{cacheFilterName}:*")]
    profileIdsInCache = [profile_id.replace(f"{cacheFilterName}:", "") for profile_id in profileIdsInCache]
    return profileIdsInCache


async def get_profiles_already_seen_by_user(current_user_id: str = None, redis_client: Redis = None):
    """
    TO DO LATER: What if respective profiles not in cache
    """
    get_cached_profile_coro = make_sync_to_coroutine(get_cached_profile_ids)
    given_filter = f"LikesDislikes:{current_user_id}:Given"
    ids_given_task = asyncio.create_task(
        get_cached_profile_coro(redisClient=redis_client, cacheFilterName=given_filter))
    match_filter = f"LikesDislikes:{current_user_id}:Match"
    ids_match_task = asyncio.create_task(
        get_cached_profile_coro(redisClient=redis_client, cacheFilterName=match_filter))
    unmatch_filter = f"LikesDislikes:{current_user_id}:Unmatch"
    ids_unmatch_task = asyncio.create_task(
        get_cached_profile_coro(redisClient=redis_client, cacheFilterName=unmatch_filter))
    return await asyncio.gather(*[ids_unmatch_task, ids_match_task, ids_given_task])



async def get_profile_by_ids(redisClient=None, profileIdList=None, logger=None, async_db=None):
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
            if len(redisGeoServicesKeys) != len(allProfilesData):
                # Oh oh - Looks like profile is missing from cache. 
                profileIdsNotInCache = get_profiles_not_in_cache(profileIdList=profileIdList, redisClient=redisClient)
                newProfilesCached = await load_profiles_to_cache_from_firebase(profileIdsNotInCache=profileIdsNotInCache,
                                                                            redisClient=redisClient, logger=logger,
                                                                            async_db=async_db)
                allProfilesData.extend(newProfilesCached)
        else:
            logger.warning(f'0 profiles were returned for following profiles: {",".join(profileIdList)}')    
            allProfilesData = await load_profiles_to_cache_from_firebase(profileIdsNotInCache=profileIdList,
                                                                            redisClient=redisClient, logger=logger,
                                                                            async_db=async_db)
        return allProfilesData
    except Exception as e:
        logger.error(f'An error occured in fetching profiles for ids: {",".join(profileIdList)}')
        logger.exception(e)
        return False
        
