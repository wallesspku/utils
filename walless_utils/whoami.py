import random
import time
import logging

from .global_obj.db_setup import db
from .global_obj.config_setup import cfg
from .network_status import NetworkStatus

logger = logging.getLogger('walless')


def whoami(ns: NetworkStatus = None, debug: bool = False):
    """
    Identify the current. It will try to identify the current node by the following order:
    1. If the UUID is configured, it will return the node with the UUID.
    2. If the IPv4 is the same as the current node, it will return the node with the same IPv4.
    3. If the debug is True, it will randomly pick up a node.
    """
    my_uuid = cfg.get('uuid')
    if my_uuid is not None:
        logger.warning('My UUID is configured to %s', my_uuid)
    if ns is None:
        ns = NetworkStatus()
        ns.wait_for_network()

    retries = 20
    while retries > 0:
        try:
            nodes = db.all_servers(get_mix=False, get_relays=True)
            break
        except:
            retries -= 1
            time.sleep(60)

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
