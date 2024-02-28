import copy
from logging import Logger
from typing import List

import pytest
from pytest import fixture

from stated.finder import StaticFinder
from stated.peer import Peer


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

        # finder = StaticFinder(peers=[Peer(host="localhost", port=8000)])
        async with Agent() as agent:
            await sleep(4)


@pytest.mark.asyncio
class TestTwoAgents:
    async def test(self, logger: Logger):
        start_agent_in_subprocess()


def run_local_agent(port: int, for_seconds: int, ports_for_peers: list[int]):
    from asyncio import run
    from asyncio import sleep

    from stated import Agent
    from stated.finder import StaticFinder

    finder = StaticFinder(peers=[Peer(host="localhost", port=port) for port in ports_for_peers])

    async def main():
        async with Agent(agent_name=f"agent:{port}", listen_port=port, finders=[finder]) as agent:
            await sleep(for_seconds)

    run(main())


def start_agent_in_subprocess():
    from multiprocessing import Process

    _ports = [8001, 8002]

    ps: List[Process] = []
    for agent_port in _ports:
        peer_ports = copy.deepcopy(_ports)
        peer_ports.remove(agent_port)
        print(f"running agent on port {agent_port} with peers {peer_ports}")
        agent_process = Process(target=run_local_agent, args=(agent_port, 10, peer_ports))
        agent_process.start()
        ps.append(agent_process)

    for i in ps:
        i.join()
