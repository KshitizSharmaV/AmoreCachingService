import sys
import os

sys.path.extend([os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)), os.getcwd()])

import asyncio
import time
import traceback
from typing import Set
from redis import Redis
from logging import Logger
from pprint import pprint
from functools import lru_cache
from dataclasses import asdict
from Utilities.DictOps import ignore_none
from ProjectConf.FirestoreConf import db
from ProjectConf.ReddisConf import redisClient
from ProjectConf.LoggerConf import logger as logger1
from redis.commands.search.query import Query
from Gateways.GeoserviceEXTs.GeoserviceGatewayEXT import QueryBuilder, Profile
from Gateways.GeoserviceGateway import GeoService_store_profiles, Geoservice_calculate_geo_hash_from_radius
from Gateways.LikesDislikesGateway import LikesDislikes_get_profiles_already_seen_by_id
from Gateways.GeoserviceEXTs.GeoservicRedisQueryConf import try_creating_profile_index_for_redis, \
    check_redis_index_exists


class ProfilesFetcher:
    """
    Recursive Profile Fetcher on Query, Include removal of profiles already seen or in deck
    Fetch various profiles
        - Fetch current user's profile
        - Query profiles based on user filters
        - Compile and return current user's and queried user's profiles
    """
    current_user_id: str
    current_user_filters: dict
    profiles_already_seen: Set[str]
    redis_client: Redis
    logger: Logger
    geohash_keys: [str]
    current_user_data: dict

    def __init__(self, current_user_id: str, current_user_filters: dict, profiles_already_in_deck: [str],
                 redis_client: Redis, logger: Logger):
        self.current_user_id = current_user_id
        self.current_user_filters = current_user_filters
        self.profiles_already_seen = set(profiles_already_in_deck)
        # Exclude own profile from being recommended to self
        self.profiles_already_seen.add(self.current_user_id)
        self.redis_client = redis_client
        self.logger = logger
        self.geohash_keys = ['geohash1', 'geohash2', 'geohash3', 'geohash4', 'geohash5']

    def fetch_current_user_data_from_firestore(self) -> dict:
        try:
            return db.collection("Profiles").document(self.current_user_id).get().to_dict()
        except Exception as e:
            self.logger.exception(e)
            self.logger.error(traceback.format_exc())

    def fetch_current_user_data(self) -> dict:
        try:
            key = f"profile:{self.current_user_id}"
            self.current_user_data = asdict(Profile.decode_data_from_redis(self.redis_client.hgetall(key)),
                                            dict_factory=ignore_none)
            if not self.current_user_data:
                self.current_user_data = self.fetch_current_user_data_from_firestore()
                asyncio.run(GeoService_store_profiles(profile=self.current_user_data, redisClient=self.redis_client,
                                                      logger=self.logger))
            return self.current_user_data
        except Exception as e:
            self.logger.exception(e)
            self.logger.error(traceback.format_exc())

    def fetch_profile_ids_already_seen_by_user(self) -> [str]:
        try:
            profile_ids_already_swiped_by_user = asyncio.run(
                LikesDislikes_get_profiles_already_seen_by_id(userId=self.current_user_id, childCollectionName="Given",
                                                              redisClient=self.redis_client, logger=self.logger))
            self.profiles_already_seen = self.profiles_already_seen.union(set(profile_ids_already_swiped_by_user))
            return self.profiles_already_seen
        except Exception as e:
            self.logger.exception(e)
            self.logger.error(traceback.format_exc())

    def add_geohash_filter_for_radius_for_query(self):
        try:
            for geohash in self.geohash_keys:
                self.current_user_filters[geohash] = '*'
            geohash_level = Geoservice_calculate_geo_hash_from_radius(
                radius=self.current_user_filters.get('radiusDistance'))
            self.current_user_filters[geohash_level] = self.current_user_data.get(geohash_level, '*')
        except Exception as e:
            self.logger.exception(e)
            self.logger.error(traceback.format_exc())

    def build_exclusion_query(self, profile_ids_already_fetched: tuple = None):
        try:
            if profile_ids_already_fetched:
                profile_ids_already_fetched = list(profile_ids_already_fetched)
                profile_ids_already_fetched.extend(self.profiles_already_seen)
                exclusion_query = f"(-@id:{'|'.join(profile_ids_already_fetched)})"
            elif self.profiles_already_seen:
                exclusion_query = f"(-@id:{'|'.join(self.profiles_already_seen)})"
            else:
                exclusion_query = ""
            return exclusion_query
        except Exception as e:
            self.logger.exception(e)
            self.logger.error(traceback.format_exc())
            print(traceback.format_exc())

    def build_search_query(self, exclusion_query: str):
        try:
            query = QueryBuilder.from_dict(self.current_user_filters).query_builder()
            query = " ".join([query, exclusion_query] if exclusion_query else [query])
            return query
        except Exception as e:
            self.logger.exception(e)
            self.logger.error(traceback.format_exc())
            print(traceback.format_exc())

    def query_redis_for_profiles(self, query_string: str):
        try:
            return self.redis_client.ft("idx:profile").search(Query(query_string=query_string).paging(0, 10))
        except Exception as e:
            self.logger.exception(e)
            self.logger.error(traceback.format_exc())
            print(traceback.format_exc())

    def get_dict_for_redis_query_result(self, result_profile):
        try:
            profile = Profile.decode_data_from_redis(result_profile.__dict__).to_dict()
            profile['id'] = profile['id'].replace('profile:', '')
            return profile
        except Exception as e:
            self.logger.exception(e)
            self.logger.exception(traceback.format_exc())
            print(traceback.format_exc())

    def fetch_filtered_profiles_for_user(self, profile_ids_already_fetched: tuple = None) -> dict:
        """
        Use current user filters to build query for redis
        Recursively fetch profiles until either:
            - no of profiles = 100
            OR
            - Geohash1 and all profiles have been queried once
            - Eliminate profiles already seen or already in deck
        """
        try:
            exclusion_query = self.build_exclusion_query(profile_ids_already_fetched=profile_ids_already_fetched)
            query = self.build_search_query(exclusion_query=exclusion_query)
            result_profiles = self.query_redis_for_profiles(query_string=query)
            profiles_dict = {doc.id.replace('profile:', ''): self.get_dict_for_redis_query_result(doc) for doc in
                             result_profiles.docs}
            return profiles_dict
        except Exception as e:
            self.logger.exception(e)
            self.logger.error(traceback.format_exc())
            print(traceback.format_exc())

    def get_current_geohash_level(self):
        # Get the current geohash level
        try:
            current_geohash_level = None
            for geohash_key in self.geohash_keys:
                if self.current_user_filters.get(geohash_key) != '*':
                    current_geohash_level = geohash_key
            return current_geohash_level
        except Exception as e:
            self.logger.exception(e)
            self.logger.error(traceback.format_exc())

    def reduce_geohash_accuracy(self, geohash: str):
        """
        geohash3 --> geohash2
        Reduces geohash level of accuracy.
        :param geohash: Current geohash level
        :return: If geohash level = 1, returns None, else, returns reduced geohash level string
        """
        try:
            if geohash[-1] == '1':
                return None
            else:
                return f"geohash{str(int(geohash[-1]) - 1)}"
        except Exception as e:
            self.logger.exception(e)
            self.logger.error(traceback.format_exc())

    def reduce_current_geohash_level_in_filters(self, current_geohash_level: str = None):
        # Reduce the geohash level in filters dict, if current geohash level >= geohash 1
        try:
            if current_geohash_level:
                reduced_geohash_level = self.reduce_geohash_accuracy(current_geohash_level)
                current_geohash = self.current_user_filters.get(current_geohash_level)
                self.current_user_filters[current_geohash_level] = '*'
                if reduced_geohash_level:
                    self.current_user_filters[reduced_geohash_level] = current_geohash[:-1]
        except Exception as e:
            self.logger.exception(e)
            self.logger.error(traceback.format_exc())

    def get_final_fetched_profiles(self) -> dict:
        try:
            self.add_geohash_filter_for_radius_for_query()
            final_fetched_profiles = self.fetch_filtered_profiles_for_user()
            while len(final_fetched_profiles) < 50:
                # Base Case
                if all(x == '*' for x in [self.current_user_filters.get(elem) for elem in self.geohash_keys]):
                    break

                # Get the current geohash level
                current_geohash_level = self.get_current_geohash_level()

                # Reduce the geohash level in filters dict, if current geohash level >= geohash 1
                self.reduce_current_geohash_level_in_filters(current_geohash_level=current_geohash_level)

                # Fetch new sets of profiles using new filters, radius
                profile_ids_already_fetched = tuple(final_fetched_profiles.keys())
                final_fetched_profiles.update(
                    self.fetch_filtered_profiles_for_user(profile_ids_already_fetched=profile_ids_already_fetched))
            return final_fetched_profiles
        except Exception as e:
            self.logger.exception(e)
            self.logger.error(traceback.format_exc())


if __name__ == "__main__":
    start = time.time()
    if not check_redis_index_exists(index="idx:profile"):
        try_creating_profile_index_for_redis()
    profiles_fetcher = ProfilesFetcher(current_user_id="WbZZuRPhxRf6KL1GFHcNWL2Ydzk1",
                                       current_user_filters={"radiusDistance": 50, "genderPreference": "Male"},
                                       profiles_already_in_deck=[],
                                       redis_client=redisClient, logger=logger1)
    profiles = profiles_fetcher.get_final_fetched_profiles()
    print(len(profiles))
    # pprint(profiles)
    print(f"Total time: {time.time() - start}")
