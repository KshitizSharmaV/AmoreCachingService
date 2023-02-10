import flask
from flask import Blueprint, jsonify, request
import json
from ProjectConf.AsyncioPlugin import run_coroutine
from ProjectConf.RedisConf import try_creating_profile_index_for_redis, check_redis_index_exists
from Gateways.LikesDislikesGateway import LikesDislikes_fetch_userdata_from_firebase_or_redis, LikesDislikes_get_profiles_already_seen_by_id
from Gateways.ProfilesGateway import ProfilesGateway_get_profile_by_ids
from Gateways.MatchUnmatchGateway import MatchUnmatch_fetch_userdata_from_firebase_or_redis, MatchUnmatch_get_match_unmatch_nomatch_for_user
from Gateways.RecommendationEngine.BuildRecommendations import RecommendationSystem
from Utilities.LogSetup import configure_logger

logger = configure_logger(__name__)
app_get = Blueprint('appGet', __name__)

# Get Profiles using their IDs
@app_get.route('/getprofilesbyids', methods=['GET'])
def get_profiles_by_ids():
    try:
        # Get the list of profile ids from the body
        profileIdList = request.get_json().get('profileIdList')
        allProfilesData = run_coroutine(ProfilesGateway_get_profile_by_ids(profileIdList=profileIdList))
        allProfilesData = allProfilesData.result()
        return json.dumps(allProfilesData, indent=4, sort_keys=True, default=str)
    except Exception as e:
        logger.error(f"Failed to fetch profiles from gateway")
        logger.exception(e)
        flask.abort(401, f'Unable to get profiles by ids :{profileIdList}')


@app_get.route('/fetchGeoRecommendationsGate', methods=['POST'])
def fetch_geo_recommendations():
    """
    Fetch recommendations based on filters and location

    Request Parameters:
        - profilesCountLeftInDeck: Cards left in deck (Unused)
        - filterData: Filters defined by user including geohashes
    :return: List of recommended profiles(Dicts/JSONs)
    """
    try:
        if not check_redis_index_exists(index="idx:profile"):
            try_creating_profile_index_for_redis()
        userId = request.get_json().get('userId')
        profilesAlreadyInDeck = request.get_json().get('profilesAlreadyInDeck')
        filterData = request.get_json().get('filterData')
        logger.warning(f"profilesAlreadyInDeck: {profilesAlreadyInDeck}")
        recommendation_system = RecommendationSystem(current_user_id=userId, 
                                                    current_user_filters=filterData,
                                                    profiles_already_in_deck=profilesAlreadyInDeck)
        profiles_array = recommendation_system.build_recommendations()
        # Check if there are profiles in the array
        if len(profiles_array) > 0:
            logger.info(f"{userId}: Successfully fetched {len(profiles_array)} recommendations")
        else:
            logger.warning(f"{userId}: No profile fetched for user")

        if type(profiles_array) != list:
            logger.error(f"Profiles array for recommendation not of List type: {type(profiles_array)}: {profiles_array}")
        return jsonify(profiles_array)
    except Exception as e:
        logger.exception(f"{userId}: Unable to fetch recommendations")
        logger.exception(e)
        response = jsonify({'message': 'Unable to fetch recommendations /fetchGeoRecommendationsGate'})
        response.status_code = 400
        return response


