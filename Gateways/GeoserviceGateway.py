from dataclasses import asdict
import pandas as pd
import asyncio
import flask
import logging
import time
import json
from redis.client import Redis
from Utilities.DictOps import ignore_none
from Gateways.GeoserviceEXTs.GeoserviceGatewayEXT import QueryBuilder, Profile
from redis.commands.search.query import Query


# Filter on Prefernces:
#### radiusDistance Preference: Get all Profiles Wthin Radius ?
#### Remove Profiles already seen by user
#### Is Profile Active ?
#### Male or Female ?
#### religionPrefernece ?
#### agePreference
#### careerPreference
#### educationPreference
#### heightAdjustment
# Profiles not already seen by user
# Profiles are not Blocked
# Arrange the deck according to people score(Grade: Completion Score(20), LikesDislikes=)
# We arrange the deck order
# send profile back

# Once you have a list of matching profile store those profiles to firestore
# Divide the list of profiles into buckets of N
# The N number should be variable for each user depending on the swipe speed of a user. But for now we will set it at 100(default)
# Store these buckets of documents into firestore

# Extra Pipeline, Add profiles to recommendations before sending back
### On top of these recommendation profiles add following differnet kinds of profiles e.g.
######## a. Top Scoring Profiles in the cluster & cloose to the user
######## b. Boosted Profiles


async def GeoService_store_profiles(profile=None, redisClient: Redis = None, logger=None):
    """
    Store Profile in Redis Cache.
        - Write/Update current Profile data in Redis

    :param profile: Profile Dict/JSON
    :param redisClient: Redis server Client
    :type redisClient: Redis
    :param logger: Current app logger for logging on stdout

    :return: Status of store action as Boolean
    """
    try:
        key = f"profile:{profile['id']}"
        val = Profile.encode_data_for_redis(profile)
        redisClient.hset(key, mapping=val)
        logger.info(f"Profile stored/updated in cache with key: {key}")
        return True
    except Exception as e:
        logger.exception(f"{profile['id']}: Recommendation caching failed")
        logger.exception(f"{profile}")
        logger.exception(e)
        return False


def GeoService_get_fitered_profiles_on_params(**kwargs):
    """
    Builds the redis-query for filters provided. Queries Redis for the given arguments
    and returns the resultant profiles.
    Tries creating profiles index in Redis before querying.

    :param kwargs: Keyword arguments, logger and redisClient required arguments. Accepts filter parameters for fetching
        profiles.

    :return: List of profile dicts matched based on filters.
    """
    if ('logger' in kwargs) & ('redisClient' in kwargs):
        logger = kwargs['logger']
        redisClient = kwargs['redisClient']
    else:
        raise ValueError("Expecting logger and redisClient to be passed to function")

    geoData = {}
    profileMatches = []

    try:
        """
        List of profiles: allProfilesMatch
        Using Pandas, Filter the profiles further on Passion, Politics, School, Work, etc 
        Sort it based on: 
            - Boosted profiles(sorted on timestamp), 
            - "Likes received" profiles(sorted on timestamp), 
            - fresh profiles and old profiles, in that particular order

        Indian - Global - Likes an American (Global Off)
        """

        '''
        Accepting: Filters, geohash type
        '''
        query_builder_args = kwargs
        for arg in ['redisClient', 'logger', 'profileId']:
            if arg in query_builder_args.keys():
                if arg == 'profileId':
                    query_builder_args['id'] = query_builder_args['profileId']
                query_builder_args.pop(arg)
        query = QueryBuilder(**query_builder_args).query_builder()
        logger.warning(f"QUERY FOR RECOMMENDATIONS: {query}")
        result_profiles = redisClient.ft("idx:profile").search(Query(query_string=query).paging(0, 10))
        logger.warning(f"LENGTH OF RECOMMENDATIONS: {result_profiles.total}")
        profileMatches = [asdict(Profile.decode_data_from_redis(doc.__dict__)) for doc in result_profiles.docs]
        return profileMatches
    except Exception as e:
        logger.exception(f"Failed to get recommendation from Caching Geo Service")
        logger.exception(e)
        return profileMatches


def log_profiles(query=None, allProfilesMatch=None, logger=None):
    # logger.info(f"===============")
    logger.info(f"{query} execution query on redis")
    # for profileId in allProfilesMatch:
    #     logger.info(profileId)


# Accepts geoService redis keys which just provide list of ids
def Geoservice_get_profile_Ids_from_redis_key(redisKeys=None):
    return [key.split(":")[-1] for key in redisKeys]


def Geoservice_calculate_geo_hash_from_radius(radius=None):
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


def GeoService_get_recommended_profiles_for_user(userId=None, filterData=None, redisClient: Redis = None, logger=None):
    """
    Get recommended profiles based on filter data provided.

    :param userId: Current user's user ID
    :type userId: str
    :param filterData: Current user's desired filters
    :type filterData: dict
    :param redisClient: Redis client instance
    :type redisClient: Redis
    :param logger: Logger instance for custom logging

    :return: A tuple of user's profile data(dict) and list of recommended profiles' dicts.
    """
    userData, recommendedProfiles = None, []
    try:
        current_user_profile = asdict(Profile.decode_data_from_redis(redisClient.hgetall(f"profile:{userId}")),
                                      dict_factory=ignore_none)
        if current_user_profile.get('id'):
            geohashtype = Geoservice_calculate_geo_hash_from_radius(radius=filterData['radiusDistance'])
            recommendedProfiles = GeoService_get_fitered_profiles_on_params(geohash2=current_user_profile["geohash2"],
                                                                            redisClient=redisClient,
                                                                            logger=logger)
            logger.info(f"{userId}: {len(recommendedProfiles)} recommendations fetched for user")
            return (current_user_profile, recommendedProfiles)
        return (current_user_profile, recommendedProfiles)

    except Exception as e:
        logger.exception(f"Unable to get recommendation for {userId}")
        logger.exception(e)
        return (userData, recommendedProfiles)


"""
UNUSED FUNCTION. TO BE SAFELY REMOVED LATER.
"""
def GeoServices_get_redis_key_list_of_ids(profileIdList=None, redisClient=None, logger=None):
    """
    Fetch Redis-keys for list of profile IDs given

    :param profileIdList: List of Profile IDs
    :type profileIdList: list
    :param redisClient: Redis: Redis client instance
    :type redisClient: Redis
    :param logger: Logging.logger: Logger instance for custom logging

    :return: List of redis-keys for profiles (GeoService Keys)
    """
    redisGeoKeysList = []
    try:
        # e.g. GeoService:dh:dhv:dhv6:dhv65:dhv65tqesm:female:Other:27:5.3:xlPsz0jEL5oMjNxqLNKk
        for profileId in profileIdList:
            userGeoServicekey = GeoService_get_fitered_profiles_on_params(profileId=profileId, redisClient=redisClient, logger=logger)
            if len(userGeoServicekey)==0:
                logger.warning(f"Unable to find a GeoService profile for ID for {profileId}")
                continue
            # Get the only profile match from the query
            redisGeoKeysList.append(userGeoServicekey.pop())
        return redisGeoKeysList
    except Exception as e:
        logger.exception(f"Unable to get geo keys for ids: {profileIdList}")
        logger.exception(e)
        return redisGeoKeysList
