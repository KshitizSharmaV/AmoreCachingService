import asyncio
import traceback
import json
import time
from ProjectConf.AsyncioPlugin import make_sync_to_coroutine

from redis.client import Redis


async def write_one_profile_to_cache(profile=None, redisClient=None, logger=None, async_db=None):
    try:
        jsonObject_dumps = json.dumps(profile, indent=4, sort_keys=True, default=str)
        # Redis - Create a new document if doesn't already exist in the database
        redisClient.set(f"Profiles:{profile['id']}", jsonObject_dumps)
        logger.info(f"{profile['id']}: Successfully loaded profile in cache")
        await async_db.collection("Profiles").document(profile["id"]).update({u'wasProfileUpdated': False})
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
    logger.warning(f'{len(profileIdsNotInCache)} profiles not found in cache')
    newProfilesCached = await asyncio.gather(
        *[write_one_profile_to_cache_after_firebase_read(profileId=profileId, redisClient=redisClient,
                                                         logger=logger, async_db=async_db) for profileId in
          profileIdsNotInCache])
    newProfilesCached = [profile for profile in newProfilesCached if profile is not None]
    return newProfilesCached


def get_profiles_not_in_cache(profileIdList=None, redisClient=None):
    allCachedProfileIds = get_cached_profile_ids(redisClient=redisClient,
                                                 cacheFilterName="Profiles")
    # allCachedProfileIds = [id.replace("Profiles:", "") for id in allCachedProfileIds]
    return list(set(profileIdList) - set(allCachedProfileIds))


def get_cached_profile_ids(redisClient=None, cacheFilterName=None):
    profileIdsInCache = [key for key in redisClient.scan_iter(f"{cacheFilterName}:*")]
    profileIdsInCache = [profile_id.replace(f"{cacheFilterName}:", "") for profile_id in profileIdsInCache]
    return profileIdsInCache


def get_cached_profiles(redisClient: Redis = None, cacheFilterName=None):
    profileIdsInCache = [key for key in redisClient.scan_iter(f"{cacheFilterName}:*")]
    profileIdsInCache = redisClient.mget(profileIdsInCache)
    return profileIdsInCache


async def all_fresh_profiles_load(redisClient=None, logger=None, async_db=None, callFrom=None):
    profileIdsInCache = get_cached_profile_ids(redisClient=redisClient,
                                               cacheFilterName="Profiles")
    if len(profileIdsInCache) == 0:
        queryOn = 'isProfileActive'
        logger.info(f"Fresh profile load into firestore was initiated. Initiated by: {callFrom}")
    else:
        queryOn = 'wasProfileUpdated'
        logger.info(f"Refreshing the cache with updated profiles only. Initiated by: {callFrom}")
    query = async_db.collection("Profiles").where(queryOn, u'==', True)
    allProfiles = await query.get()
    logger.info(f"Updating Cache with {len(allProfiles)} profiles")
    # Writing the profiles to cache
    _ = await asyncio.gather(*[write_one_profile_to_cache(profile={"id": profile.id, **profile.to_dict()},
                                                          redisClient=redisClient,
                                                          logger=logger,
                                                          async_db=async_db) for profile in allProfiles])
    return


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
