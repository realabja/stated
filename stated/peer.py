from dataclasses import dataclass


@dataclass
class Peer:
    name: str | None = None
    ip: str | None = None
    port: int | None = None
    host: str | None = None
    proximity: int = 0
    connection_integrity: float = 0
