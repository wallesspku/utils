import random
import logging

from .global_obj.db_setup import db
from .global_obj.config_setup import cfg
from .network_status import NetworkStatus

logger = logging.getLogger('walless')


def whoami(ns: NetworkStatus = None, debug: bool = False):
    # if debug is True, will randomly pick up a node
    my_uuid = cfg.get('uuid')
    if my_uuid is not None:
        logger.warning('My UUID is configured to %s', my_uuid)
    if ns is None:
        ns = NetworkStatus()
        ns.wait_for_network()

    nodes = db.all_servers(get_mix=True, get_relays=True)

    # uuid is priority 1
    if my_uuid is not None:
        for node in nodes:
            if node.uuid == my_uuid:
                return node

    # ipv4 is priority 2
    for node in nodes:
        if node.ip(4) is not None and node.ip(4) == ns.ipv4:
            return node

    if debug:
        return random.choice(nodes)
