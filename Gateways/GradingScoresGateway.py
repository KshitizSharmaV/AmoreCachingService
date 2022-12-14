import time 
import asyncio 
import json
from ProjectConf.RedisConf import redis_client

async def store_graded_profile_in_firestore_route(normalizedAllProfileScoresDf=None, logger=None, async_db=None):
    try:
        all_profile_scores_status = await asyncio.gather(*[store_profile_grading_firestore(scoringData=scoringData[1],
                                                            logger=logger,
                                                            async_db=async_db) for scoringData in normalizedAllProfileScoresDf.iterrows()])
        return True
    except Exception as e:
        logger.error(f"Async function failed to iterate over graded profiles in Grading Scores Gateway")
        logger.exception(e)


async def store_profile_grading_firestore(scoringData=None,logger=None,  async_db=None):
    try:
        if scoringData is not None:
            timestamp = time.time()
            profileGrade = {"totalScore": scoringData["totalScore"], 
                "popularityScore": scoringData["popularityScore"],
                "profileCompletionScore": scoringData["profileCompletionScore"],
                "activityScore": scoringData["activityScore"],
                "matchingScore": scoringData["matchingScore"],
                "userRank": scoringData["userRank"],
                "timestamp": timestamp
            }
            # store for quick access of grades
            await async_db.collection('ProfilesGrading').document(scoringData["profileId"]).set(profileGrade)
            # for historical storage of profile scores
            await async_db.collection('ProfilesGrading').document(scoringData["profileId"]).collection(scoringData["profileId"]).document(str(timestamp)).set(profileGrade)
            #  store latest grades to the 
            jsonObjectDumps = json.dumps(profileGrade, indent=4, sort_keys=True, default=str)
            # Redis - Create a new document if doesn't already exist in the database
            redis_client.set(f"GradingScore:{scoringData['profileId']}", jsonObjectDumps)
            logger.info(f"{scoringData['profileId']}: Profile grades stored successfully in cache and firestore")
        else:
            logger.error(f"Scoring Data is None")
    except Exception as e:
        logger.error(f"{scoringData['profileId']}: Exception in storing grading score for profile")
        logger.exception(e)
    