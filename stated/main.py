from __future__ import annotations

import datetime
from asyncio import Queue
from asyncio import create_task
from asyncio import sleep
from logging import getLogger
from typing import List

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from stated.finder import Finder
from stated.peer import Peer

logger = getLogger(__name__)

logger.debug("[stated]: imported")


class Agent:
    def __init__(self, agent_name: str | None = None):
        logger.info("[stated]: initializing stated agent")
        self.blocks = []
        self.scan_interval = 1
        self.agent_name = agent_name or self.generate_agent_name()
        self.peers: List[Peer] = list()
        self.finders: List[Finder] = list()
        self.init_certificate()

    def init_certificate(self):
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())

        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, self.agent_name)])
        self.public_key = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)
            .public_key(self.private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=100000))
            .sign(self.private_key, hashes.SHA256())
        )

    def generate_agent_name(self):
        return "stated-agent-1"

    async def start(self) -> Agent:
        self.task_agent_finders = create_task(self.find_peers_task())
        return self

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return await self.ensure_teardown()

    async def flush_backlog(self):
        logger.info("[stated]: flushing backlog")

    async def ensure_teardown(self):
        await self.flush_backlog()
        self.task_agent_finders.cancel()
        return self

    async def find_peers(self):
        logger.info("[stated]: agent finder started")

    async def find_peers_task(self):
        while True:
            try:
                await self.find_peers()
                await sleep(self.scan_interval)
            except Exception as e:
                logger.error(f"[stated]: error finding other agents: {e}")
