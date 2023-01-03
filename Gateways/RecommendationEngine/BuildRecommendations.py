import asyncio
import traceback

import pandas as pd
from redis import Redis
from logging import Logger
from Gateways.RecommendationEngine.ProfilesGrader import ProfilesGrader
from Gateways.RecommendationEngine.ProfilesFetcher import ProfilesFetcher
from ProjectConf.AsyncioPlugin import run_coroutine
# IMPORTS FOR TEST
from Gateways.RecommendationEngine.ProfilesFetcher import ProfilesFetcher
from ProjectConf.LoggerConf import logger as logger1


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
    other_users_data: dict
    logger: Logger

    normalised_other_users_df: pd.DataFrame

    def __init__(self, current_user_id: str, current_user_filters: dict, profiles_already_in_deck: [str], logger: Logger):
        self.current_user_id = current_user_id
        self.current_user_filters = current_user_filters
        self.profiles_already_in_deck = profiles_already_in_deck
        self.logger = logger
        self.profiles_fetcher = ProfilesFetcher(current_user_id=current_user_id,
                                                current_user_filters=current_user_filters,
                                                profiles_already_in_deck=profiles_already_in_deck,
                                                logger=logger)

    def fetch_current_and_other_users_data(self):
        """
        - Fetch current and other users' data
            - Other users data fetched recursively with elimination filters on
        """
        try:
            self.current_user_data = self.profiles_fetcher.fetch_current_user_data()
            self.profiles_fetcher.fetch_profile_ids_already_seen_by_user()
            # Brings all the profiles which are not seen by the user
            self.other_users_data = self.profiles_fetcher.get_final_fetched_profiles()
        except Exception as e:
            self.logger.exception(e)

    def grade_other_users_profiles(self):
        """
        - Grade/Rate the other users profiles fetched in previous step
        - Get the normalised data frame of other users' data
        """
        try:
            if self.other_users_data:
                self.profile_grader = ProfilesGrader(current_user_data=self.current_user_data,
                                                     other_users_data=self.other_users_data,
                                                     logger=self.logger)
                future = run_coroutine(self.profile_grader.get_normalised_graded_profiles_df())
                self.normalised_other_users_df = future.result()
            else:
                self.normalised_other_users_df = pd.DataFrame()
        except Exception as e:
            self.logger.exception(e)

    def build_recommendations(self):
        """
        - Fetch current and other users' data
            - Other users data fetched recursively with elimination filters on
        - Grade/Rate the other users profiles fetched in previous step
        - Get the normalised data frame of other users' data
        - Use religion, education and country preferences to rank the top 50 profiles
        - Return the top 50 profiles in that order
        """
        self.fetch_current_and_other_users_data()
        self.grade_other_users_profiles()
        '''
        Available:
        current_user_data: dict
        other_user_data: list(dict)
        normalised_df: Dataframe
        '''
        if not self.normalised_other_users_df.empty:
            self.normalised_other_users_df.sort_values(by=['userRank'], inplace=True)
            return [self.other_users_data.get(user_id) for user_id in self.normalised_other_users_df.index.tolist() if
                    self.other_users_data.get(user_id)]
        else:
            return []


if __name__ == "__main__":
    recommendation_obj = RecommendationSystem(current_user_id="nVA4bAkUWubnEFGTVdO4IVUDDW02",
                                              current_user_filters={"radiusDistance": 50}, 
                                              profiles_already_in_deck=[],
                                              logger=logger1)
    recommendation_obj.build_recommendations()
