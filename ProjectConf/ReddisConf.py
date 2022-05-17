import redis
import os
from redis.commands.json.path import Path
import json

redis_service_host = os.getenv('REDIS_SVC_SERVICE_HOST', None)
redis_service_port = os.getenv('REDIS_SVC_SERVICE_PORT', None)

if redis_service_host and redis_service_port:
    redisClient = redis.StrictRedis (
    host = redis_service_host,
    port = redis_service_port,
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
