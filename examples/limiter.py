import asyncio
import datetime
import functools
from typing import Callable

import aiohttp
import async_requests

COUNT = 0


def timer():
    def wrapper(function: Callable):
        @functools.wraps(function)
        async def wrapped(*args, **kwargs) -> None:
            global COUNT
            COUNT += 1
            local_count = COUNT
            time = datetime.datetime.now().strftime("%H:%M:%S")
            print("Starting %s. at %s" % (local_count, time))
            await function(*args, **kwargs)
            time = datetime.datetime.now().strftime("%H:%M:%S")
            print("Finished %s. at %s" % (local_count, time))

            return None

        return wrapped

    return wrapper


async def parse(response: aiohttp.ClientResponse) -> str:
    await asyncio.sleep(5)
    text = await response.text()
    return text


@timer()
async def make_request(url: str) -> None:
    session = aiohttp.ClientSession()
    # Singleton - always returns same instance!
    limiter = await async_requests.Limiter.build(session=session, max_concurrency=2)
    _ = await limiter.get(url, parser=parse)
    await session.close()
    return None


async def test() -> None:
    url = "https://www.scrapethissite.com/pages/simple/"
    async with asyncio.TaskGroup() as tg:
        for _ in range(1, 5):
            tg.create_task(make_request(url))


asyncio.run(test())
