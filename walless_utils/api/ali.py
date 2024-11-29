from typing import *
from dataclasses import dataclass
import json
from datetime import datetime, timezone, timedelta
import time
import os
import logging
try:
    from alibabacloud_tea_openapi import models as open_api_models
    from alibabacloud_swas_open20200601 import models as swas_models
    from alibabacloud_swas_open20200601.client import Client
except ImportError:
    pass

logger = logging.getLogger('walless')

init2004 = 'm-j6c4ghaaduas2nom55ul'


@dataclass
class AliInstance:
    instance_id: str
    ip: str
    created_at: int
    expire: int
    status: str
    region_id: str
    remaining: Optional[int] = None


class Ali:
    region_ids = [
        'cn-hongkong',
        # 'ap-southeast-1',  # sgp
    ]
    stop_threshold = 20 * 2**30  # 20 GiB left == stop instance
    alert_threshold = 30 * 2**30  # 30 GiB left == switch to other instances

    def __init__(self, key, secret):
        self.clients = {
            rid: Client(open_api_models.Config(
                access_key_id=key,
                access_key_secret=secret,
                endpoint=f'swas.{rid}.aliyuncs.com'
            ))
            for rid in self.region_ids
        }
        self.instances: Dict[str, AliInstance] = dict()
        self.total_balance = 0

    def list_instances(self, force=False):
        if len(self.instances) > 0 and not force:
            return
        self.total_balance = 0
        for rid in self.region_ids:
            res = self.clients[rid].list_instances(swas_models.ListInstancesRequest(region_id=rid, page_size=100))
            for ins in res.body.instances:
                self.instances[ins.instance_id] = (AliInstance(
                    ins.instance_id, ins.public_ip_address,
                    int(datetime.fromisoformat(ins.creation_time[:-1]).replace(tzinfo=timezone.utc).timestamp()),
                    int(datetime.fromisoformat(ins.expired_time[:-1]).replace(tzinfo=timezone.utc).timestamp() + 15*24*3600),
                    ins.status,
                    ins.region_id
                ))
            res = self.clients[rid].list_instances_traffic_packages(swas_models.ListInstancesTrafficPackagesRequest(
                instance_ids=json.dumps(list(self.instances)), region_id=rid)
            )
            for ins in res.body.instance_traffic_package_usages:
                remains = ins.traffic_package_total - ins.traffic_used
                self.total_balance += remains // 2**30
                self.instances[ins.instance_id].remaining = remains

    @staticmethod
    def wait_until_up(ip):
        # Wait until it is up.
        while True:
            ping_ret = os.system('ping -c 1 -q -W 3 ' + ip + ' > /dev/zero')
            if ping_ret == 0:
                break
            time.sleep(1)

    def modify_fw(self):
        self.list_instances()
        for ins in self.instances.values():
            if time.time() - ins.created_at > 86400:
                continue
            try:
                self.clients[ins.region_id].create_firewall_rule(swas_models.CreateFirewallRuleRequest(
                    instance_id=ins.instance_id, port='1/65535', region_id=ins.region_id, rule_protocol='TCP')
                )
                logger.warning(f'Finished FW setup with {ins.ip}.')
            except:
                pass

    def stop(self, ins: AliInstance):
        self.list_instances()
        try:
            self.clients[ins.region_id].stop_instance(
                swas_models.StopInstanceRequest(instance_id=ins.instance_id, region_id=ins.region_id)
            )
            logger.warning(f'Instance {ins.instance_id} Stopped.')
        except Exception as e:
            logger.warning(f"Failed to stop {ins.instance_id}. Error msg: {e}")

    def start(self, ins: AliInstance):
        try:
            self.clients[ins.region_id].start_instance(
                swas_models.StartInstanceRequest(instance_id=ins.instance_id, region_id=ins.region_id)
            )
            logger.warning(f'Instance {ins.instance_id} Started.')
        except Exception as e:
            logger.warning(f"Failed to start {ins.instance_id}. Error msg: {e}")

    def scan_to_start(self):
        # This function should be run in the 1st of every month
        # It starts all the instances since their traffics are refreshed.
        self.list_instances()
        for ins in self.instances.values():
            if ins.remaining > self.stop_threshold and ins.status != 'Running':
                self.start(ins)
            if ins.remaining < self.stop_threshold:
                logger.error(f'Instance with ip {ins.ip} is not started because its data is below 50GiB.')

    def scan_to_stop(self):
        self.list_instances()
        alerted = list()
        for ins in self.instances.values():
            if ins.remaining < self.alert_threshold:
                alerted.append(ins.ip)
            if ins.remaining < self.stop_threshold and ins.status == 'Running':
                self.stop(ins)
        return alerted

    def available_servers(self) -> List[str]:
        # It returns servers with more than 100GiB data
        instances = list(self.instances.values())
        ret = list()
        sh_tz = timezone(timedelta(hours=8))
        today = datetime.now(sh_tz).replace(hour=0, minute=0, second=0, microsecond=0)
        next_month = today
        while next_month.month == today.month:
            next_month += timedelta(days=1)
        next_month = next_month.timestamp()
        for ins in instances:
            if ins.remaining > self.alert_threshold and ins.status == 'Running':
                if ins.expire > next_month:
                    ret.append((True, -ins.remaining, ins.expire, ins.ip))
                else:
                    ret.append((False, ins.expire, -ins.remaining, ins.ip))
        ret.sort()
        ret = [ret_[3] for ret_ in ret]
        return ret
