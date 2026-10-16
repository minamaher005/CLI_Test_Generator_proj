import asyncio
from typing import Awaitable, Callable


class RetryError(RuntimeError):
    """Raised when every retry attempt has failed."""


async def retry(
    coro_factory: Callable[[], Awaitable],
    attempts: int = 3,
    delay: float = 0.01,
):
    """Await the coroutine *returned by the factory*, retrying on failure.

    The factory is called once per attempt, so each attempt gets a fresh
    coroutine. After all attempts fail, RetryError is raised (chained from
    the last exception).
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            return await coro_factory()
        except Exception as e:
            last_exc = e
            if attempt < attempts:
                await asyncio.sleep(delay)
    raise RetryError(f"all {attempts} attempts failed") from last_exc


async def with_timeout(coro, seconds: float):
    """Await coro with a timeout; returns None if it times out instead.

    A non-positive timeout raises ValueError before awaiting anything.
    """
    if seconds <= 0:
        raise ValueError("timeout must be positive")
    try:
        return await asyncio.wait_for(coro, timeout=seconds)
    except asyncio.TimeoutError:
        return None


async def _fail_n_times(n: int, state: list):
    """Helper used by tests: fail n times, then succeed."""
    state.append(1)
    if len(state) <= n:
        raise ConnectionError("flaky service")
    return "ok"
