from asyncio import sleep
from logging import getLogger
from typing import Any
from typing import Awaitable
from typing import Callable

logger = getLogger(__name__)


async def schedule(task: Callable[[], Awaitable[Any]], every_seconds: int):
    logger.info(f"[schedule]: scheduling task '{task.__name__}' to run {every_seconds} seconds")
    while True:
        try:
            await task()
        except Exception as e:
            logger.warning(f"[schedule]: task '{task.__name__}' failed: \n  {e}")
        await sleep(every_seconds)
