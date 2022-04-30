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

app_set = Blueprint('appSet', __name__)
logger = logging.getLogger()

@current_app.route('/storeprofilegradingscore', methods=['GET'])
def store_profile_grading_score():
    try:
        normalizedAllProfileScoresDf = None
        future = run_coroutine(store_graded_profile_in_firestore_route(normalizedAllProfileScoresDf=normalizedAllProfileScoresDf,redisClient=redisClient, logger=logger, async_db=async_db))
        newProfilesCached = future.result()
        return True
    except Exception as e:
        logger.error(f"Failed to write grading scores to firestore or cache")
        logger.error(traceback.format_exc())
        logger.exception(traceback.format_exc())
        return False