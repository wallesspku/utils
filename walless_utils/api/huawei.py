from collections import defaultdict


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
        all_records = defaultdict(list)
        for li in self.line_ids:
            list_req = ListRecordSetsWithLineRequest(line_id=li)
            line_records = self.client.list_record_sets_with_line(list_req).to_dict()
            for rec in line_records['recordsets']:
                all_records[rec['name']].append(rec)
        self.all_records = dict(all_records)
        return self.all_records
    
    def add_mod_cname(self, domain, edu_cname=None, default_cname=None):
        if len(self.all_records) == 0:
            self.list_huawei()
        domain = domain+'.'
        from huaweicloudsdkdns.v2 import UpdateRecordSetRequest, CreateRecordSetWithLineRequest
        edu_rec = out_rec = None
        if domain in self.all_records:
            rec_list = self.all_records[domain]
            for rec in rec_list:
                if rec['line'] == 'Jiaoyuwang':
                    edu_rec = rec
                if rec['line'] == 'default_view':
                    out_rec = rec

        for line_id, cname, rec in zip(self.line_ids, [edu_cname, default_cname], [edu_rec, out_rec]):
            if cname is None:
                continue

            if rec is not None:
                if rec['records'][0] == cname:
                    continue
                upd_req = UpdateRecordSetRequest(self.hw_cfg['zone_id'], rec['id'], {
                    'name': domain, 'type': 'CNAME', 'records': [cname+'.']
                })
                self.client.update_record_set(upd_req)
            else:
                create_req = CreateRecordSetWithLineRequest(self.hw_cfg['zone_id'], {
                    'name': domain, 'type': 'CNAME', 'records': [cname+'.'], 'line': line_id
                })
                self.client.create_record_set_with_line(create_req)

    def clean(self):
        from huaweicloudsdkdns.v2 import DeleteRecordSetsRequest, DeleteRecordSetRequest
        if len(self.all_records) == 0:
            self.list_huawei()
        for rec_name, recs in self.all_records.items():
            if '.0.' in rec_name:
                for rec in recs:
                    req = DeleteRecordSetsRequest(zone_id=self.hw_cfg['zone_id'], recordset_id=rec['id'])
                    res = self.client.delete_record_sets(req)
            if len(recs) > 2:
                lines = set()
                for rec in recs:
                    if rec['line'] in lines:
                        req = DeleteRecordSetsRequest(zone_id=self.hw_cfg['zone_id'], recordset_id=rec['id'])
                        res = self.client.delete_record_sets(req)
                    else:
                        lines.add(rec['line'])
