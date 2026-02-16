from redis import asyncio as aioredis
from app.core.config import settings

class RedisService:
    _pool: aioredis.Redis = None

    @classmethod
    def get_redis(cls) -> aioredis.Redis:
        if cls._pool is None:
            cls._pool = aioredis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                encoding="utf-8",
                decode_responses=True
            )
        return cls._pool

    @classmethod
    async def close(cls):
        if cls._pool:
            await cls._pool.close()
            cls._pool = None

redis_service = RedisService()
