import flask
from flask import Blueprint, current_app, jsonify, request
import json

from ProjectConf.AsyncioPlugin import run_coroutine
from ProjectConf.ReddisConf import redisClient
from ProjectConf.FirestoreConf import async_db, db
from Helpers.CommonHelper import load_profiles_to_cache_from_firebase, get_profiles_not_in_cache, get_cached_profile_ids, fresh_load_balances
import logging

app_get = Blueprint('appGet', __name__)
logger = logging.getLogger()

# Get Profiles using their IDs
@current_app.route('/getprofilesbyids', methods=['GET'])
def get_profiles_by_ids():
    # Get the list of profile ids from the body
    profileIdList = request.get_json().get('profileIdList')
    # Find those Profiles in the local cache
    profileIdCachedKeys = [f"Profiles:{id}" for id in profileIdList]
    cursor = redisClient.mget(profileIdCachedKeys)
    # Iterate over the cached profiles cursor
    responseData = [json.loads(profile) for profile in cursor if profile]
    # Check if profile is missing from the response data, means profile not in cache
    logger.info(f"{len(responseData)} Profiles were fetched from cache")
    if len(profileIdCachedKeys) != len(responseData) :
        # Oh oh - Looks like profile is missing from cache. 
        profileIdsNotInCache = get_profiles_not_in_cache(profileIdList=profileIdList,redisClient=redisClient)
        future = run_coroutine(load_profiles_to_cache_from_firebase(profileIdsNotInCache=profileIdsNotInCache,redisClient=redisClient, logger=logger, async_db=async_db))
        newProfilesCached = future.result()
        responseData.extend(newProfilesCached)
    return json.dumps(responseData, indent=4, sort_keys=True, default=str)


# Get All the profile IDs
@current_app.route('/getcachedprofileids', methods=['GET'])
def get_cached_profile_ids_route():
    cachedProfileIds = get_cached_profile_ids(redisClient=redisClient)
    if len(cachedProfileIds) == 0:
        future = run_coroutine(fresh_load_balances(redisClient=redisClient, logger=logger,async_db=async_db, callFrom="get_cached_profile_ids_route api"))
        newProfilesCached = future.result()
        return 
    responseData = [id.replace("Profiles:","") for id in cachedProfileIds]
    logger.info(f"{len(responseData)} Profile Ids were fetched from cache")
    return json.dumps(responseData)



