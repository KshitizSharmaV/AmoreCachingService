from redis import Redis, ResponseError
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition
from redis.commands.search.query import Query
from ProjectConf.ReddisConf import redisClient

# Options for index creation
index_def = IndexDefinition(prefix=["profile:"])

# Schema definition
schema = (
    TextField("geohash", sortable=True),
    TextField("geohash1", sortable=True),
    TextField("geohash2", sortable=True),
    TextField("geohash3", sortable=True),
    TextField("geohash4", sortable=True),
    TextField("geohash5", sortable=True),
    TextField("genderPreference", sortable=True),
    TextField("religionPreference", sortable=True),
    TextField("id", sortable=True),
    NumericField("age", sortable=True)
)


def try_creating_profile_index_for_redis():
    try:
        redisClient.ft("idx:profile").create_index(schema, definition=index_def)
        print("Index for profiles created")
    except ResponseError:
        print("Index already exists")


def check_redis_index_exists(index: str) -> bool:
    try:
        redisClient.ft(index_name=index).info()
        return True
    except ResponseError:
        return False
