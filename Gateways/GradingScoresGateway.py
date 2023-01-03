import time 
import asyncio 
import json
from ProjectConf.RedisConf import redis_client

# @current_app.route('/storeprofilegradingscore', methods=['POST'])
# def store_profile_grading_score():
#     try:
#         # Get the json object of the graded profiles
#         normalizedAllProfileScoresDf = request.get_json().get('normalizedAllProfileScoresDf')
#         normalizedAllProfileScoresDf = pd.DataFrame(normalizedAllProfileScoresDf)
#         logger.info("Received new grading scores to be stored to firestore and cache")
#         logger.info(normalizedAllProfileScoresDf)
#         future = run_coroutine(
#                     store_graded_profile_in_firestore_route(normalizedAllProfileScoresDf=normalizedAllProfileScoresDf,
#                                                     logger=current_app.logger,
#                                                     async_db=async_db))
#         newProfilesCached = future.result()
#         current_app.logger.info(f"Successfully wrote grading scores to firestore/cache")
#         return json.dumps({"status": True})
#     except Exception as e:
#         current_app.logger.error(f"Failed to write grading scores to firestore or cache")
#         current_app.logger.exception(e)
#         return json.dumps({"status": False})


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
    