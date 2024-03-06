import asyncio
from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine, TypeVar

import aiohttp

T = TypeVar("T")

ParserFunc = Callable[[aiohttp.ClientResponse], Coroutine[Any, Any, T]]


class RequestException(Exception):
    pass


class AsyncRequests(ABC):

    @property
    @abstractmethod
    def session(self) -> aiohttp.ClientSession:
        pass

    async def _post_base(
        self,
        url: str,
        json: dict,
        parser: ParserFunc[T],
    ) -> T:
        async with self.session.post(url, json=json) as response:
            parsed = await parser(response)

        return parsed

    async def _get_base(
        self,
        url: str,
        parser: ParserFunc[T],
    ) -> T:
        async with self.session.get(url) as response:
            if response.status != 200:
                raise RequestException()

            parsed = await parser(response)
        return parsed


class ConcurrencyLimiter:

    def __init__(self, max_concurrency: int):
        self.self = self
        self._lock = asyncio.Lock()
        self.max_concurrency = max_concurrency
        self._concurrent_requests = 0

    async def _run_function(
        self, func: Callable[..., Coroutine[Any, Any, T]], *args, **kwargs
    ) -> T:
        while True:
            async with self._lock:
                if self.self._concurrent_requests < self.max_concurrency:
                    self.self._concurrent_requests += 1
                    break
            await asyncio.sleep(0.01)
        res = await func(*args, **kwargs)
        async with self._lock:
            self.self._concurrent_requests -= 1
        return res


class AsyncRequestsLimiterBase(AsyncRequests):

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, max_concurrency: int):
        self.self = self
        self._limiter = ConcurrencyLimiter(max_concurrency)

    async def post(self, url: str, json: dict, parser: ParserFunc[T]) -> str:
        return await self._limiter._run_function(
            super()._post_base,
            *(
                url,
                json,
                parser,
            ),
        )

    async def get(self, url: str, parser: ParserFunc[T]) -> T:
        return await self._limiter._run_function(
            super()._get_base,
            *(
                url,
                parser,
            ),
        )
