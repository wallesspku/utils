import time
from threading import Lock, Thread
from typing import List
from copy import deepcopy
import logging

from ..database import DBCommunicator
from .node import Node

logger = logging.getLogger('walless')


class NodePool:
    """
    It fetches node list from the database and save it as a local cache.
    It updates the list on-demand (instead of pulling everything every time).
    """
    def __init__(self, db=None, relay: bool = True, min_gap=60):
        self.nodes = []
        self.last_update = 100
        self.min_gap = min_gap
        self.relay = relay
        self.db: DBCommunicator = db
        self.pool_lock = Lock()
        self.pull_lock = Lock()
    
    def _pull(self, blocking):
        if not self.pull_lock.acquire(blocking=blocking):
            return
        try:
            logger.debug(f'Pulling nodes with {blocking=}')
            all_nodes = self.db.all_servers(self.relay)
            self.nodes = all_nodes
        finally:
            self.pull_lock.release()

    def pull(self, force=False):
        with self.pool_lock:
            if len(self.nodes) == 0 or force:
                # if the list is empty, pull it immediately and block the main thread
                self._pull(blocking=True)
                self.last_update = time.time()
                return

            if time.time() - self.last_update < self.min_gap:
                return

            th = Thread(target=self._pull, args=(False,))
            th.start()
            self.last_update = time.time()

    def all_nodes(self, pull=True) -> List[Node]:
        if pull or len(self.nodes) == 0:
            self.pull()
        # return a duplicate to prevent in-place modification
        return deepcopy(self.nodes)
