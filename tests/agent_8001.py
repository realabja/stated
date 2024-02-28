import logging
from asyncio import run
from asyncio import sleep

from rich.logging import RichHandler

from stated import Agent
from stated.finder import StaticFinder
from stated.peer import Peer

FORMAT = "%(message)s"
logging.basicConfig(level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])


def run_local_agent(port: int, for_seconds: int, ports_for_peers: list[int]):

    finder = StaticFinder(peers=[Peer(host="localhost", port=port) for port in ports_for_peers])

    async def main():
        async with Agent(agent_name=f"agent:{port}", listen_port=port, finders=[finder]) as agent:
            await sleep(for_seconds)

    run(main())


if __name__ == "__main__":
    run_local_agent(8001, 1000, [8002])
