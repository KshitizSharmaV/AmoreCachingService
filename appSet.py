from tempfile import TemporaryFile
import flask
from flask import Blueprint, current_app, jsonify, request
import json

from ProjectConf.AsyncioPlugin import run_coroutine
from ProjectConf.ReddisConf import redisClient
from ProjectConf.FirestoreConf import async_db, db
from Gateways.GradingScoresGateway import store_graded_profile_in_firestore_route
from Gateways.LikesDislikesGateway import LikesDislikes_async_store_likes_dislikes_superlikes_for_user
from Gateways.MatchUnmatchGateway import MatchUnmatch_unmatch_two_users
from Gateways.RewindGateway import Rewind_task_function
from Gateways.ReportProfile import Report_profile_task
from Gateways.GeoserviceGateway import GeoService_store_profiles
from Gateways.MessagesGateway import match_two_profiles_for_direct_message
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
        - swipe info: Like, Dislike, Superlikes
        - swiped profile id
        """
        currentUserId = request.get_json().get('currentUserId')
        swipeInfo = request.get_json().get('swipeInfo')
        swipedUserId = request.get_json().get('swipedUserId')
        future = run_coroutine(LikesDislikes_async_store_likes_dislikes_superlikes_for_user(currentUserId=currentUserId,
                                                                                            swipedUserId=swipedUserId,
                                                                                            swipeStatusBetweenUsers=swipeInfo,
                                                                                            async_db=async_db,
                                                                                            redisClient=redisClient,
                                                                                            logger=current_app.logger))
        future.result()
        current_app.logger.info(f"Storing {currentUserId} {swipeInfo} on {swipedUserId}")
        return jsonify({'status': 200})
    except Exception as e:
        current_app.logger.exception(
            f"Unable to store likes dislikes super likes {currentUserId}:{swipedUserId}:{swipeInfo} ")
        current_app.logger.exception(e)
        return False


@current_app.route('/unmatchgate', methods=['POST'])
def unmatch():
    try:
        current_user_id = request.get_json().get('current_user_id')
        other_user_id = request.get_json().get('other_user_id')
        future = run_coroutine(MatchUnmatch_unmatch_two_users(current_user_id=current_user_id, 
                                                        other_user_id=other_user_id,
                                                     redisClient=redisClient,
                                                     logger=current_app.logger))
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
        swipeStatusBetweenUsers = request.get_json().get('swipeInfo')
        swiped_user_id = request.get_json().get('swipedUserID')
        if current_user_id and swipeStatusBetweenUsers and swiped_user_id:
            future = run_coroutine(Rewind_task_function(current_user_id=current_user_id, 
                                                        swiped_user_id=swiped_user_id,
                                                        swipeStatusBetweenUsers=swipeStatusBetweenUsers,
                                                        redisClient=redisClient, 
                                                        logger=current_app.logger))
            future.result()
            current_app.logger.info(f"Successfully rewinded {swipeStatusBetweenUsers} by {current_user_id}")
        else:
            current_app.logger.warning(f"None received {current_user_id} {swipeStatusBetweenUsers} {swiped_user_id}")
        return jsonify({'status': 200})
    except Exception as e:
        current_app.logger.exception(f"Unable to rewind {swipeStatusBetweenUsers} by {current_user_id}")
        current_app.logger.exception(e)


@current_app.route('/storeProfileInBackendGate', methods=['POST'])
def store_profile():
    """
    Stores Profile in Cache.
    Request Parameters:
        - profile: Dict/JSON containing Profile information of the currently logged-in user.
    Returns: Status Message for Amore Flask.
    """
    try:
        profile = request.get_json().get('profile')
        # Update the cache with profile data?
        future = run_coroutine(GeoService_store_profiles(profile=profile,
                                                         redisClient=redisClient,
                                                         logger=current_app.logger))
        result = future.result()
        current_app.logger.info(f"{profile['id']}: Successfully stored profile in Cache/DB")
        response = jsonify({'message': f"{profile['id']}: Successfully stored profile in Cache/DB"})
        response.status_code = 200
        return response
    except Exception as e:
        current_app.logger.exception(f"{profile['id']}: Unable to stored profile in Cache/DB")
        current_app.logger.exception(e)
        response = jsonify({'message': 'An error occured in API /storeProfileInBackendGate'})
        response.status_code = 400
        return response


@current_app.route('/reportprofilegate', methods=['POST'])
def report_profile():
    """
    Report Profile API:
        - Report Profile Task: View Function Docstring for explanation
        - Unmatch Task: View Function Docstring for explanation
    Returns: Status Message for Amore Flask.
    """
    current_user_id, reported_profile_id = None, None
    try:
        current_user_id = request.get_json().get('current_user_id')
        reported_profile_id = request.get_json().get('other_user_id')
        reason_given = request.get_json().get('reasonGiven')
        description_given = request.get_json().get('descriptionGiven')
        status = Report_profile_task(current_user_id=current_user_id, reported_profile_id=reported_profile_id,
                                     reason_given=reason_given, description_given=description_given,
                                     redisClient=redisClient)
        future = run_coroutine(MatchUnmatch_unmatch_two_users(current_user_id=current_user_id, 
                                                    other_user_id=reported_profile_id,
                                                     redisClient=redisClient,
                                                     logger=current_app.logger))
        future.result()
        current_app.logger.info(f"Successfully reported profile {reported_profile_id}")
        return jsonify({'status': 200})
    except Exception as e:
        current_app.logger.exception(f"Unable to report profile {reported_profile_id}")
        current_app.logger.exception(e)


@current_app.route('/matchondirectmessageGate', methods=['POST'])
def match_profiles_on_direct_message():
    """
    Report Profile API:
        - Report Profile Task: View Function Docstring for explanation
        - Unmatch Task: View Function Docstring for explanation
    Returns: Status Message for Amore Flask.
    """
    current_user_id, other_user_id = None, None
    try:
        current_user_id = request.get_json().get('currentUserId')
        other_user_id = request.get_json().get('otherUserId')
        future = run_coroutine(
            match_two_profiles_for_direct_message(current_user_id=current_user_id, other_user_id=other_user_id,
                                                  async_db=async_db, logger=logger, redis_client=redisClient))
        _ = future.result()
        current_app.logger.info(f"Successfully matched profile {current_user_id} and {other_user_id}")
        return jsonify({'status': 200})
    except Exception as e:
        current_app.logger.exception(f"Unable to match profiles {current_user_id} and {other_user_id}")
        current_app.logger.exception(e)
