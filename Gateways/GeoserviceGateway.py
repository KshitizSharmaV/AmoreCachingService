import pandas as pd
import asyncio
import flask
import logging
import json


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


async def GeoService_store_profiles(profile=None, redisClient=None, logger=None):
    try:
        # Remove the profile first before adding/updating if exists

        userDataFields = list(profile.keys())
        religion = profile['religion'] if 'religion' in userDataFields else "Other"
        # e.g. "GeoService:ts:tsx:tsx3:tsx3u:tsx3uuq6w1:male:45:8OQ8W2v6nOT4y3kqYqvVXFpQOaT2
        key = f"GeoService:{profile['geohash1']}:{profile['geohash2']}:{profile['geohash3']}:{profile['geohash4']}:{profile['geohash5']}:{profile['geohash']}:{profile['genderIdentity']}:{religion}:{profile['age']}:{profile['id']}"
        jsonObject_dumps = json.dumps(profile, indent=4, sort_keys=True, default=str)
        redisClient.set(key, jsonObject_dumps)
        logger.info(f"{key} storage was success")
        return True
    except Exception as e:
        logger.exception(f"{profile['id']}: Recommendation caching failed")
        logger.exception(f"{profile}")
        logger.exception(e)
        return False


def GeoService_get_fitered_profiles_on_params(**kwargs):
    # Usage Examples
    # MUST pass a redisClient & a logger
    # e.g. "GeoService:ts:tsx:tsx3:tsx3u:tsx3uuq6w1:male:Other:45:5.3:8OQ8W2v6nOT4y3kqYqvVXFpQOaT2"
    # e.g. GeoService:tx:*:*:*:*:*:*:*:*:*
    # e.g. GeoService:tx:*:*:*:*:*:*:*:*:8OQ8W2v6nOT4y3kqYqvVXFpQOaT2
    if ('logger' in kwargs) & ('redisClient' in kwargs):
        logger = kwargs['logger']
        redisClient = kwargs['redisClient']
    else:
        raise ValueError("Expecting logger and redisClient to be passed to function")
        return False
    
    geoData = {}
    profileMatches = []
        
    try:
        # Query Based on geohash
        # 'geohash1' : 5000 km
        # 'geohash2' : 1500 km
        # 'geohash3' : 200 km
        # 'geohash4' : 50 km
        # 'geohash5' : 5 km
        for i in list(range(1,6)):
            geoNumber = f"geohash{i}"
            geoData[geoNumber] = kwargs[geoNumber] if geoNumber in kwargs else "*"
        geoSearchQuery = f"GeoService:{geoData['geohash1']}:{geoData['geohash2']}:{geoData['geohash3']}:{geoData['geohash4']}:{geoData['geohash5']}"
        
        # Add gender to query
        genderPreference = kwargs["genderPreference"] if 'genderPreference' in kwargs else "*"
        initalSearchString = f"{geoSearchQuery}:{genderPreference}"
        
        # logger.info(f"STEP 1:{initalSearchString}")
        
        # Add religion to query
        religionSearchQueries = []
        if 'religionPreference' in kwargs:
            for religion in kwargs["religionPreference"]:
                query = f"{initalSearchString}:{religion}"
                religionSearchQueries.append(query)
        else:
            religion = "*"
            query = f"{initalSearchString}:{religion}"
            religionSearchQueries.append(query)
        
        # logger.info(f"STEP 2:{religionSearchQueries}")

        # Age Preference to query
        ageSearchQueries = []
        minAgePreference = kwargs["minAgePreference"] if 'minAgePreference' in kwargs else None
        maxAgePreference = kwargs["maxAgePreference"] if 'maxAgePreference' in kwargs else None
        if minAgePreference and maxAgePreference:
            for previousQuery in religionSearchQueries:
                for age in list(range(minAgePreference,maxAgePreference+1)):
                    query = f"{previousQuery}:{str(age)}"
                    ageSearchQueries.append(query)
        else:
            for previousQuery in religionSearchQueries:
                ageSearchQueries.append(f"{previousQuery}:*") 
                
        # logger.info(f"STEP 3:{ageSearchQueries}")
        
        # Add Profile id to filter on
        profileId = kwargs["profileId"] if 'profileId' in kwargs else "*"
        
        allProfilesMatch = []
        for query in ageSearchQueries:
            query = f"{query}:{profileId}"
            profileMatches = [key for key in redisClient.scan_iter(f"{query}")]
            allProfilesMatch.extend(profileMatches)
            log_profiles(query=query, allProfilesMatch=allProfilesMatch, logger=logger)

        return profileMatches
    except Exception as e:
        logger.exception(f"Failed to get recommendation from Caching Geo Service")
        logger.exception(e)
        return False

def log_profiles(query=None, allProfilesMatch=None, logger=None):
    logger.info(f"===============")
    logger.info(f"{query} execution query on redis")
    for profileId in allProfilesMatch:
        logger.info(profileId)
    

# Accepts geoService redis keys which just provide list of ids
def Geoservice_get_profile_Ids_from_redis_key(redisKeys=None):
    return [key.split(":")[-1] for key in redisKeys]

def Geoservice_calculate_geo_hash_from_radius(radius=None):
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
    

def GeoService_get_recommended_profiles_for_user(userId=None, filterData=None, redisClient=None, logger=None):
    try:
        redisGeoServicesKeys = GeoServices_get_redis_key_list_of_ids(profileIdList=[userId],redisClient=redisClient, logger=logger)
        if redisGeoServicesKeys:
            profileId = redisGeoServicesKeys.pop()
            userData = redisClient.mget(profileId)
            userData = userData.pop()
            # Convert the profile from string to dictionary
            userData = json.loads(userData)
            # Get filter the user wants
            geohashtype = Geoservice_calculate_geo_hash_from_radius(radius=filterData['radiusDistance'])
            # geohashtype = userData[geohashtype]
            recommendedProfilesKeys = GeoService_get_fitered_profiles_on_params(geohash2 = userData["geohash2"],
                                                                                redisClient=redisClient,
                                                                                logger=logger)
            logger.info(f"{userId}: {len(recommendedProfilesKeys)} recommendations fetched for user")
            return (userData, recommendedProfilesKeys)
        return False
    except Exception as e:
        logger.exception(f"Unable to get recommendation for {userId}")
        logger.exception(e)
        return False


def GeoServices_get_redis_key_list_of_ids(profileIdList=None, redisClient=None, logger=None):
    try:
        redisGeoKeysList = []
        # e.g. GeoService:dh:dhv:dhv6:dhv65:dhv65tqesm:female:Other:27:5.3:xlPsz0jEL5oMjNxqLNKk
        for profileId in profileIdList:
            userGeoServicekey = GeoService_get_fitered_profiles_on_params(profileId=profileId, redisClient=redisClient, logger=logger)
            if len(userGeoServicekey)==0:
                logger.error(f"Unable to find a GeoService profile for ID for {profileId}")
                continue
            # Get the only profile match from the query
            redisGeoKeysList.append(userGeoServicekey.pop())
        # return false if no match was found
        return redisGeoKeysList if len(redisGeoKeysList) != 0 else False
    except Exception as e:
        logger.exception(f"Unable to get geo keys for ids: {profileIdList}")
        logger.exception(e)
        return False

    
        

        
        

        