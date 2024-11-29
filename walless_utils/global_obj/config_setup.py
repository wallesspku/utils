import os
from typing import Optional, Dict, Any
import logging
import yaml

from .abs_setup import AbstractSetup


DOMAINS = dict()
URL_TEMPLATE = dict()
BALANCE_CONFIG = dict()
cfg = dict()
logger = logging.getLogger('walless')


class ConfigSetup(AbstractSetup):
    def __init__(self):
        super().__init__()
        self.name = 'config'
        self.log_level = 1
    
    def setup(self):
        cfg.update(self.load_config())
        URL_TEMPLATE.update(cfg.get('url_template', {}))
        BALANCE_CONFIG.update(cfg.get('balance', {}))
        if 'subs' in cfg:
            domains = cfg['subs'].get('domains', {})
            DOMAINS.update({
                'subs': domains.get('subs'),
                'provider': domains.get('provider'),
                'profile': domains.get('profile'),
            })

    def load_config(self) -> Optional[Dict[str, Any]]:
        config_paths = [
            './walless.config.d',
            os.path.expanduser('~/.config/walless.config.d'),
            '/etc/walless.config.d',
        ]
        if 'WALLESS_ROOT' in os.environ:
            config_paths.insert(0, os.path.join(os.environ.get('WALLESS_ROOT'), '.config', 'walless.config.d'))
        if 'WALLESS_CONFIG' in os.environ:
            config_paths.insert(0, os.environ['WALLESS_CONFIG'])

        for p in config_paths:
            if os.path.exists(p):
                config_path = p
                logger.info(f'Config found at {config_path}.')
                break
        if config_path is None:
            raise ValueError("Config is not found in the following paths: %s" % '\n'.join(config_paths))

        configs = []
        for jp in reversed(list(filter(lambda x: x.endswith('.yaml'), sorted(os.listdir(config_path))))):
            with open(os.path.join(config_path, jp)) as fp:
                configs.append(yaml.safe_load(fp))

        ret = dict()
        for config in configs:
            ret.update(config)
        return ret


config_setup = ConfigSetup()
