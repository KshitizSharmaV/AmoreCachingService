import redis
import os
from redis import ResponseError
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

in_env = os.getenv('CACHING_SERVICE_SERVICE_HOST', None)

if in_env:
    redis_client = redis.StrictRedis(
        host="redis-svc.default",
        port=6379,
        charset="utf-8",
        decode_responses=True
    )
else:
    redis_client = redis.StrictRedis(
        host="localhost",
        port=6379,
        charset="utf-8",
        decode_responses=True
    )

# Profiles Options for index creation
profile_index_def = IndexDefinition(index_type=IndexType.JSON, prefix=["profile:"])
# Profiles Schema definition
profile_schema = (
    TextField("$.geohash", as_name="geohash", sortable=True),
    TextField("$.geohash1", as_name="geohash1"),
    TextField("$.geohash2", as_name="geohash2"),
    TextField("$.geohash3", as_name="geohash3"),
    TextField("$.geohash4", as_name="geohash4"),
    TextField("$.geohash5", as_name="geohash5"),
    TextField("$.genderIdentity", as_name="genderIdentity"),
    TextField("$.religion", as_name="religion"),
    TextField("$.id", as_name="id"),
    NumericField("$.age", as_name="age", sortable=True)
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
        redis_client.ft("idx:profile").create_index(profile_schema, definition=profile_index_def)
        print("Index for profiles created")
    except ResponseError:
        print("Index already exists")


def try_creating_fcm_index_for_redis():
    """Create a index for FCMTokens in redis for querying
    """
    try:
        redis_client.ft("idx:FCMTokens").create_index(fcm_schema, definition=fcm_index_def)
        print("Index for FCMTokens created")
    except ResponseError:
        print("Index already exists for FCM Tokens")


def check_redis_index_exists(index: str) -> bool:
    """Check if the index exists in the redis database
    
    Args:
        index: String: to check if index exists in redis
    """
    try:
        redis_client.ft(index_name=index).info()
        return True
    except ResponseError:
        return False


if __name__ == "__main__":
    try_creating_profile_index_for_redis()
    # try_creating_fcm_index_for_redis()
