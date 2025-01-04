import os
from typing import Optional, Dict, Any
import logging
from pathlib import Path

from .abs_setup import AbstractSetup


DOMAINS = dict()
URL_TEMPLATE = dict()
BALANCE_CONFIG = dict()
cfg = dict()
logger = logging.getLogger('walless')


def load_toml(file_path: str):
    try:
        # for python 3.11
        import tomllib
        with open(file_path, 'rb') as fp:
            return tomllib.load(fp)
    except ImportError:
        # for older versions; need `pip3 install toml`
        import toml
        return toml.load(file_path)


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
            Path('~/walless.config.d').expanduser(),
            Path('/etc/walless.config.d'),
        ]
        if 'WALLESS_ROOT' in os.environ:
            config_paths.insert(0, Path(os.environ.get('WALLESS_ROOT'))/'walless.config.d')
        if 'WALLESS_CONFIG' in os.environ:
            config_paths.insert(0, Path(os.environ['WALLESS_CONFIG']))

        config_path: Path = None
        for p in config_paths:
            if p.exists():
                config_path = p
                logger.info(f'Config found at {config_path}.')
                break
        if config_path is None:
            raise ValueError("Config is not found in the following paths: %s" % '\n'.join(config_paths))

        ret = dict()
        for fp in reversed(list(filter(lambda x: x.suffix == '.toml', sorted(list(config_path.iterdir()))))):
            ret.update(load_toml(os.path.join(config_path, fp)))

        return ret


config_setup = ConfigSetup()
