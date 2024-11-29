import time
from threading import Lock, Thread
import logging
from copy import deepcopy

from ..database import DBCommunicator

logger = logging.getLogger('walless')


class UserPool:
    """
    It fetches user list from the database and save it as a local cache.
    It updates the list on-demand (instead of pulling everything every time).
    """
    def __init__(self, enable_only=True, db=None, min_gap=60):
        self.id2user = dict()
        self.email2user = dict()
        self.last_update = 100
        self.last_pull = 100
        self.min_gap = min_gap
        self.enable_only = enable_only
        self.db: DBCommunicator = db
        self.pool_lock = Lock()
        self.pull_lock = Lock()
    
    def _pull(self, blocking):
        if not self.pull_lock.acquire(blocking=blocking):
            return
        try:
            logger.debug(f'Pulling users with {blocking=}')
            since = time.time()
            for u in self.db.all_users(self.enable_only, int(self.last_update)):
                self.add_or_update_user(u)
            self.last_update = time.time() - 30
            logger.debug(f'User pull done. Time cose: {time.time() - since:.2f}s.')
        finally:
            self.pull_lock.release()

    def pull(self, force=False):
        with self.pool_lock:
            if len(self.email2user) == 0 or force:
                # pull with blocking
                self._pull(blocking=True)
                self.last_pull = time.time()
                return

            if time.time() - self.last_update < self.min_gap:
                return

            # pull without blocking
            self.last_pull = time.time()
            th = Thread(target=self._pull, args=(False,))
            th.start()

    def add_or_update_user(self, user):
        if user.user_id in self.id2user:
            self.id2user.pop(user.user_id)
        if user.email in self.email2user:
            self.email2user.pop(user.email)
        if not user.enable and self.enable_only:
            return
        self.id2user[user.user_id] = user
        self.email2user[user.email] = user

    def pull_one_user(self, email, force=False):
        if email in self.email2user and not force and (time.time() - self.email2user[email].last_change) < self.min_gap:
            return
        with self.pool_lock:
            user = self.db.get_one_user_by_email(email)
            if user is None:
                return
            self.add_or_update_user(user)

    def all_users(self, pull=True):
        if pull or len(self.id2user) == 0:
            self.pull()
        # return a copy to prevent in-place modification
        return deepcopy(list(self.id2user.values()))
