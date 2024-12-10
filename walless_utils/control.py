from typing import *
import logging
import os

from .api import Huawei, Cloudflare
from .global_obj.global_setup import setup_everything
from .global_obj.db_setup import db
from .global_obj.config_setup import cfg

logger = logging.getLogger('walless')


class Controller:
    def __init__(self):
        setup_everything(log_paths=[os.path.expanduser('~/.var/log/walless_cron.log')])
        self.huawei = Huawei(cfg['huawei'])
        self.cloudflare = Cloudflare(cfg['cloudflare'])
        self.cf_loaded = self.hw_loaded = False
        self.nodes = db.all_servers(get_mix=True, get_relays=True, include_delete=False)

    def _load_cf(self):
        if self.cf_loaded:
            return
        dns, _ = self.cloudflare.load_dns()
        for node in self.nodes:
            for proto in [4, 6]:
                if node.real_urls(proto) in dns:
                    node.dns[proto].ip = dns[node.real_urls(proto)].content
        self.cf_loaded = True

    def _load_huawei(self):
        if self.hw_loaded:
            return
        records = self.huawei.list_huawei()
        for node in self.nodes:
            for proto in [4, 6]:
                if node.urls(proto)+'.' in records:
                    node.dns[proto].read_huawei_record(records[node.urls(proto)+'.'])
        self.hw_loaded = True

    def sync_ip(self):
        # apply the ipv4/ipv6 records on DB to cloudflare, if mismatched
        self._load_cf()
        for node in self.nodes:
            for proto in [4, 6]:
                if node.ip(proto) is not None and node.dns[proto].ip != node.ip(proto):
                    logger.warning(f'The IPv{proto} of {node.name} mismatches. Setting its DNS records to {node.ip(proto)}.')
                    self.cloudflare.update_dns(node.real_urls(proto), node.ip(proto))

    def sync_mix(self):
        # apply the mix settings on DB to huawei cloud, if mismatched
        # only ipv4 (A record) will be mapped
        self._load_huawei()
        for node in self.nodes:
            for scope in ['default', 'edu']:
                if node.ip(4) is None:
                    continue
                if scope in node.mix:
                    db_cname = node.mix[scope].real_urls(4)
                else:
                    db_cname = node.real_urls(4)
                if scope not in node.dns[4].cname or node.dns[4].cname[scope] != db_cname:
                    logger.warning(f'{scope} CNAME for {node.name} is missing. It should be {db_cname}. Modifying it now.')
                    self.huawei.add_mod_cname(node.urls(4), **{scope+'_cname': db_cname})
