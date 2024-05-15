# async_requests

Limit number of async requests being made concurrently. 

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


async def parse(response: aiohttp.ClientResponse) -> str:
    await asyncio.sleep(5)
    text = await response.text()
    return text


@timer()
async def make_request(limiter: async_requests.Limiter, url: str) -> None:
    _ = await limiter.get(url, parser=parse)
    return None


async def test() -> None:
    session = aiohttp.ClientSession()
    limiter = async_requests.Limiter(session=session, max_concurrency=2)
    url = "https://www.scrapethissite.com/pages/simple/"
    async with asyncio.TaskGroup() as tg:
        for _ in range(1, 5):
            tg.create_task(make_request(limiter, url))
    await session.close()


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
