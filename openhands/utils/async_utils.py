from typing import Callable
import asyncio
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor

GENERAL_TIMEOUT: int = 15
EXECUTOR = ThreadPoolExecutor()

async def call_sync_from_async(fn: Callable, *args, **kwargs):
    loop = asyncio.get_event_loop()
    coro = loop.run_in_executor(None, lambda: fn(*args, **kwargs))
    result = await coro
    return result

def call_async_from_sync(
    corofn: Callable, timeout: float = GENERAL_TIMEOUT, *args, **kwargs
):
    if corofn is None:
        raise ValueError('corofn is None')
    if not asyncio.iscoroutinefunction(corofn):
        raise ValueError('corofn is not a coroutine function')

    async def arun():
        coro = corofn(*args, **kwargs)
        result = await coro
        return result

    def run():
        return asyncio.run(arun())

    if getattr(EXECUTOR, 'shutdown', False):
        result = run()
        return result

    future = EXECUTOR.submit(run)
    futures.wait([future], timeout=timeout or None)
    result = future.result()
    return result    