import asyncio

import async_requests
import pytest


@pytest.fixture
def max_concurrency() -> int:
    return 2


@pytest.fixture
def concurrency_limiter(max_concurrency: int) -> async_requests.ConcurrencyLimiter:
    cl = async_requests.ConcurrencyLimiter(max_concurrency)
    return cl
