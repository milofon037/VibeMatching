import asyncio

from bot.backend_client import BackendClient
from bot.config import settings


async def main() -> None:
    client = BackendClient(base_url=settings.backend_base_url)
    telegram_id = 990001

    status, _ = await client.register_user(telegram_id)
    assert status in (200, 201)

    profile_status, _ = await client.get_profile_me(telegram_id)
    if profile_status == 404:
        create_status, _ = await client.create_profile(
            telegram_id,
            {"name": "SmokeBot", "age": 25, "gender": "male", "city": "Kazan"},
        )
        assert create_status == 200

    feed_status, feed_payload = await client.feed(telegram_id, limit=1)
    assert feed_status == 200
    assert isinstance(feed_payload, list)

    matches_status, matches_payload = await client.get_matches(telegram_id)
    assert matches_status == 200
    assert isinstance(matches_payload, list)

    print("bot smoke test: OK")


if __name__ == "__main__":
    asyncio.run(main())
