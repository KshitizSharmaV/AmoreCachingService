import redis
from redis.commands.json.path import Path
import json

redisClient = redis.StrictRedis (
    host = "localhost",
    port = "6379",
    charset="utf-8",
    decode_responses=True
)

# cursor, keys = r.scan(match='123*')
# data = r.mget(keys)

# redisClient.set('mykey','hello from kshitiz')
# value= redisClient.get('mykey')
# print(value)


# redisClient.zadd('vehicles', {'car' : 0})
# redisClient.zadd('vehicles', {'bike' : 0})
# vehicles = redisClient.zrange('vehicles', 0, -1)
# print(vehicles)


# jsonObejct = [{"type":"Kshiti","Hey":"World"}, {"okay":"hey"}]
# jsonObject_dumps = json.dumps(jsonObejct)
# redisClient.set("profile1",jsonObject_dumps)

# unpacked_item = json.loads(redisClient.get('profile1'))
# print("Un-packed")
# print(unpacked_item)