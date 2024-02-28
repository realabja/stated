from typing import List

from stated.peer import Peer


class BaseFinder(object):
    def __init__(self) -> None:
        self.all_peers: List[Peer] = []

    async def get_all_peers(self) -> List[Peer]:
        raise NotImplementedError("Subclasses must implement this method")
        return self.all_peers


class StaticFinder(BaseFinder):
    def __init__(self, peers: List[Peer]) -> None:
        self.all_peers = peers

    async def get_all_peers(self) -> List[Peer]:
        return self.all_peers
