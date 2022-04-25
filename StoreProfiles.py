import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

import asyncio
from google.cloud import firestore
from ProjectConf.FirestoreConf import db, async_db
import json


async def main():
    allProfiles = {}
    query = async_db.collection("Profiles")
    docs = await query.get()
    count = 0
    for doc in docs:
        count += 1
        print(f"{doc.id} => {doc.to_dict()}")
        allProfiles[doc.id] = doc.to_dict()
    print(f"Count:{count}")

    with open('CachingService/AllProfiles_Cache.json', 'w') as f:
        json.dump(allProfiles, f, indent=4, sort_keys=True, default=str)

if __name__ == '__main__':
    asyncio.run(main())