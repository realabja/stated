from __future__ import annotations

import datetime
import socket
from asyncio import AbstractEventLoop
from asyncio import StreamReader
from asyncio import StreamWriter
from asyncio import create_task
from asyncio import get_event_loop
from asyncio import open_connection
from asyncio import sleep
from asyncio import start_server
from asyncio import wait_for
from logging import getLogger
from typing import Dict
from typing import List
from typing import Literal
from typing import Tuple

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from stated.finder import BaseFinder
from stated.peer import Peer
from stated.utils import schedule

logger = getLogger(__name__)
logger.debug("[stated]: importing stated agent module")

MessageType = str
Acknowledgement = Tuple[Literal["ack", "nack"] | str, str]


class Agent:
    def __init__(
        self,
        agent_name: str | None = None,
        finders: List[BaseFinder] = [],
        listen_port: int = 9999,
        bind_ip: str = "127.0.0.1",
    ):
        logger.info(f"[stated]: initializing stated agent instance {agent_name}")
        self.max_op_wait = 10
        # self.blocks = []
        self.port = listen_port
        self.bind_ip = bind_ip
        self.full_scan_for_peer_interval = 10
        self.agent_name = agent_name or self.generate_agent_name()
        self.peers: List[Peer] = list()
        self.connected_peers: List[Peer] = list()
        self.replication_factor = 2
        self.finders: List[BaseFinder] = finders
        self.agent_state = "initialization"
        self.kv_store: Dict[str, str] = {}

    async def put(self, key, value):
        if not self.agent_state == "running":
            await wait_for(self.is_running(), self.max_op_wait)
        logger.debug(f"[stated]: putting {key} in storage")
        await self.put_in_peers(key, value)
        self.kv_store[key] = value

    async def on_put(self, message: str, writer: StreamWriter):
        logger.info(f"[stated]: received put request {message}")
        key, value = message.split(":")
        if key not in self.kv_store:
            self.kv_store[key] = value
            writer.write("ack".encode())
        else:
            writer.write("nack: conflict".encode())

    async def is_running(self):
        while True:
            await sleep(1)
            if len(self.connected_peers) > self.replication_factor - 1:
                break

    async def get(self, key):
        return self.kv_store.get(key)

    async def put_in_peers(self, key, value):
        for peer in self.peers:
            await self.put_remote(peer, key, value)

    async def get_from_peers(self, key):
        for peer in self.peers:
            await self.get_remote(peer, key)

    @staticmethod
    async def put_remote(peer: Peer, key, value):
        await Agent.send_op(peer, "put", data=f"{key}:{value}")

    def generate_agent_name(self):
        return "stated-agent-1"

    async def start(self) -> Agent:
        await self.start_server()
        self.task_server = create_task(self.server.serve_forever())
        self.task_agent_finders = create_task(schedule(self.find_peers_task, self.full_scan_for_peer_interval))
        self.task_ping_peers = create_task(schedule(self.ping_peers, 5))
        return self

    async def __aenter__(self):
        await self.start()
        return self

    @staticmethod
    def parse_message(message: str) -> tuple[MessageType, str]:
        message_type, message = message.split(",", 1)
        return message_type, message

    @staticmethod
    def ping_response(message: str) -> str:
        return f"ack, message: {message} received"

    async def message_handler(self, message_type: str, message: str, writer: StreamWriter, addr: tuple[str, int]):
        logger.debug(f"[stated]: incoming {message_type}, from {addr[0]}:{addr[1]}")
        match message_type:
            case "op:ping":
                writer.write(self.ping_response(message).encode())
            case "op:put":
                await self.on_put(message, writer)
            case _:
                logger.warning(f"[stated]: unknown message type {message_type}")

    async def incoming_handler(self, reader: StreamReader, writer: StreamWriter):
        data = await reader.read(-1)
        message = data.decode()
        addr = writer.get_extra_info("peername")
        message_type, message = self.parse_message(message)
        await self.message_handler(message_type, message, writer, addr)
        writer.write_eof()
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def start_server(self):

        server = await start_server(self.incoming_handler, self.bind_ip, self.port)
        address = [sock.getsockname() for sock in server.sockets][0]
        await server.__aenter__()
        logger.info(f"[stated]: listening for connections: {address[0]}:{address[1]}")

        self.server = server

    async def add_peer(self, peer: Peer):
        self.peers.append(peer)
        await self.check_connection_to_peers(peer)

    async def __aexit__(self, exc_type, exc, tb):
        await self.server.__aexit__()
        if exc_type:
            logger.error(f"[stated]: traceback {exc_type} {exc} {tb}")
            logger.error(f"[stated]: agent {self.agent_name} exited with error {exc_type}")
        return await self.ensure_teardown()

    async def flush_backlog(self):
        logger.info("[stated]: flushing backlog")
        await sleep(3)

    async def ensure_teardown(self):
        await self.flush_backlog()
        self.task_agent_finders.cancel()
        return self

    async def find_peers(self):
        logger.info("[stated]: agent finder started")

    async def find_peers_task(self):
        # logger.debug("[stated]: actively looking for peers")
        for i in self.finders:
            all_peers = await i.get_all_peers()
            for peer in all_peers:
                if peer not in self.peers:
                    await self.add_peer(peer)
                    logger.info(f"[stated]: found new peer {peer}")

    async def check_connection_to_peers(self, peer: Peer):
        logger.info(f"[stated]: connecting to peer {peer.name}")
        peer.connection_integrity = 1

    @staticmethod
    async def dns_peer(peer: Peer, loop: AbstractEventLoop = get_event_loop()):
        ip = await loop.getaddrinfo(peer.host, peer.port)
        _ip = ip[0][4][0]
        peer.ip = _ip

    async def ping_peers(self):
        loop = get_event_loop()
        # logger.debug("[stated]: pinging peers")
        for peer in self.peers:
            try:
                await self.dns_peer(peer, loop)
                # logger.debug(f"[stated]: pinging peer {peer.name} at {peer.host}:{peer.port}")
                await self.send_op(peer, "ping", extra=f"agent:{self.agent_name}, state:{self.agent_state}")
                if peer not in self.connected_peers:
                    self.connected_peers.append(peer)
            except Exception as e:
                logger.warning(f"[stated]: error pinging peer {peer.name} at {peer.host}:{peer.port} {e}")

    @staticmethod
    async def send_op(
        peer: Peer,
        op: str,
        data: str | None = None,
        extra: str | None = None,
    ) -> Acknowledgement:
        reader, writer = await open_connection(peer.ip, peer.port)
        to_send = f"op:{op}"
        if data:
            to_send += f", data:{data}"
        if extra:
            to_send += f", {extra}"
        # in future we will chunk the data into smaller parts
        writer.write(to_send.encode())
        writer.write_eof()
        await writer.drain()
        out = await reader.read(-1)
        writer.close()
        await writer.wait_closed()

        _out = out.decode()
        _ack_and_extra = _out.split(",", maxsplit=1)
        ack = _ack_and_extra[0]
        extra = ""
        if len(_ack_and_extra) > 1:
            extra = _ack_and_extra[1]
        return ack, extra

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
