import random
import asyncio
import pandas as pd
from google.cloud import firestore
from redis import Redis
from logging import Logger
from ProjectConf.FirestoreConf import async_db
from Gateways.MatchUnmatchGateway import MatchUnmatch_fetch_userdata_from_firebase_or_redis


class ProfilesGrader:
    """
    Profile Grading modules
        - Popularity Score
        - Profile Completion Score
        - Activity Score
        - Matching Score
    - All Scores aggregator
    """
    current_user_data: dict
    redis_client: Redis
    logger: Logger
    weights: dict = {
        "popularityScoreWeighted": 0.45,
        "profileCompletionScoreWeighted": 0.25,
        "activityScoreWeighted": 0.30
    }

    # weights: dict = {
    #     "popularityScoreWeighted": 0.35,
    #     "profileCompletionScoreWeighted": 0.15,
    #     "activityScoreWeighted": 0.20,
    #     "matchingScoreWeighted": 0.30
    # }

    def __init__(self, current_user_data: dict, other_users_data: [dict], redis_client: Redis, logger):
        self.current_user_data = current_user_data
        self.other_users_data = other_users_data
        self.redis_client = redis_client
        self.logger = logger

    async def get_profiles_from_subcollection_firestore(self, collectionName=None, userId=None,
                                                        collectionNameChild=None,
                                                        matchFor=None):
        docs = async_db.collection(collectionName).document(userId).collection(collectionNameChild) \
            .where(u'swipe', u'==', matchFor).order_by(u'timestamp', direction=firestore.Query.DESCENDING).stream()
        user_ids = [doc.id async for doc in docs]
        return user_ids

    async def get_profile_ids_for_likes_dislikes_redis(self, user_id: str, sub_collection: str, swipe_type: str):
        try:
            redis_key = f"LikesDislikes:{user_id}:{sub_collection}:{swipe_type}"
            id_list = list(self.redis_client.smembers(redis_key))
            if not id_list:
                id_list = await self.get_profiles_from_subcollection_firestore(collectionName=u'LikesDislikes',
                                                                               userId=user_id,
                                                                               collectionNameChild=sub_collection,
                                                                               matchFor=swipe_type)
                self.redis_client.sadd(redis_key, *id_list)
            return id_list
        except Exception as e:
            self.logger.exception(e)

    async def profile_ids_which_liked_user(self, user_id: str):
        try:
            return await self.get_profile_ids_for_likes_dislikes_redis(user_id=user_id, sub_collection="Received",
                                                                       swipe_type="Likes")
        except Exception as e:
            self.logger.exception(e)

    async def profile_ids_which_disliked_user(self, user_id: str):
        try:
            return await self.get_profile_ids_for_likes_dislikes_redis(user_id=user_id, sub_collection="Received",
                                                                       swipe_type="Dislikes")
        except Exception as e:
            self.logger.exception(e)

    async def profile_ids_which_superliked_user(self, user_id: str):
        try:
            return await self.get_profile_ids_for_likes_dislikes_redis(user_id=user_id, sub_collection="Received",
                                                                       swipe_type="Superlikes")
        except Exception as e:
            self.logger.exception(e)

    async def profile_ids_liked_by_user(self, user_id: str):
        try:
            return await self.get_profile_ids_for_likes_dislikes_redis(user_id=user_id, sub_collection="Given",
                                                                       swipe_type="Likes")
        except Exception as e:
            self.logger.exception(e)

    async def profile_ids_disliked_by_user(self, user_id: str):
        try:
            return await self.get_profile_ids_for_likes_dislikes_redis(user_id=user_id, sub_collection="Given",
                                                                       swipe_type="Dislikes")
        except Exception as e:
            self.logger.exception(e)

    async def profile_ids_superliked_by_user(self, user_id: str):
        try:
            return await self.get_profile_ids_for_likes_dislikes_redis(user_id=user_id, sub_collection="Given",
                                                                       swipe_type="Superlikes")
        except Exception as e:
            self.logger.exception(e)

    async def calculate_popularity_score(self, user_id=None):
        """
        Popularity score is calculated based on number of super likes, likes & dislike received
            superlike -- +4
            like -- +2
            dislike -- -1
            _______________
            561
            How to convert 561 to a score on 0-10 scale?
        """
        try:
            liked_by_list = await self.profile_ids_which_liked_user(user_id=user_id)
            disliked_by_list = await self.profile_ids_which_disliked_user(user_id=user_id)
            superliked_by_list = await self.profile_ids_which_superliked_user(user_id=user_id)
            # logger.info(f"{userId}: Successfully calculated profile popularity score")
            return (4 * len(superliked_by_list)) + (2 * len(liked_by_list)) - len(disliked_by_list)
        except Exception as e:
            self.logger.error(f"{user_id}: Unable to calculate popularity score")
            return

    # how much of profile has user completed
    async def get_profile_completion_score(self, user_profile: dict):
        try:
            return (float(user_profile['profileCompletion']) / 100) * 10
        except Exception as e:
            self.logger.error(f"{self.current_user_data['id']}: Unable to get profile completion score")
            return

    # a user with more matches will be given more score
    async def calculate_matching_score(self, user_id=None):
        """
        bring matches and unmatches into normalised df
        """
        try:
            # logger.error(f"{userId}: Successfully calculated matching score")
            return random.uniform(0, 1)
        except Exception as e:
            self.logger.error(f"{user_id}: Unable to get matching score")
            return

    # How active a user is calculated by counting their total swipes
    async def calculate_activity_score(self, user_id=None):
        """
            superlike -- +4
            like -- +2
            dislike -- -1
        """
        try:
            user_like_list = await self.profile_ids_liked_by_user(user_id=user_id)
            user_dislike_list = await self.profile_ids_disliked_by_user(user_id=user_id)
            user_super_like_list = await self.profile_ids_superliked_by_user(user_id=user_id)
            return (4 * len(user_super_like_list)) + (2 * len(user_like_list)) + len(user_dislike_list)
        except Exception as e:
            self.logger.error(f"{user_id}: Unable to calculate the activity score")
            return

    async def calculate_all_scores_for_profile(self, user_profile: dict):
        try:
            popularity_score = await self.calculate_popularity_score(user_id=user_profile.get('id'))
            profile_completion_score = await self.get_profile_completion_score(user_profile=user_profile)
            activity_score = await self.calculate_activity_score(user_id=user_profile.get('id'))
            all_profile_scores = {
                "userId": user_profile.get('id'),
                "popularity_score": popularity_score,
                "profile_completion_score": profile_completion_score,
                "activity_score": activity_score
            }
            # matchingScore = await self.calculate_matching_score(user_id=user_profile.get('id'))
            # all_profile_scores = {"userId": user_profile.get('id'),
            #                     "popularity_score": popularity_score,
            #                     "profile_completion_score": profile_completion_score,
            #                     "activity_score": activity_score,
            #                     "matchingScore": matchingScore}
            self.logger.info(f"{user_profile.get('id')}: Successfully calculated total profile score")
            return all_profile_scores
        except Exception as e:
            self.logger.error(f"{user_profile.get('id')}: Unable to calculate total profile completion score")
            return

    async def get_no_of_matches_and_unmatches_for_user(self, user_id):
        try:
            data = await asyncio.gather(*[
                MatchUnmatch_fetch_userdata_from_firebase_or_redis(userId=user_id, childCollectionName=fromCollection,
                                                                   redisClient=self.redis_client, logger=self.logger)
                for
                fromCollection in ['Match', 'Unmatch']])
            matches, unmatches = len(data[0]), len(data[1])
            return {"profileId": user_id, "matches": matches, "unmatches": unmatches}
        except Exception as e:
            self.logger.exception(e)

    async def get_normalised_graded_profiles_df(self):
        try:
            all_profile_scores_df = await asyncio.gather(
                *[self.calculate_all_scores_for_profile(user_profile=user_profile) for user_profile in
                  self.other_users_data])
            all_profile_scores_df = pd.DataFrame(all_profile_scores_df)
            all_profile_scores_df = all_profile_scores_df.set_index('userId')
            # normalize data
            normalized_all_profile_scores_df = (all_profile_scores_df - all_profile_scores_df.min()) / (
                    all_profile_scores_df.max() - all_profile_scores_df.min())

            for columnName in list(normalized_all_profile_scores_df.columns):
                normalized_all_profile_scores_df[columnName + "Weighted"] = normalized_all_profile_scores_df[
                                                                                columnName] * \
                                                                            self.weights.get(columnName + "Weighted")

            normalized_all_profile_scores_df["totalScore"] = normalized_all_profile_scores_df[
                [name for name in normalized_all_profile_scores_df.columns if "Weighted" in name]].sum(axis=1)

            normalized_all_profile_scores_df["userRank"] = normalized_all_profile_scores_df["totalScore"].rank(
                ascending=False)

            normalized_all_profile_scores_df["profileId"] = normalized_all_profile_scores_df.index

            ids = normalized_all_profile_scores_df["profileId"].tolist()
            matches_unmatches_dicts = asyncio.gather(
                *[self.get_no_of_matches_and_unmatches_for_user(user_id=id) for id in ids])
            normalized_all_profile_scores_df = normalized_all_profile_scores_df.append(matches_unmatches_dicts,
                                                                                       ignore_index=True)

            return normalized_all_profile_scores_df
        except Exception as e:
            self.logger.error(f"Error occurred in Profile Grader")
            self.logger.exception(e)
