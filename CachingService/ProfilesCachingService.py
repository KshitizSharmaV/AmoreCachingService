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
from Helpers.CommonHelper import write_to_cache
import json

# Log Settings
LOG_FILENAME = datetime.now().strftime("%H_%M_%d_%m_%Y")+".log"
if not os.path.exists('Logs/AmoreCachingService/'):
    os.makedirs('Logs/AmoreCachingService/')
logHandler = TimedRotatingFileHandler(f'Logs/AmoreCachingService/{LOG_FILENAME}',when="midnight")
logFormatter = logging.Formatter(f'%(asctime)s %(levelname)s %(threadName)s : %(message)s')
logHandler.setFormatter( logFormatter )
logger = logging.getLogger(f'Logs/AmoreCachingService/{LOG_FILENAME}')
logger.addHandler( logHandler )
logger.setLevel( logging.INFO )

async def main():
    dataCursor, profileIdsInCache = redisClient.scan(match='Profiles:*')
    # Script checks if cache is being loaded for first time 
    queryOn = 'isProfileActive' if len(profileIdsInCache) == 0 else 'wasProfileUpdated'
    query = async_db.collection("Profiles").where(queryOn, u'==',True)
    allProfiles = await query.get()
    logger.info(f"Updating Cache with {len(allProfiles)} profiles")
    # Writing the profiles to cache
    _ =  await asyncio.gather(*[write_to_cache(profile={"id": profile.id, **profile.to_dict()},
                                                redisClient=redisClient,
                                                logger=logger,
                                                async_db=async_db) for profile in allProfiles])                                                

# Argument Passing For How Often should the file run? Per Minute
if __name__ == '__main__':
    # Check Logic: See if there are Any profiles with key "Profiles:*" already in cache
    asyncio.run((main()))
    