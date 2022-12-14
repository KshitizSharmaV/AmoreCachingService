import redis
import os
from redis.commands.json.path import Path
import json

from redis import Redis, ResponseError
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query


in_env = os.getenv('CACHING_SERVICE_SERVICE_HOST', None)

if in_env:
    redisClient = redis.StrictRedis (
        host = "redis-svc.default",
        port = "6379",
        charset="utf-8",
        decode_responses=True
    )
else:
    redisClient = redis.StrictRedis (
        host = "localhost",
        port = "6379",
        charset="utf-8",
        decode_responses=True
    )


# Profiles Options for index creation
profile_index_def = IndexDefinition(prefix=["profile:"])
# Profiles Schema definition
profile_schema = (
    TextField("geohash", sortable=True),
    TextField("geohash1", sortable=True),
    TextField("geohash2", sortable=True),
    TextField("geohash3", sortable=True),
    TextField("geohash4", sortable=True),
    TextField("geohash5", sortable=True),
    TextField("genderIdentity", sortable=True),
    TextField("religion", sortable=True),
    TextField("id", sortable=True),
    TextField("isProfileActive", sortable=True),
    NumericField("age", sortable=True)
)

# FCMTokens Options for index creation
fcm_index_def = IndexDefinition(index_type=IndexType.JSON, prefix=["FCMTokens:"])
# FCMTokens Schema definition
fcm_schema = (
    TextField("$.userId", as_name="userId"),
    TextField("$.deviceId", as_name="deviceId")
)

def try_creating_profile_index_for_redis():
    """Creates indexes in redis for profiles querying
    """
    try:
        redisClient.ft("idx:profile").create_index(profile_schema, definition=profile_index_def)
        print("Index for profiles created")
    except ResponseError:
        print("Index already exists")


def try_creating_fcm_index_for_redis():
    """Create a index for FCMTokens in redis for querying
    """
    try:
        redisClient.ft("idx:FCMTokens").create_index(fcm_schema, definition=profile_index_def)
        print("Index for FCMTokens created")
    except ResponseError:
        print("Index already exists for FCM Tokens")


def check_redis_index_exists(index: str) -> bool:
    """Check if the index exists in the redis database
    
    Args:
        index: String: to check if index exists in redis
    """
    try:
        redisClient.ft(index_name=index).info()
        return True
    except ResponseError:
        return False



if __name__ == "__main__":
    try_creating_profile_index_for_redis()
    try_creating_fcm_index_for_redis()


