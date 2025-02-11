import json
from typing import Optional

import redis.asyncio as redis

from pywce import pywce_logger

logger = pywce_logger(__name__, False)

REDIS_URL = "redis://localhost"


class RedisManager:
    """Handles Redis Pub/Sub for incoming and outgoing messages."""
    _redis: Optional[redis.Redis] = None
    _instance: Optional["RedisManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connect()
        return cls._instance

    def _connect(self):
        if self._redis is None:
            self._redis = redis.from_url(REDIS_URL)

    def get_instance(self) -> redis.Redis:
        self._connect()
        return self._redis

    async def publish(self, channel: str, message: dict):
        r = self.get_instance()

        async with r.pubsub() as pubsub:
            result = await r.publish(channel, json.dumps(message))
            logger.info(f"publish result: {result}")
