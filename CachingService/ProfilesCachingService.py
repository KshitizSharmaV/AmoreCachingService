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
from ProjectConf.MongoDBConf import mongoClient, amoreCacheDB # MongoDB
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
    # Firestore - Querying updated profiles only
    query = async_db.collection("Profiles").where(u'wasProfileUpdated', u'==',True)
    docs = await query.get()
    logger.info(f"Updating {len(docs)} profiles in cache")
    # Writing the profiles to cache
    _ =  await asyncio.gather(*[write_to_cache(profile={"_id": profile.id, **profile.to_dict()},
                                                amoreCacheDB=amoreCacheDB,
                                                logger=logger,
                                                async_db=async_db) for profile in docs])

# Argument Passing For How Often should the file run? Per Minute
if __name__ == '__main__':
    asyncio.run(main())