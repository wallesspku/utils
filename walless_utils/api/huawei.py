from collections import defaultdict
import logging

logger = logging.getLogger('walless')


class Huawei:
    def __init__(self, hw_cfg):
        self.hw_cfg = hw_cfg
        from huaweicloudsdkcore.auth.credentials import BasicCredentials
        basic_cre = BasicCredentials(hw_cfg['ak'], hw_cfg['sk'], hw_cfg['project_id'])
        from huaweicloudsdkdns.v2 import DnsClient
        self.client = DnsClient. \
            new_builder(). \
            with_credentials(basic_cre). \
            with_endpoint('dns.ap-southeast-1.myhuaweicloud.com'). \
            build()
        self.line_ids = ['Jiaoyuwang', 'default_view']

        self.all_records = dict()

    def list_huawei(self):
        from huaweicloudsdkdns.v2 import ListRecordSetsWithLineRequest, DeleteRecordSetsRequest
        if self.all_records:
            return self.all_records
        all_records = defaultdict(list)
        for li in self.line_ids:
            list_req = ListRecordSetsWithLineRequest(line_id=li)
            line_records = self.client.list_record_sets_with_line(list_req).to_dict()
            for rec in line_records['recordsets']:
                all_records[rec['name']].append(rec)
        self.all_records = dict(all_records)
        return self.all_records
    
    def add_record_set(self, domain, line, records):
        from huaweicloudsdkdns.v2 import CreateRecordSetWithLineRequest
        create_req = CreateRecordSetWithLineRequest(self.hw_cfg['zone_id'], {
            'name': domain, 'type': 'CNAME', 'records': records, 'line': line
        })
        res = self.client.create_record_set_with_line(create_req)
    
    def delete_record(self, record_id):
        from huaweicloudsdkdns.v2 import DeleteRecordSetsRequest
        req = DeleteRecordSetsRequest(zone_id=self.hw_cfg['zone_id'], recordset_id=record_id)
        res = self.client.delete_record_sets(req)
    
    def apply_nodes(self, nodes):
        records = self.list_huawei()
        proto = 4
        for node in nodes:
            key = node.urls(proto)+'.'
            if key in records:
                for rec in records[key]:
                    if rec['line'] in node.dns[proto].cname:
                        logger.error(
                            "Duplicate DNS CNAME record found for %s in line %s. Deleting it now.", 
                            key, rec['line']
                        )
                        self.delete_record(rec['id'])
                    else:
                        node.dns[proto].cname[rec['line']] = rec
