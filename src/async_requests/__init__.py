import asyncio
from typing import Any, Callable, Coroutine, TypeVar

import aiohttp

T = TypeVar("T", bound=Any)

ParserFunc = Callable[[aiohttp.ClientResponse], Coroutine[Any, Any, T]]


class ConcurrencyLimiter:
    """Limits concurrency of functions called.

    Attributes:
        max_concurrency (int): Max number of concurrent requests.
    """

    def __init__(self, max_concurrency: int):
        """Creates instance.

        Args:
            max_concurrency (int): Max concurrent executions of callables passed.
        """
        self.self = self
        self._lock = asyncio.Lock()
        self._max_concurrency = max_concurrency
        self._concurrent_requests = 0

    @property
    def max_concurrency(self) -> int:
        return self._max_concurrency

    async def set_max_concurrency(self, value: int) -> None:
        if not isinstance(value, int):
            raise ValueError("must be an int!")
        elif value == self.max_concurrency:
            return None
        async with self._lock:
            self._max_concurrency = value

    async def __call__(
        self, func: Callable[..., Coroutine[Any, Any, T]], *args, **kwargs
    ) -> T:
        """Limit concurrency of callable passed.

        Args:
            func (Callable[..., Coroutine[Any, Any, T]]): Function to limit concurrent calls to.

        Returns:
            T: Result of coroutine.
        """
        while True:
            async with self._lock:
                if self._concurrent_requests < self.max_concurrency:
                    self._concurrent_requests += 1
                    break
            await asyncio.sleep(0.01)
        res = await func(*args, **kwargs)
        async with self._lock:
            self._concurrent_requests -= 1
        return res


class Singleton(type):
    """Singleton metaclass, limits instances of class to one.

    Returns:
        _instances (dict[type, type]):  Type of subclass and instance of subclass.
    """

    _instances: dict[type["Singleton"], "Singleton"] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Limiter(metaclass=Singleton):
    """Limit the concurrency of async requests.

    Attributes:
       max_concurrency (int): Max number of concurrent requests.
       session (aiohttp.ClientSession): Async request interface.
    """

    _instance = None
    _limiter = ConcurrencyLimiter(0)
    _session: aiohttp.ClientSession

    @classmethod
    async def build(
        cls, session: aiohttp.ClientSession, max_concurrency: int
    ) -> "Limiter":
        """Initialise instance based on max concurrent requests.

        Args:
            session (aiohttp.ClientSession): Async request interface.
            max_concurrency (int): Max number of concurrent requests.
        """
        self = cls()
        self._session = session
        await self._limiter.set_max_concurrency(max_concurrency)

        return self

    async def post(self, url: str, json: dict, parser: ParserFunc[T]) -> T:
        """Post request - executed when live concurrent requests are below max_concurrency.

        Args:
            url (str): Url to send request.
            json (dict): Payload to send with request.
            parser (ParserFunc[T]): Coroutine to parse the request response.

        Returns:
            T: Result of parser.
        """
        return await self._limiter(
            self._post_base,
            *(
                url,
                json,
                parser,
            ),
        )

    async def get(self, url: str, parser: ParserFunc[T]) -> T:
        """Get request - executed when live concurrent requests are below max_concurrency.

        Args:
            url (str): Url to send request.
            parser (ParserFunc[T]): Coroutine to parse the request response.

        Returns:
            T: Result of parser.
        """
        return await self._limiter(
            self._get_base,
            *(
                url,
                parser,
            ),
        )

    async def _post_base(self, url: str, json: dict, parser: ParserFunc[T]) -> T:
        async with self._session.post(url, json=json) as response:
            parsed = await parser(response)
        return parsed

    async def _get_base(self, url: str, parser: ParserFunc[T]) -> T:
        async with self._session.get(url) as response:
            parsed = await parser(response)
        return parsed
