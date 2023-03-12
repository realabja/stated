from fastapi import FastAPI

from stated.peer import Peer


class Finder(object):
    def __init__(self) -> None:
        ...

    def next_peer(self, last_found_peer: Peer | None = None):
        ...
