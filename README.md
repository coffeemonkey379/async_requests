# async_requests

A class which limits the number of concurrent async requests being made.

## Installation

``` shell

pip install async_requests -i http://192.168.50.88:3141/fideres/live --trusted-host 192.168.50.88 --extra-index-url https://pypi.org/simple

```

## Example

``` Python

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


# Sleep for 5 seconds in parser function
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



```

This would expect the following outcome...

```shell

Starting 1. at 18:15:25
Starting 2. at 18:15:25
Starting 3. at 18:15:25
Starting 4. at 18:15:25
Finished 1. at 18:15:30
Finished 2. at 18:15:30
Finished 3. at 18:15:35
Finished 4. at 18:15:35

```

## Multiple Instance

If you require multiple instances of Limiter i.e. to cap requests to different URLs, you should just inherit.

``` Python

import asyncio

import aiohttp
import async_requests


class LimiterOne(async_requests.Limiter):
    pass


class LimiterTwo(async_requests.Limiter):
    pass


async def inheritance_test():
    session = aiohttp.ClientSession()
    # Singleton - always returns same instance!
    limiter_one_a = await LimiterOne.build(session=session, max_concurrency=2)
    limiter_one_b = await LimiterOne.build(session=session, max_concurrency=2)

    limiter_two_a = await LimiterTwo.build(session=session, max_concurrency=2)
    limiter_two_b = await LimiterTwo.build(session=session, max_concurrency=2)
    assert limiter_one_a is limiter_one_b
    assert limiter_two_a is limiter_two_b
    assert limiter_one_a is not limiter_two_a
    assert limiter_one_b is not limiter_two_b


asyncio.run(test())

```