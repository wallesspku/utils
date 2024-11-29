import logging

from .abs_setup import AbstractSetup
from ..objects.user_pool import UserPool
from ..objects.node_pool import NodePool
from .config_setup import cfg, config_setup
from .db_setup import db, db_setup

logger = logging.getLogger('walless')
user_pool: UserPool = UserPool()
node_pool: NodePool = NodePool()


class PoolSetup(AbstractSetup):
    def __init__(self):
        super().__init__()
        self.log_level = 1
        self.name = 'pool'

    def setup(self, user_pool_kwargs=None, node_pool_kwargs=None):
        config_setup()
        db_setup()

        up_kwargs = {'db': db}
        if user_pool_kwargs:
            up_kwargs.update(user_pool_kwargs)
        for key, value in up_kwargs.items():
            setattr(user_pool, key, value)

        np_kwargs = {'db': db, 'cfg': cfg}
        if node_pool_kwargs:
            np_kwargs.update(node_pool_kwargs)
        for key, value in np_kwargs.items():
            setattr(node_pool, key, value)


pool_setup = PoolSetup()
