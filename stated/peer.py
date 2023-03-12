from dataclasses import dataclass


@dataclass
class Peer:
    ip: str
    port: int
    host: str
    proximity: int
