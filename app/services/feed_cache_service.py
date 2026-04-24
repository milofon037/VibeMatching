from redis.asyncio import Redis


class FeedCacheService:
    def __init__(self, redis_client: Redis, ttl_seconds: int = 900) -> None:
        self.redis_client = redis_client
        self.ttl_seconds = ttl_seconds

    def _key(self, user_id: int) -> str:
        return f"feed:queue:user:{user_id}"

    async def get_cached_profile_ids(self, user_id: int, limit: int) -> list[int]:
        if limit <= 0:
            return []

        key = self._key(user_id)
        cached_values = await self.redis_client.lrange(key, 0, limit - 1)
        profile_ids: list[int] = []
        for value in cached_values:
            try:
                profile_ids.append(int(value))
            except (TypeError, ValueError):
                continue
        return profile_ids

    async def consume(self, user_id: int, count: int) -> None:
        if count <= 0:
            return

        key = self._key(user_id)
        await self.redis_client.ltrim(key, count, -1)

    async def replace_cache(self, user_id: int, profile_ids: list[int]) -> None:
        key = self._key(user_id)
        await self.redis_client.delete(key)

        if not profile_ids:
            return

        payload = [str(profile_id) for profile_id in profile_ids]
        await self.redis_client.rpush(key, *payload)
        await self.redis_client.expire(key, self.ttl_seconds)
