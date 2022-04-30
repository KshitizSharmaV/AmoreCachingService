import time 
import asyncio 
import json

async def store_graded_profile_in_firestore_route(normalizedAllProfileScoresDf=None, redisClient=None, logger=None, async_db=None):
    all_profile_scores_status = await asyncio.gather(*[store_profile_grading_firestore(userId=row[0],userData=row[1]) for row in  normalizedAllProfileScoresDf.iterrows()])


async def store_profile_grading_firestore(profile=None, userData=None,redisClient=None, logger=None,  async_db=None):
    try:
        timestamp = time.time()
        profileGrade = {"totalScore": userData.total_score, 
            "id":profile["id"],
            "popularityScore": userData.popularity_score,
            "profileCompletionScore": userData.profile_completion_score,
            "activityScore":userData.activity_score,
            "matchingScore":userData.matching_score,
            "userRank":userData.user_rank,
            "timestamp": timestamp
        }
        # store for quick access of grades
        await async_db.collection('ProfilesGrading').document(profile["id"]).set(profileGrade)
        # for historical storage of profile scores
        await async_db.collection('ProfilesGrading').document(profile["id"]).collection(profile["id"]).document(str(timestamp)).set(profileGrade)
        #  store latest grades to the 
        jsonObject_dumps = json.dumps(profile, indent=4, sort_keys=True, default=str)
        # Redis - Create a new document if doesn't already exist in the database
        redisClient.set(f"Profiles:{profile['id']}", jsonObject_dumps)
        
        redisClient.set(f"ProfileGrade:{profile['id']}", )
        print(f"Profile grading for {profile['id']} stored successfully.")
        
    except Exception as e:
        print(f"Exception in storing profile grading for {profile['id']}: {e}")
    