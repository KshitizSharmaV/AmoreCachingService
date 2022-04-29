from genericpath import exists
import flask
from flask import Flask, jsonify, request
import traceback
import time
from datetime import datetime
import logging
import os
from logging.handlers import TimedRotatingFileHandler
import json
from bson import json_util
import asyncio

from ProjectConf.ReddisConf import redisClient
from ProjectConf.FirestoreConf import async_db, db
from ProjectConf.AsyncioPlugin import run_coroutine
from Helpers.CommonHelper import write_profiles_to_cache_after_read

app = Flask(__name__)

# Log Settings
LOG_FILENAME = datetime.now().strftime("%H_%M_%d_%m_%Y")+".log"
if not os.path.exists('Logs/AppLogs/'):
    os.makedirs('Logs/AppLogs/')
logHandler = TimedRotatingFileHandler(f'Logs/AppLogs/{LOG_FILENAME}',when="midnight")
logFormatter = logging.Formatter(f'%(asctime)s %(levelname)s %(threadName)s : %(message)s')
logHandler.setFormatter( logFormatter )
logger = logging.getLogger(f'Logs/AppLogs/{LOG_FILENAME}')
logger.addHandler( logHandler )
logger.setLevel( logging.INFO )

# Get Profiles using their IDs
@app.route('/getprofilesbyids', methods=['GET'])
def get_profiles_by_ids():
    # Get the list of profile ids from the body
    profileIdList = request.get_json().get('profileIdList')
    # Find those Profiles in the local cache
    profileIdCachedKeys = [f"Profiles:{id}" for id in profileIdList]
    cursor = redisClient.mget(profileIdCachedKeys)
    # Iterate over the cached profiles cursor
    responseData = [json.loads(profile) for profile in cursor if profile]
    # Check if profile is missing from the response data, means profile not in cache
    logger.info(f"{len(responseData)} profiles were fetched from cache")
    if len(profileIdCachedKeys) != len(responseData) :
        # Oh oh - Looks like profile is missing from cache. 
        profilesNotInCache = get_profiles_not_in_cache(profileIdList=profileIdList)
        future = run_coroutine(load_profiles_to_cache_from_firebase(profilesNotInCache=profilesNotInCache))
        newProfilesCached = future.result()
        responseData.extend(newProfilesCached)
    return json.dumps(responseData, indent=4, sort_keys=True, default=str)

def get_profiles_not_in_cache(profileIdList=None):
    allCachedProfileIds = get_cached_profile_ids()
    allCachedProfileIds = [id.replace("Profiles:","") for id in allCachedProfileIds]
    return list(set(profileIdList)-set(allCachedProfileIds))

async def load_profiles_to_cache_from_firebase(profilesNotInCache=None):
    logger.warning(f'{len(profilesNotInCache)} profiles not found in cache')
    newProfilesCached =  await asyncio.gather(*[write_profiles_to_cache_after_read(profileId=profileId,redisClient=redisClient,
                                                                    logger=logger, async_db=async_db) for profileId in profilesNotInCache])
    newProfilesCached = [profile for profile in newProfilesCached if profile is not None]
    return newProfilesCached

# Get All the profile IDs
@app.route('/getcachedprofileids', methods=['GET'])
def get_cached_profile_ids_route():
    cachedProfileIds = get_cached_profile_ids()
    responseData = [id.replace("Profiles:","") for id in cachedProfileIds]
    return json.dumps(responseData)

def get_cached_profile_ids():
    # dataCursor, profileIdsInCache = redisClient.scan(match='Profiles:*')
    profileIdsInCache = redisClient.keys()
    return profileIdsInCache

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8800, debug=True)






