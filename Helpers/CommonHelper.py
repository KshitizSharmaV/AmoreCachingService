
import asyncio
import traceback


async def write_to_cache(profile=None, amoreCacheDB=None, logger=None, async_db=None):
    try:
        # MongoDB - Create a new document if doesn't already exist in the database
        amoreCacheDB["Profiles"].update_one({'_id': profile['_id']},{"$set": profile}, upsert=True)
        logger.info(f"{profile['_id']}: Successfully loaded data in cache")
        # Firestore - Writting back wasProfileUpdated flag to False so service doesn't read again
        await async_db.collection("Profiles").document(profile['_id']).update({u'wasProfileUpdated': False})
        return profile
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        logger.error(f"{profile['_id']}: Failed to load data in cache")
        return False


async def write_to_cache_after_read(profileId=None, amoreCacheDB=None, logger=None, async_db=None):
    try:
        profile = await async_db.collection('Profiles').document(profileId).get()
        profile_temp = profile.to_dict()
        if profile_temp:
            profile_temp["_id"] = profile.id  # un-comment for production
            profile = await write_to_cache(profile=profile_temp, 
                                    amoreCacheDB=amoreCacheDB, 
                                    logger=logger, 
                                    async_db=async_db)
            return profile
        else:
            # RAISE AN ALERT - System should never receive an unrecognized ID
            logger.error(f"{profileId}: Unable to find profile in firestore")
            return
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        logger.error(f"{profileId}: Failed to get profile from firestore")
        return

