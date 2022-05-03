import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from logging.handlers import TimedRotatingFileHandler
import pandas as pd
from datetime import datetime
import traceback
import time
import logging
import asyncio
from google.cloud import firestore
from ProjectConf.FirestoreConf import db, async_db # Firestore
from ProjectConf.ReddisConf import redisClient
from Gateways.LikesDislikesGateway import async_get_likes_dislikes_match_unmatch_for_user_from_firebase
from Gateways.ProfilesGateway import get_cached_profile_ids
from ProjectConf.AsyncioPlugin import run_coroutine
import json

# Log Settings
LOG_FILENAME = datetime.now().strftime("%H_%M_%d_%m_%Y")+".log"
if not os.path.exists('Logs/LikesDislikesCachingService/'):
    os.makedirs('Logs/LikesDislikesCachingService/')
logHandler = TimedRotatingFileHandler(f'Logs/LikesDislikesCachingService/{LOG_FILENAME}',when="midnight")
logFormatter = logging.Formatter(f'%(asctime)s %(levelname)s %(threadName)s : %(message)s')
logHandler.setFormatter( logFormatter )
logger = logging.getLogger(f'Logs/LikesDislikesCachingService/{LOG_FILENAME}')
logger.addHandler( logHandler )
logger.setLevel( logging.INFO )


async def main():
    try:
        # Get all the active user ids from profile gateway in cache
        # Load the LikesDilikes for all users
        cachedLikesDislikes =  get_cached_profile_ids(redisClient=redisClient,
                                                    cacheFilterName="LikesDislikes")
        logger.info(f"There are {len(cachedLikesDislikes)} LikesDislikes profile in the cache")
        cachedProfileIds =  get_cached_profile_ids(redisClient=redisClient, cacheFilterName="Profiles")
        cachedProfileIds = [id.replace("Profiles:","") for id in cachedProfileIds]
        logger.info(f"There are {len(cachedProfileIds)} profiles in cache.")
        for collectionNameChild in ["Received","Given","Match","UnMatch"]:
            _ =  await asyncio.gather(*[async_get_likes_dislikes_match_unmatch_for_user_from_firebase(userId=profileId, 
                                                                    collectionNameChild=collectionNameChild, 
                                                                    async_db=async_db, 
                                                                    redisClient=redisClient, logger=logger) for profileId in cachedProfileIds])
        logger.info("All LikesDislikes was successfully stored in cache from firestore")
        return True
    except Exception as e:
        logger.error(f"Failed to kick start LikesdislikesCachingService")
        logger.exception(e)
        return 
    

# Argument Passing For How Often should the file run? Per Minute
if __name__ == '__main__':
    asyncio.run((main()))