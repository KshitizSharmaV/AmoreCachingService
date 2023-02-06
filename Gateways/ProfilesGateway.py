import asyncio
import traceback
from Gateways.ProfileQueryModel import serialise_deserialise_date_in_profile
from Gateways.ProfilesGatewayEXT import Profiles_store_profiles
from ProjectConf.RedisConf import redis_client
from ProjectConf.FirestoreConf import async_db
from Utilities.LogSetup import configure_logger
logger = configure_logger(__name__)


async def ProfilesGateway_write_one_profile_to_cache_after_firebase_read(profileId: str = None):
    """
    Call this function when you want to fetch a profile from firestore, it also stores the profile
    in the redis. Pass the profileId to this function

    :param profile: profileId: String
    :return profile for the id
    """
    try:
        profileDoc = await async_db.collection('Profiles').document(profileId).get()
        profile = profileDoc.to_dict()
        if profile:
            profile["id"] = profileDoc.id
            _ = await Profiles_store_profiles(profile=profile)
            return profile
        else:
            # System should never receive an unrecognized ID
            logger.error(f"{profileId}: Unable to find profile in FireStore")
            return None
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        logger.error(f"{profileId}: Failed to fetch profile from FireStore")
        return False


# Function accepts multiple Profile IDs
async def ProfilesGateway_load_profiles_to_cache_from_firebase(profileIdsNotInCache=None):
    """
    Accepts list of ids and returns profiles for them. Usually called when a profile id isn't
    present in redis
    
    :param profileIdsNotInCache: [String]: list of profile ids you want to fetch data for
    :return new profiles cached
    """
    logger.warning(f'{len(profileIdsNotInCache)} GeoService profiles not found in cache')
    logger.warning(f'Loading profile from firestore {profileIdsNotInCache}')
    newProfilesCached = await asyncio.gather(*[ProfilesGateway_write_one_profile_to_cache_after_firebase_read(profileId=profileId) for profileId in profileIdsNotInCache])
    newProfilesCached = [profile for profile in newProfilesCached if profile is not None]
    return newProfilesCached

async def ProfilesGateway_get_profile_by_ids(profileIdList=None):
    """
    Accepts list of profile ids & returns a list of profiles data
    Checks for profiles not present in Redis, fetches them and stores into Redis

    :param profileIdList: list of profile Ids
    :type profileIdList: list
    :return: A list of profile data
    """
    try:
        all_profiles_data = []
        fetched_profiles_ids = set()
        for profile_id in profileIdList:
            profile = redis_client.json().get(f"profile:{profile_id}")
            if profile.get('id'):
                profile = serialise_deserialise_date_in_profile(profile_json=profile, deserialise=True)
                all_profiles_data.append(profile)
                fetched_profiles_ids.add(profile_id)
        keys_not_in_cache = list(set(profileIdList).difference(fetched_profiles_ids)) if len(fetched_profiles_ids) != len(profileIdList) else []
        if not len(all_profiles_data):
            logger.warning(f'0 profiles were returned for following profiles: {",".join(profileIdList)}')
        print(keys_not_in_cache)
        if len(keys_not_in_cache) > 0:
            new_profiles_cached = await ProfilesGateway_load_profiles_to_cache_from_firebase(profileIdsNotInCache=keys_not_in_cache)
            all_profiles_data.extend(new_profiles_cached)
        print(all_profiles_data)
        return all_profiles_data
    except Exception as e:
        logger.error(f'An error occurred in fetching profiles for ids: {",".join(profileIdList)}')
        logger.exception(e)
        return False
