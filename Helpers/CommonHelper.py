import asyncio
import traceback
import json

async def write_to_cache(profile=None, redisClient=None, logger=None, async_db=None):
    try:
        jsonObject_dumps = json.dumps(profile, indent=4, sort_keys=True, default=str)
        # MongoDB - Create a new document if doesn't already exist in the database
        redisClient.set(f"Profiles:{profile['id']}", jsonObject_dumps)
        logger.info(f"{profile['id']}: Successfully loaded data in cache")
        await async_db.collection("Profiles").document(profile["id"]).update({u'wasProfileUpdated':False})
        return profile
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        logger.error(f"{profile['id']}: Failed to load data in cache")
        return False


async def write_profiles_to_cache_after_read(profileId=None, redisClient=None, logger=None, async_db=None):
    try:
        profile = await async_db.collection('Profiles').document(profileId).get()
        profile_temp = profile.to_dict()
        if profile_temp:
            profile_temp["id"] = profile.id
            jsonObject_dumps = json.dumps(profile_temp, indent=4, sort_keys=True, default=str)
            redisClient.set(f"Profiles:{profileId}", jsonObject_dumps)
            logger.info(f"{profileId}: Fetched FirSto Profiles & stored in cache")
            return profile_temp
        else:
            # RAISE AN ALERT - System should never receive an unrecognized ID
            logger.error(f"{profileId}: Unable to find profile in FirSto")
            return
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        logger.error(f"{profileId}: Failed to get profile from FirSto")
        return
    
