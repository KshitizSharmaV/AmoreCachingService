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

from ProjectConf.MongoDBConf import mongoClient, amoreCacheDB # MongoDB
from ProjectConf.FirestoreConf import async_db, db
from ProjectConf.AsyncioPlugin import run_coroutine
from Helpers.CommonHelper import write_to_cache_after_read

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
    cursor = amoreCacheDB["Profiles"].find({"_id":{"$in" : profileIdList}})
    # Iterate over the mongo cursor
    responseData = [json.dumps(doc, default=json_util.default) for doc in cursor]
    
    # Check if profile is missing from the response data, means profile not in cache
    if len(profileIdList) != len(responseData) :
        # Oh oh - Looks like profile is missing from cache. 
        profilesNotInCache = get_profiles_not_in_cache(profileIdList=profileIdList)
        future = run_coroutine(load_profiles_to_mongo_from_firebase(profilesNotInCache=profilesNotInCache))
        newProfilesCached = future.result()
        responseData.extend(newProfilesCached)
    
    return json.dumps(responseData, indent=4, sort_keys=True, default=str)

def get_profiles_not_in_cache(profileIdList=None):
    allCachedProfileIds = get_all_profile_ids()
    return list(set(profileIdList)-set(allCachedProfileIds))

async def load_profiles_to_mongo_from_firebase(profilesNotInCache=None):
    logger.warning(f'{len(profilesNotInCache)} profiles were not found in cache')
    newProfilesCached =  await asyncio.gather(*[write_to_cache_after_read(profileId=profileId,
                                                                    amoreCacheDB=amoreCacheDB,
                                                                    logger=logger,
                                                                    async_db=async_db) for profileId in profilesNotInCache])
    newProfilesCached = [profile for profile in newProfilesCached if profile is not None]
    return newProfilesCached

# Get All the profile IDs
@app.route('/getallprofileids', methods=['GET'])
def get_all_profile_ids_route():
    responseData = get_all_profile_ids()
    return json.dumps(responseData)

def get_all_profile_ids():
    return [str(id) for id in amoreCacheDB["Profiles"].find().distinct('_id')]


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8800, debug=True)
