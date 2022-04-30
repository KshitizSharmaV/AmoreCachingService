import redis
from redis.commands.json.path import Path
import json

redisClient = redis.StrictRedis (
    host = "localhost",
    port = "6379",
    charset="utf-8",
    decode_responses=True
)