# Get LikesDislikes for Super Likes, Received view
@app_get.route('/getlikesdislikesforuser', methods=['GET'])
def get_likes_dislikes_for_user_route():
    """
    Returns list of Profile IDs for the given type of CollectionName(Given, Received)
    & Swipe (Like Given, Dislike Given, Like Received, etc.)
    """
    try:
        currentUserId = request.get_json().get('currentUserId')
        childCollectionName = request.get_json().get('childCollectionName')
        matchFor = request.get_json().get('matchFor')
        noOfLastRecords = request.get_json().get('noOfLastRecords')
        logger.warning(f"Request to fetch last {noOfLastRecords} likes dislikes")
        # Get profile ids for given filter in likesdislikes
        ids_list = run_coroutine(LikesDislikes_fetch_userdata_from_firebase_or_redis(userId=currentUserId,
                                                                    childCollectionName=childCollectionName,
                                                                    swipeStatusBetweenUsers=matchFor,
                                                                    no_of_last_records=noOfLastRecords))
        ids_list = ids_list.result()

        if childCollectionName == "Received":
            # Don't show the profiles that user has already swiped from their received list.
            swipe_received_profiles_already_swiped = \
                run_coroutine(MatchUnmatch_get_match_unmatch_nomatch_for_user(userId=currentUserId))
            swipe_received_profiles_already_swiped = swipe_received_profiles_already_swiped.result()
            ids_list = list(set(ids_list).difference(*swipe_received_profiles_already_swiped))

        # Get profile data for ids                                    
        profiles_array_future = run_coroutine(ProfilesGateway_get_profile_by_ids(profileIdList=ids_list))
        profiles_array_future = profiles_array_future.result()
        logger.info(f"Fetched for {currentUserId} {childCollectionName} {matchFor}: {len(profiles_array_future)}")
        return json.dumps(profiles_array_future, indent=4, sort_keys=True, default=str)
    except Exception as e:
        logger.error(f"Failed to get the Likes Dislikes for user from gateway")
        logger.exception(e)
        return flask.abort(401, f'Unable to get likes dislikes for users {currentUserId} {childCollectionName} {matchFor}')


# Profiles already seen by current_user -> list of profile ids
@app_get.route('/getprofilesalreadyseen', methods=['GET'])
def get_profiles_already_seen_by_user_route():
    '''
    Get profiles already seen by user
    '''
    try:
        userId = request.get_json().get('currentUserId')
        idsAlreadySeenByUser = run_coroutine(LikesDislikes_get_profiles_already_seen_by_id(userId=userId, childCollectionName="Given")) 
        idsAlreadySeenByUser = idsAlreadySeenByUser.result()                                                    
        logger.info(f"{len(idsAlreadySeenByUser)} Already seen profiles Ids were fetched from cache")
        return json.dumps(idsAlreadySeenByUser)
    except Exception as e:
        logger.error(f"Failed to get the already seen cached profiles ids from gateway")
        logger.exception(e)
        return flask.abort(401, f'Unable to get profiles already seen by the user')

@app_get.route('/loadmatchesunmatchesgate', methods=['POST'])
def load_match_unmatch_profiles():
    """
    Store match unmatch profiles for user in redi
    : param userId: user id you want to save match unmatches in redis
    : param fromCollection: Match or Unmatch
    """
    try:
        userId = request.get_json().get('userId')
        # fromCollection always receives Match from API, though we load both Match and Unmatch profiles incache
        fromCollection = request.get_json().get('fromCollection')
        
        ids_list = run_coroutine(MatchUnmatch_fetch_userdata_from_firebase_or_redis(userId=userId, 
                                                                                childCollectionName=fromCollection))
        ids_list = ids_list.result()         
        if len(ids_list) > 0:
            # Get profile data for ids                                    
            profiles_array_future = run_coroutine(ProfilesGateway_get_profile_by_ids(profileIdList=ids_list))
            profiles_array_future = profiles_array_future.result()
            logger.info(f"MatchUnmatch:{userId}:{fromCollection} fetched {len(profiles_array_future)} profiles")
        else:
            profiles_array_future = []
            logger.warning(f"MatchUnmatch:{userId}:{fromCollection} no profiles to be fetched")
        return json.dumps(profiles_array_future, indent=4, sort_keys=True, default=str)
    except Exception as e:
        logger.exception(f"{userId} unable to load {fromCollection} for user")
        logger.exception(e)
        return flask.abort(401, f'{userId} unable to load {fromCollection} for user')
