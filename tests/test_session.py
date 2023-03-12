from logging import Logger

import pytest
from pytest import fixture


@fixture(autouse=True)
def logger():
    import logging

    from rich.logging import RichHandler

    FORMAT = "%(message)s"
    logging.basicConfig(level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])

    _logger = logging.getLogger("rich")
    _logger.info("[tests]: session started")
    yield _logger
    _logger.info("[tests]: session has ended")


@pytest.mark.asyncio
class TestBasic:
    async def test_simple(self, logger: Logger):
        from asyncio import sleep

        from stated import Agent

        async with Agent() as agent:
            await sleep(4)
