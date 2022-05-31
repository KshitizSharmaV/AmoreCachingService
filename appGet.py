import flask
from flask import Blueprint, current_app, jsonify, request
import json
from itertools import chain
from ProjectConf.AsyncioPlugin import run_coroutine
from ProjectConf.ReddisConf import redisClient
from ProjectConf.FirestoreConf import async_db, db
from Gateways.ProfilesGateway import *
from Gateways.GeoserviceGateway import GeoService_get_recommended_profiles_for_user, GeoService_get_fitered_profiles_on_params, Geoservice_get_profile_Ids_from_redis_key
from Gateways.LikesDislikesGateway import *

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
        allProfilesData = run_coroutine(get_profile_by_ids(redisClient=redisClient, profileIdList=profileIdList,
                                                           logger=current_app.logger, async_db=async_db))
        allProfilesData = allProfilesData.result()
        return json.dumps(allProfilesData, indent=4, sort_keys=True, default=str)
    except Exception as e:
        current_app.logger.error(f"Failed to fetch profiles from gateway")
        current_app.logger.exception(e)
        flask.abort(401, f'Unable to get profiles by ids :{profileIdList}')


# Get the profiles ids which are store in cache.
# Assumption: All the active profiles in firestore are in Redis cache to. - Run the ProfilesCachingService to refersh all profiles automatically
@current_app.route('/getcachedprofileids', methods=['GET'])
def get_cached_profile_ids_route():
    try:
        # Get the cacheFilterName
        cacheFilterName = request.get_json().get('cacheFilterName')
        cachedProfileRedisIds = GeoService_get_fitered_profiles_on_params(redisClient=redisClient, logger=current_app.logger)
        responseData = Geoservice_get_profile_Ids_from_redis_key(redisKeys=cachedProfileRedisIds)
        current_app.logger.info(f"{responseData}")
        current_app.logger.info(f"{len(responseData)} Profile Ids were fetched from cache")
        return json.dumps(responseData)
    except Exception as e:
        current_app.logger.error(f"Failed to get the cached user ids from gateway")
        current_app.logger.exception(e)
        return json.dumps({'status': False})


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


@current_app.route('/fetchGeoRecommendationsGate', methods=['POST'])
def fetch_geo_recommendations():
    try:
        userId = request.get_json().get('userId')
        profilesCountLeftInDeck = request.get_json().get('CountLeftInDeck')
        filterData = request.get_json().get('filterData')
        profilesList = GeoService_get_recommended_profiles_for_user(userId=userId,
                                                                        filterData=filterData,
                                                                        redisClient=redisClient,
                                                                        logger=current_app.logger)
        profilesList = profilesList[1] if len(profilesList) > 0 else profilesList
        profiles_array = list(map(redisClient.mget, profilesList))
        profiles_array = [json.loads(profile_string[0]) for profile_string in profiles_array]
        current_app.logger.info(f"{userId}: Successfully fetched {len(profilesList)} recommendations")
        response = jsonify({'message': f"{userId}: Successfully fetched recommendations"})
        response.status_code = 200
        return jsonify(profiles_array)
    except Exception as e:
        current_app.logger.exception(f"{userId}: Unable to fetch recommendations")
        current_app.logger.exception(e)
        response = jsonify({'message': 'Unable to fetch recommendations /fetchGeoRecommendationsGate'})
        response.status_code = 400
        return response


# Profiles already seen by current_user -> list of profile ids
@current_app.route('/getlikesdislikesforuser', methods=['GET'])
def get_likes_dislikes_for_user_route():
    """
    Returns list of Profile IDs for the given type of Swipe (Like Given, Dislike Given, Like Received, etc.)
    """
    try:
        currentUserId = request.get_json().get('currentUserId')
        collectionNameChild = request.get_json().get('collectionNameChild')
        matchFor = request.get_json().get('matchFor')
        ids_list = get_swipe_infos_for_user_from_firebase(userId=currentUserId,
                                                                     collectionNameChild=collectionNameChild,
                                                                     matchFor=matchFor, db=db, redisClient=redisClient,
                                                                     logger=current_app.logger)
        profiles_array_future = run_coroutine(get_profile_by_ids(redisClient=redisClient, profileIdList=ids_list,
                                                                 logger=current_app.logger, async_db=async_db))
        profiles_array_future = profiles_array_future.result()
        current_app.logger.info(f"Fetched for {currentUserId} {collectionNameChild} {matchFor}: {len(profiles_array_future)}")
        # current_app.logger.info(json.dumps(profiles_array_future, indent=4, sort_keys=True, default=str))
        return json.dumps(profiles_array_future, indent=4, sort_keys=True, default=str)
    except Exception as e:
        current_app.logger.error(f"Failed to get the Likes Dislikes for user from gateway")
        current_app.logger.exception(e)
        return flask.abort(401, f'Unable to get likes dislikes for users {currentUserId} {collectionNameChild} {matchFor}')
