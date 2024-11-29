from .abs_setup import AbstractSetup
from ..database import DBCommunicator
from .config_setup import cfg, config_setup

db: DBCommunicator = DBCommunicator({})

class DBSetup(AbstractSetup):
    def __init__(self):
        super().__init__()
        self.name = 'db'
        self.log_level = 1

    def setup(self):
        config_setup()
        if 'db' not in cfg:
            raise ValueError('DB configuration is not found in config')
        db.conn_cfgs = cfg['db']


db_setup = DBSetup()
