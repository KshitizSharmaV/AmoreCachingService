import redis
import os
from redis.commands.json.path import Path
import json

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
