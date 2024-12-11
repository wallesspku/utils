from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass, field
from datetime import date, timedelta

from ..global_obj.config_setup import URL_TEMPLATE


@dataclass
class AbstractNode:
    def __post_init__(self):
        self.tag = tuple() if self.tag is None else tuple(self.tag.split(':'))
        self.properties = tuple() if self.properties is None else tuple(self.properties.split(':'))

    @classmethod
    def from_list(cls, items):
        return cls(*items)

    def can_be_used_by(self, user_tag, protocol: Optional[int] = None) -> bool:
        if protocol is not None:
            if protocol == 4 and self.ipv4 is None:
                return False
            if protocol == 6 and self.ipv6 is None:
                return False
            if not any(tag in self.tag for tag in ['gfw', 'cn']):
                return False
        if not set(self.tag).issubset(user_tag):
            return False
        return True
    

@dataclass
class Relay(AbstractNode):
    relay_id: int
    name: str
    tunnel: Optional[str]
    tag: Tuple[str]
    properties: Tuple[str]
    hidden: bool
    source_id: int
    target_id: int
    port: int
    source: "Node" = None
    target: "Node" = None

    def __repr__(self):
        return f'<Relay from {self.source} to {self.target}>'

    def ip(self, proto):
        return self.source.ip(proto)

    def port_range(self):
        start = self.port - self.port % 100
        return start, start + 100
    
    @property
    def ipv4(self):
        return self.source.ipv4
    
    @property
    def ipv6(self):
        return self.source.ipv6


class DNSRecord:
    def __init__(self):
        # A/AAAA record on Cloudflare
        self.ip = None
        # CNAME record on Huawei
        self.cname: Dict[str, Optional[str]] = {'edu': None, 'out': None}

    def read_huawei_record(self, records):
        for rec in records:
            if rec['line'] == 'Jiaoyuwang':
                self.cname['edu'] = rec['records'][0][:-1]
            if rec['line'] == 'default_view':
                self.cname['default'] = rec['records'][0][:-1]


@dataclass
class Node(AbstractNode):
    node_id: int
    uuid: str
    deleted: bool
    hidden: bool
    name: str
    weight: float
    tag: Tuple[str]
    ipv4: str
    ipv6: str
    port: int
    properties: Tuple[str]
    remarks: Optional[str]
    idc: Optional[str]
    upload: int
    download: int
    traffic_reset_day: int
    traffic_limit: Optional[int]
    relay_in: List[Relay] = field(default_factory=list)
    relay_out: List[Relay] = field(default_factory=list)
    # a map from scope ("edu" or "default") to target node
    # if the scope is missing (default), no mix is applied
    mix: Dict[str, "Node"] = field(default_factory=dict)

    def __post_init__(self):
        super().__post_init__()
        self.weight: float = float(self.weight)
        # self.dns should be retrieved from API (cloudflare and huaweicloud)
        self.dns: Dict[int, DNSRecord] = {4: DNSRecord(), 6: DNSRecord()}

    def ip(self, proto, value=None):
        assert proto in [4, 6]
        if value is None:
            return getattr(self, 'ipv'+str(proto))
        setattr(self, 'ipv'+str(proto), value)

    def urls(self, proto):
        # proto is 4 or 6
        return URL_TEMPLATE['mix'].replace('#', str(proto)).replace('$', str(self.node_id))

    def real_urls(self, proto):
        return URL_TEMPLATE['real'].replace('#', str(proto)).replace('$', str(self.node_id))

    def __repr__(self):
        return f'<Node {self.node_id}: {self.name}>'

    @staticmethod
    def port_range():
        return 4400, 4500
    
    def __hash__(self):
        return hash(self.uuid)

    def last_reset_day(self) -> date:
        day = self.traffic_reset_day if self.traffic_reset_day is not None else 1
        today = date.today()
        # Check if the reset day has already passed this month
        if today.day >= day:
            last_reset = date(today.year, today.month, day)
        else:
            # If not, go to the previous month
            last_month = today.replace(day=1) - timedelta(days=1)
            # Handle February and other months with fewer days
            try:
                last_reset = last_month.replace(day=day)
            except ValueError:
                # If the day is out of range for the month, set to the last day of the month
                last_reset = last_month
        return last_reset

    def next_reset_day(self) -> date:
        day = self.traffic_reset_day if self.traffic_reset_day is not None else 1
        today = date.today()
        # Check if the reset day is yet to come this month
        if today.day < day:
            next_reset = date(today.year, today.month, day)
        else:
            # If the reset day has already passed, go to the next month
            next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
            # Handle months with fewer days
            try:
                next_reset = next_month.replace(day=day)
            except ValueError:
                # If the day is out of range for the month, set to the last day of the month
                next_reset = next_month.replace(day=1) - timedelta(days=1)
        return next_reset


def link_relays(nodes: List[Node], relays: List[Relay]):
    uuid2node: Dict[int, Node] = {n.uuid: n for n in nodes}
    for relay in relays:
        if relay.source_id in uuid2node and relay.target_id in uuid2node:
            relay.source, relay.target = uuid2node[relay.source_id], uuid2node[relay.target_id]
            relay.source.relay_out.append(relay)
            relay.target.relay_in.append(relay)


@dataclass
class Mix:
    source_uuid: str
    target_uuid: str
    # scope can either be "default" or "edu"
    scope: str
    
    @classmethod
    def from_list(cls, li):
        return cls(*li)


def link_mixes(nodes: List[Node], mixes: List[Mix]):
    uuid2nodes = {n.uuid: n for n in nodes}
    for mix in mixes:
        if mix.source_uuid in uuid2nodes and mix.target_uuid in uuid2nodes:
            uuid2nodes[mix.source_uuid].mix[mix.scope] = uuid2nodes[mix.target_uuid]
