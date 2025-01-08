from threading import Lock
import time
import logging

logger = logging.getLogger('walless')


class AbstractSetup:
    # it supplies lock and common setup methods
    def __init__(self):
        self._lock = Lock()
        self._setup_done = False
        self.name = 'abstract'
        self.log_level = logging.INFO

    @property
    def setup_done(self):
        return self._setup_done

    def __call__(self, **kwargs):
        if self._setup_done:
            return
        with self._lock:
            if self._setup_done:
                return
            logger.log(self.log_level, f'Setting up {self.name}.')
            since = time.time()
            self.setup(**kwargs)
            logger.log(self.log_level, f'{self.name} setup finished in {time.time()-since:.2f}s.')
            self._setup_done = True

    def setup(self):
        raise NotImplementedError
