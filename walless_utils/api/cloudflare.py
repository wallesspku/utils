import logging

from ..global_obj.config_setup import cfg

logger = logging.getLogger('walless')


class Cloudflare:
    def __init__(self):
        from cloudflare import Cloudflare as CFApi
        self.cf = CFApi(**cfg['cloudflare']['auth'])
        self.zone_ids = cfg['cloudflare']['zones']
        self.dns, self.zones = dict(), list()

    def load_dns(self):
        if self.dns:
            return self.dns, self.zones
        for zid in self.zone_ids:
            zone = self.cf.zones.get(zone_id=zid)
            self.zones.append(zone)
            for dns in self.cf.dns.records.list(zone_id=zid):
                if dns.type not in ['A', 'AAAA']:
                    continue
                if dns.name in self.dns:
                    logger.warning(f'Duplicate DNS: {dns.name}.')
                self.dns[dns.name] = dns
        return self.dns, self.zones

    def update_dns(self, domain, content):
        zone_id = None
        for zone in self.zones:
            if domain.endswith(zone.name):
                zone_id = zone.id
                break
        if zone_id is None:
            logger.error(f'Fail to modify DNS {domain}')
            return

        if ':' in content:
            record_type = 'AAAA'
        else:
            record_type = 'A'

        kwargs = dict(name=domain, type=record_type, content=content, zone_id=zone_id, ttl=1, proxied=False)
        if domain in self.dns:
            r = self.cf.dns.records.update(self.dns[domain].id, **kwargs)
        else:
            r = self.cf.dns.records.create(**kwargs)
        self.dns[domain] = r
    
    def apply_nodes(self, nodes):
        # pull DNS records and apply them to nodes by modifying their `dns` field
        self.load_dns()
        for node in nodes:
            for proto in [4, 6]:
                if node.real_urls(proto) in self.dns:
                    node.dns[proto].ip = self.dns[node.real_urls(proto)].content
