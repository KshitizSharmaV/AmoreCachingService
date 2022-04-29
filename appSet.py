import flask
from flask import Blueprint, current_app, jsonify, request
import json

from ProjectConf.AsyncioPlugin import run_coroutine
from ProjectConf.ReddisConf import redisClient
from ProjectConf.FirestoreConf import async_db, db
from Helpers.CommonHelper import get_cached_profile_ids, fresh_load_balances
import logging

app_set = Blueprint('appSet', __name__)
logger = logging.getLogger()

@current_app.route('/storeprofilegradingscore', methods=['GET'])
def store_profile_grading_score():
    cachedProfileIds = get_cached_profile_ids(redisClient=redisClient)
    if len(cachedProfileIds) == 0:
        future = run_coroutine(fresh_load_balances(redisClient=redisClient, logger=logger,async_db=async_db, callFrom="get_cached_profile_ids_route api"))
        newProfilesCached = future.result()
        return 
    responseData = [id.replace("Profiles:","") for id in cachedProfileIds]
    logger.info(f"{len(responseData)} Profile Ids were fetched from cache")
    return json.dumps(responseData)
