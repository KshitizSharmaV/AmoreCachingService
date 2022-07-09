import asyncio
import pandas as pd
from redis import Redis
from logging import Logger
from Gateways.RecommendationEngine.ProfilesGrader import ProfilesGrader
from Gateways.RecommendationEngine.ProfilesFetcher import ProfilesFetcher


class RecommendationSystem:
    """
    - Recursive Profile Fetcher on Query, Include removal of profiles already seen or in deck
    - Profile Grading modules
        - Popularity Score
        - Profile Completion Score
        - Activity Score
        - Matching Score
    - Dataframe sorting
    """
    profile_grader: ProfilesGrader
    profiles_fetcher: ProfilesFetcher
    current_user_id: str
    current_user_data: dict
    current_user_filters: dict
    profiles_already_in_deck: [str]
    other_users_data: [dict]
    redis_client: Redis
    logger: Logger

    normalised_other_users_df: pd.DataFrame

    def __init__(self, current_user_id: str, current_user_filters: dict, profiles_already_in_deck: [str],
                 redis_client: Redis, logger: Logger):
        self.current_user_id = current_user_id
        self.current_user_filters = current_user_filters
        self.profiles_already_in_deck = profiles_already_in_deck
        self.redis_client = redis_client
        self.logger = logger
        self.profiles_fetcher = ProfilesFetcher(current_user_id=current_user_id,
                                                current_user_filters=current_user_filters,
                                                profiles_already_in_deck=profiles_already_in_deck,
                                                redis_client=redis_client, logger=logger)

    def fetch_current_and_other_users_data(self):
        """
        - Fetch current and other users' data
            - Other users data fetched recursively with elimination filters on
        """
        try:
            self.current_user_data = self.profiles_fetcher.fetch_current_user_data()
            self.other_users_data = self.profiles_fetcher.get_final_fetched_profiles()
        except Exception as e:
            self.logger.exception(e)

    def grade_other_users_profiles(self):
        """
        - Grade/Rate the other users profiles fetched in previous step
        - Get the normalised data frame of other users' data
        """
        try:
            self.profile_grader = ProfilesGrader(current_user_data=self.current_user_data,
                                                 other_users_data=self.other_users_data,
                                                 redis_client=self.redis_client, logger=self.logger)
            self.normalised_other_users_df = asyncio.run(self.profile_grader.get_normalised_graded_profiles_df())
        except Exception as e:
            self.logger.exception(e)

    def build_recommendations(self):
        """
        - Fetch current and other users' data
            - Other users data fetched recursively with elimination filters on
        - Grade/Rate the other users profiles fetched in previous step
        - Get the normalised data frame of other users' data
        - Take the top 50 before further processing
        - Use religion, career, community, education and country preferences to rank the top 50 profiles
        - Return the top 50 profiles in that order
        """
        self.fetch_current_and_other_users_data()
        self.grade_other_users_profiles()

        pass
