import asyncio

import async_requests
import pytest


@pytest.mark.asyncio
async def test_asyncio_lock(
    concurrency_limiter: async_requests.ConcurrencyLimiter, max_concurrency: int
) -> None:
    async def quick_sleep() -> None:
        await asyncio.sleep(0.1)

    async def check_concurrency() -> None:
        try:
            async with asyncio.timeout(1):
                while True:
                    assert concurrency_limiter._concurrent_requests <= max_concurrency
                    await asyncio.sleep(0.01)
        except TimeoutError:
            pass

    async with asyncio.TaskGroup() as tg:
        for _ in range(10):
            tg.create_task(concurrency_limiter(quick_sleep))
        tg.create_task(check_concurrency())
