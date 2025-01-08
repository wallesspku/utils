import logging
import time

from .logger_setup import logger_setup
from .config_setup import config_setup
from .db_setup import db_setup
from .pool_setup import pool_setup, node_pool, user_pool
from .abs_setup import AbstractSetup

logger = logging.getLogger('walless')


class EverythingSetup(AbstractSetup):
    def __init__(self):
        super().__init__()
        self.name = 'everything'
        self.log_level = logging.INFO

    def setup(
        self, log_paths=None, user_pool_kwargs=None, node_pool_kwargs=None,
        pull_node=False, pull_user=False, add_notifier=False,
    ):
        logger_setup(log_paths=log_paths)
        config_setup()
        db_setup()
        pool_setup(user_pool_kwargs=user_pool_kwargs, node_pool_kwargs=node_pool_kwargs)
        if pull_node:
            logger.info('Pulling node pool...')
            since = time.time()
            node_pool.pull(force=True)
            logger.info(f'Node pool pull finished in {time.time()-since:.2f}s.')
        if pull_user:
            logger.info('Pulling user pool...')
            since = time.time()
            user_pool.pull(force=True)
            logger.info(f'User pool pull finished in {time.time()-since:.2f}s.')
        if add_notifier:
            logger_setup.add_notifier()


setup_everything = EverythingSetup()
