import flask
from flask import Blueprint, current_app, jsonify, request
import json

from ProjectConf.AsyncioPlugin import run_coroutine
from ProjectConf.ReddisConf import redisClient
from ProjectConf.FirestoreConf import async_db, db
from Gateways.GradingScoresGateway import store_graded_profile_in_firestore_route
from Gateways.LikesDislikesGateway import async_store_likes_dislikes_superlikes_for_user
from Gateways.UnmatchRewindGateway import rewind_task_function, unmatch_task_function
from Gateways.GeoserviceGateway import GeoService_store_profiles
import logging
import asyncio
import traceback
import pandas as pd

app_set = Blueprint('appSet', __name__)
logger = logging.getLogger()


@current_app.route('/storeprofilegradingscore', methods=['POST'])
def store_profile_grading_score():
    try:
        # Get the json object of the graded profiles
        normalizedAllProfileScoresDf = request.get_json().get('normalizedAllProfileScoresDf')
        normalizedAllProfileScoresDf = pd.DataFrame(normalizedAllProfileScoresDf)
        logger.info("Received new grading scores to be stored to firestore and cache")
        logger.info(normalizedAllProfileScoresDf)
        future = run_coroutine(
            store_graded_profile_in_firestore_route(normalizedAllProfileScoresDf=normalizedAllProfileScoresDf,
                                                    redisClient=redisClient,
                                                    logger=current_app.logger,
                                                    async_db=async_db))
        newProfilesCached = future.result()
        current_app.logger.info(f"Successfully wrote grading scores to firestore/cache")
        return json.dumps({"status": True})
    except Exception as e:
        current_app.logger.error(f"Failed to write grading scores to firestore or cache")
        current_app.logger.exception(e)
        return json.dumps({"status": False})


# store_likes_dislikes_superlikes store likes, dislikes and superlikes in own user id and other profile being acted on
@current_app.route('/storelikesdislikesGate', methods=['POST'])
def store_likes_dislikes_superlikes():
    """
    Endpoint to store likes, superlikes, dislikes, liked_by, disliked_by, superliked_by for users
    """
    try:
        """
        Body of Request contains following payloads:
        - current user id
        - swipe info: Like, Dislike, Superlike
        - swiped profile id
        """
        currentUserId = request.get_json().get('currentUserId')
        swipeInfo = request.get_json().get('swipeInfo')
        swipedUserId = request.get_json().get('swipedUserId')
        future = run_coroutine(
            async_store_likes_dislikes_superlikes_for_user(currentUserId=currentUserId, swipedUserId=swipedUserId,
                                                           swipeInfo=swipeInfo, async_db=async_db,
                                                           redis_client=redisClient))
        future.result()
        current_app.logger.info(f"Successfully stored LikesDislikes:{currentUserId}:{swipedUserId}:{swipeInfo}")
        return jsonify({'status': 200})
    except Exception as e:
        current_app.logger.exception(f"Unable to store likes dislikes super likes {currentUserId}:{swipedUserId}:{swipeInfo} ")
        current_app.logger.exception(e)


@current_app.route('/unmatchgate', methods=['POST'])
def unmatch():
    try:
        current_user_id = request.get_json().get('current_user_id')
        other_user_id = request.get_json().get('other_user_id')
        future = run_coroutine(unmatch_task_function(current_user_id=current_user_id, other_user_id=other_user_id,
                                                     redis_client=redisClient))
        future.result()
        current_app.logger.info(f"Successfully Unmatched {current_user_id} and {other_user_id}")
        return jsonify({'status': 200})
    except Exception as e:
        current_app.logger.exception(f"Unable to unmatch {current_user_id} and {other_user_id}")
        current_app.logger.exception(e)


@current_app.route('/rewindsingleswipegate', methods=['POST'])
def rewind_single_swipe():
    try:
        current_user_id = request.get_json().get('currentUserID')
        swipe_info = request.get_json().get('swipeInfo')
        swiped_user_id = request.get_json().get('swipedUserID')
        future = run_coroutine(rewind_task_function(current_user_id=current_user_id, swiped_user_id=swiped_user_id,
                                                    redis_client=redisClient, logger=current_app.logger))
        future.result()
        current_app.logger.info(f"Successfully rewinded {swipe_info} by {current_user_id}")
        return jsonify({'status': 200})
    except Exception as e:
        current_app.logger.exception(f"Unable to rewind {swipe_info} by {current_user_id}")
        current_app.logger.exception(e)


@current_app.route('/storeProfileInBackendGate', methods=['POST'])
def store_profile():
    try:
        profile = request.get_json().get('profile')
        # Update the cache with profile data?
        future = run_coroutine(GeoService_store_profiles(profile=profile,
                                                        redisClient=redisClient, 
                                                        logger=current_app.logger))
        result = future.result()
        current_app.logger.info(f"{profile['id']}: Successfully stored profile in Cache/DB")
        response = jsonify({'message':f"{profile['id']}: Successfully stored profile in Cache/DB"})
        response.status_code = 200
        return response
    except Exception as e:
        current_app.logger.exception(f"{profile['id']}: Unable to stored profile in Cache/DB")
        current_app.logger.exception(e)
        response = jsonify({'message': 'An error occured in API /storeProfileInBackendGate'})
        response.status_code = 400
        return response