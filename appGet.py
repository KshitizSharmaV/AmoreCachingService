import flask
from flask import Blueprint, current_app, jsonify, request
import json
from itertools import chain
from ProjectConf.AsyncioPlugin import run_coroutine
from ProjectConf.ReddisConf import redisClient
from ProjectConf.FirestoreConf import async_db, db
from Gateways.ProfilesGateway import load_profiles_to_cache_from_firebase, get_profiles_not_in_cache, \
    get_cached_profile_ids, all_fresh_profiles_load, get_profiles_already_seen_by_user, get_cached_profiles, \
    get_profile_by_ids
from Gateways.RecommendationGateway import GeoService_get_recommended_profiles_for_user

import logging
import traceback

app_get = Blueprint('appGet', __name__)
logger = logging.getLogger()

# Get Profiles using their IDs
@current_app.route('/getprofilesbyids', methods=['GET'])
def get_profiles_by_ids():
    try:
        # Get the list of profile ids from the body
        profileIdList = request.get_json().get('profileIdList')
        allProfilesData = get_profile_by_ids(redisClient=redisClient, 
                                            profileIdList=profileIdList, 
                                            logger=current_app.logger)
        return json.dumps(allProfilesData, indent=4, sort_keys=True, default=str)
    except Exception as e:
        current_app.logger.error(f"Failed to fetch profiles from gateway")
        current_app.logger.exception(e)
        return False

# Get the profiles ids which are store in cache. 
# Assumption: All the active profiles in firestore are in Redis cache to. - Run the ProfilesCachingService to refersh all profiles automatically
@current_app.route('/getcachedprofileids', methods=['GET'])
def get_cached_profile_ids_route():
    try:
        # Get the cacheFilterName
        cacheFilterName = request.get_json().get('cacheFilterName')
        cachedProfileIds = get_cached_profile_ids(redisClient=redisClient, 
                                                  cacheFilterName=cacheFilterName)
        if len(cachedProfileIds) == 0:
            future = run_coroutine(all_fresh_profiles_load(redisClient=redisClient, 
                                                            logger=current_app.logger,
                                                            async_db=async_db, 
                                                            callFrom="get_cached_profile_ids_route api"))
            newProfilesCached = future.result()
            cachedProfileIds = get_cached_profile_ids(redisClient=redisClient, 
                                                  cacheFilterName=cacheFilterName)
        responseData = [id.replace("Profiles:","") for id in cachedProfileIds]
        current_app.logger.info(f"{len(responseData)} Profile Ids were fetched from cache")
        return json.dumps(responseData)
    except Exception as e:
        current_app.logger.error(f"Failed to get the cached user ids from gateway")
        current_app.logger.exception(e)
        return json.dumps({'status':False})


@current_app.route('/getallcachedprofiles', methods=['GET'])
def get_all_cached_profiles_route():
    try:
        # Get the cache_filter_name
        cache_filter_name = request.get_json().get('cacheFilterName')
        cached_profile_ids = get_cached_profiles(redisClient=redisClient, cacheFilterName=cache_filter_name)
        if len(cached_profile_ids) == 0:
            future = run_coroutine(all_fresh_profiles_load(redisClient=redisClient, logger=current_app.logger, async_db=async_db,
                                                           callFrom="get_cached_profiles_route api"))
            newProfilesCached = future.result()
            cached_profile_ids = get_cached_profiles(redisClient=redisClient, cacheFilterName=cache_filter_name)
        # responseData = [id.replace("Profiles:","") for id in cached_profile_ids]
        current_app.logger.info(f"{len(cached_profile_ids)} Profile Ids were fetched from cache")
        return json.dumps(cached_profile_ids)
    except Exception as e:
        current_app.logger.error(f"Failed to get the cached user ids from gateway")
        current_app.logger.exception(e)
        return json.dumps({'status':False})


# Profiles already seen by current_user -> list of profile ids
@current_app.route('/getprofilesalreadyseen', methods=['POST'])
def get_profiles_already_seen_by_user_route():
    try:
        current_user_id = request.get_json().get('currentUserId')
        future = run_coroutine(get_profiles_already_seen_by_user(current_user_id=current_user_id,
                                                                 redis_client=redisClient))
        ids_already_seen_by_user = future.result()
        ids_already_seen_by_user = chain(*ids_already_seen_by_user)
        response_data = [profile_id.split(':')[0] for profile_id in ids_already_seen_by_user]
        current_app.logger.info(f"{len(response_data)} Already seen profiles Ids were fetched from cache")
        return json.dumps(response_data)
    except Exception as e:
        current_app.logger.error(f"Failed to get the already seen cached profiles ids from gateway")
        current_app.logger.exception(e)
        return json.dumps({'status': False})

@current_app.route('/getprofilerecommendations', methods=['POST'])
def get_recommendations_for_user():
    try:
        current_user_id = request.get_json().get('currentUserId')
        GeoService_get_recommended_profiles_for_user(profileId=None, 
                                redis_client=None)
    except Exception as e:
        current_app.logger.error(f"{current_user_id}: Failed to get recommendation")
        current_app.logger.exception(e)
        return json.dumps({'status': False})


