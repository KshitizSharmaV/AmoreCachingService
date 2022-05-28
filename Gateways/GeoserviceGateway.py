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
### On top of these recommendation profiles add following differnet kinds of profiles: 
######## a. Top Scoring Profiles in the cluster & cloose to the user
######## b. Boosted Profiles


async def GeoService_store_profiles(profile=None, redisClient=None, logger=None):
    try:
        userDataFields = list(profile.keys())
        religion = profile['religion'] if 'religion' in userDataFields else "Other"
        # e.g. "GeoService:ts:tsx:tsx3:tsx3u:tsx3uuq6w1:male:Other:45:5.3:8OQ8W2v6nOT4y3kqYqvVXFpQOaT2
        key = f"GeoService:{profile['geohash2']}:{profile['geohash3']}:{profile['geohash4']}:{profile['geohash5']}:{profile['geohash']}:{profile['genderIdentity']}:{religion}:{profile['age']}:{profile['id']}"
        jsonObject_dumps = json.dumps(profile, indent=4, sort_keys=True, default=str)
        redisClient.set(key, jsonObject_dumps)
        logger.info(f"{key} storage was success")
        return True
    except Exception as e:
        logger.error(f"{profile['id']}: Recommendation caching failed")
        logger.error(f"{profile}")
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

    try:
        geohash2 = kwargs['geohash2'] if 'geohash2' in kwargs else "*"
        geohash3 = kwargs['geohash3'] if 'geohash3' in kwargs else "*"
        geohash4 = kwargs['geohash4'] if 'geohash4' in kwargs else "*"
        geohash5 = kwargs['geohash5'] if 'geohash5' in kwargs else "*"
        geohash = kwargs['geohash'] if 'geohash' in kwargs else "*"
        genderIdentity = kwargs['genderIdentity'] if 'genderIdentity' in kwargs else "*"
        religion = kwargs['religion'] if 'religion' in kwargs else "*"
        age = kwargs['age'] if 'age' in kwargs else "*"
        height = kwargs['height'] if 'height' in kwargs else "*"
        id = kwargs['id'] if 'id' in kwargs else "*"
        searchQuery = f'GeoService:{geohash2}:{geohash3}:{geohash4}:{geohash5}:{geohash}:{genderIdentity}:{religion}:{age}:{id}'
        profileMatches = [key for key in redisClient.scan_iter(f"{searchQuery}")]
        # log_profiles(profileMatches=profileMatches, logger=logger, searchQuery=searchQuery)ß
        return profileMatches
    except Exception as e:
        logger.exception(f"{searchQuery}: Failed to get recommendation from Caching Geo Service")
        logger.exception(e)
        return False


def log_profiles(profileMatches=None, logger=None, searchQuery=None):
    logger.info(f"{searchQuery} executing query to get data from cache")
    print("*******************************")
    for profileId in profileMatches:
        print(profileId)
    print(len(profileMatches))
    print("**************")


async def GeoService_get_recommended_profiles_for_user(userId=None, redisClient=None, logger=None):
    try:
        # e.g. GeoService:dh:dhv:dhv6:dhv65:dhv65tqesm:female:Other:27:5.3:xlPsz0jEL5oMjNxqLNKk
        userGeoServicekey = GeoService_get_fitered_profiles_on_params(id=userId, redisClient=redisClient, logger=logger)
        # Get the only profile match from the query
        profileKey = userGeoServicekey.pop()
        userData = redisClient.mget(profileKey)
        userData = userData[0]
        # Convert the profile from string to dictionary
        userData = json.loads(userData)
        # Get filter the user wants
        genderPrefernce = "Male" if userData['showMePreference'] == "Women" else (
            "Male" if userData['showMePreference'] == "Men" else "*")
        recommendedProfilesKeys = GeoService_get_fitered_profiles_on_params(geohash3=userData["geohash3"],
                                                                            genderIdentity=genderPrefernce,
                                                                            redisClient=redisClient,
                                                                            logger=logger)
        logger.info(f"{userId}: {len(recommendedProfilesKeys)} recommendations fetched for user")
        return (userData, recommendedProfilesKeys)
    except Exception as e:
        logger.exception(f"{userId}: Failed to get recommendation for user")
        logger.exception(e)
        return False
