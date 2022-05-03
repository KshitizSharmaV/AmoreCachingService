import flask
from flask import Blueprint, current_app, jsonify, request
import json

from ProjectConf.AsyncioPlugin import run_coroutine
from ProjectConf.ReddisConf import redisClient
from ProjectConf.FirestoreConf import async_db, db
from Gateways.GradingScoresGateway import store_graded_profile_in_firestore_route
from Gateways.LikesDislikesGateway import async_store_likes_dislikes_superlikes_for_user
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
        future = run_coroutine(store_graded_profile_in_firestore_route(normalizedAllProfileScoresDf=normalizedAllProfileScoresDf,
                                                                        redisClient=redisClient, 
                                                                        logger=logger, 
                                                                        async_db=async_db))
        newProfilesCached = future.result()
        return json.dumps({"status":True})
    except Exception as e:
        logger.error(f"Failed to write grading scores to firestore or cache")
        logger.exception(e)
        return json.dumps({"status":False})

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
        future = run_coroutine(async_store_likes_dislikes_superlikes_for_user(currentUserId=currentUserId, 
                                        swipedUserId=swipedUserId, 
                                        swipeInfo=swipeInfo, 
                                        async_db=async_db))
        future.result()
        logger.info(f"Successfully stored LikesDislikes:{currentUserId}:{swipedUserId}:{swipeInfo}")
        return jsonify({'status': 200})
    except Exception as e:
        logger.exception(f"Unable to store likes dislikes super likes {currentUserId}:{swipedUserId}:{swipeInfo} ")
        logger.exception(e)
