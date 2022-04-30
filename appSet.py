import flask
from flask import Blueprint, current_app, jsonify, request
import json

from ProjectConf.AsyncioPlugin import run_coroutine
from ProjectConf.ReddisConf import redisClient
from ProjectConf.FirestoreConf import async_db, db
from Gateways.GradingScoresGateway import store_graded_profile_in_firestore_route
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