from typing import List, Tuple, Any
import time
import logging

from threading import Lock, Thread
from walless_utils.database import DBCommunicator

logger = logging.getLogger('walless')


class EditReservior:
    """
    Cache for SQL edit operations.
    """
    def __init__(
        self, sql: str, db: DBCommunicator = None,
        cache_size: int = 128, cache_time: int = 300, disabled=False,
        block: bool = False, cursor=None,
    ):
        # time unit: seconds
        self.cache_lock = Lock()
        self.commit_lock = Lock()
        self.cache_size, self.cache_time = cache_size, cache_time
        self.sql = sql
        # if cursor is set, will use this connection to commit
        self.db = db
        self.cursor = cursor
        # if set as True, will wait for the previous commit to finish
        # otherwise will discard the commit
        self.block = block
        self.last_commit = time.time()
        self.cache: List[Tuple[Any, ...]] = list()
        self.disabled = disabled
    
    def _commit(self, args: List[Tuple[Any, ...]]):
        if len(args) == 0:
            return
        if self.commit_lock.locked() and not self.block:
            logger.warning(
                f'Last commit of "{self.sql}" is not done yet. '
                'Discard this commit.'
            )
            return
        with self.commit_lock:
            if self.cursor is not None:
                DBCommunicator.execute_cursor(
                    cursor=self.cursor, sql=self.sql, args=args, bulk=True, query=False,
                )
            else:
                self.db.execute(sql=self.sql, args=args, bulk=True, query=False)
    
    def flush(self):
        if self.disabled:
            return
        if self.block:
            self._commit(self.cache)
        else:
            th = Thread(target=self._commit, args=(self.cache,))
            th.start()
        self.cache = list()
        self.last_commit = time.time()
    
    def add(self, args):
        if self.disabled:
            return
        with self.cache_lock:
            self.cache.append(args)
            oversized = (self.cache_size <= len(self.cache))
            time_passed = (self.cache_time <= time.time() - self.last_commit)
            if oversized or time_passed:
                self.flush()
