import socket
import time
from datetime import datetime
import math
import requests
import warnings
from zoneinfo import ZoneInfo

tz = ZoneInfo('Asia/Shanghai')


USER_COLUMNS = [
    'user_id', 'enabled', 'username', 'password', 'email', 'tag', 'reg_time', 'last_activity', 'upload', 'download',
    'balance', 'uuid', 'last_change', 'remarks'
]
NODE_COLUM_AND_TYPE = [
    ('node_id', int), ('uuid', str), ('deleted', bool), ('hidden', bool), ('name', str), ('weight', float), ('tag', str),
    ('ipv4', str), ('ipv6', str), ('port', int), ('properties', str),
    ('remarks', str), ('idc', str), ('upload', int), ('download', int),
    ('traffic_reset_day', int), ('traffic_limit', int),
]
NODE_COLUMNS, NODE_DTYPES = zip(*NODE_COLUM_AND_TYPE)
TRAFFIC_COLUMNS = ['ut_date', 'node_id', 'user_id', 'upload', 'download']
USER_TRAFFIC_COLUMNS = ['ut_date', 'user_id', 'upload', 'download']
NODE_TRAFFIC_COLUMNS = ['ut_date', 'node_id', 'upload', 'download']
RELAY_COLUMNS = ['relay_id', 'name', 'tunnel', 'tag', 'properties', 'hidden', 'source_id', 'target_id', 'port']
SUBLOG_COLUMNS = ['sub_id', 'ts', 'ip', 'remarks', 'proxy_group', 'user_id']
REGISTRATION_COLUMNS = ['reg_id', 'ts', 'email_header', 'receiver', 'sender', 'status']
MIX_COLUMNS = ['source_id', 'target_id', 'scope']

_units = ['B', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB']

HUAWEI_LINES = ['default_view', 'Jiaoyuwang', 'Dianxin', 'Yidong', 'Liantong', 'Liantong_Huabei', 'Dianxin_Beijing']

class TableNames:
    user = 'main_user'
    node = 'main_node'
    traffic = 'main_traffic'
    user_traffic = 'main_usertraffic'
    node_traffic = 'main_nodetraffic'
    traffic_log = 'main_trafficlog'
    reg = 'main_registration'
    sublog = 'main_sublog'
    relay = 'main_relay'
    probe = 'main_probe'
    mix = 'main_mix'

tn = TableNames()


def data_format(data_size, decimal=False):
    sign = ''
    if data_size < 0:
        sign = '-'
        data_size = -data_size
    if decimal:
        return sign + _decimal_data_format(data_size)
    else:
        return sign + _data_format(data_size)


def _decimal_data_format(data_size, unit_idx=0):
    if data_size > 1024:
        return _decimal_data_format(data_size / 1024, unit_idx+1)
    return f'{data_size:.2f} {_units[unit_idx]}'


def _data_format(data_size, unit_idx=0):
    if data_size % 1024 != 0:
        suffix = '{} {}'.format(data_size % 1024, _units[unit_idx])
    else:
        suffix = ''
    if data_size < 1024 or unit_idx == len(_units) - 1:
        if suffix == '':
            return '0 B'
        return suffix
    else:
        prefix = _data_format(data_size // 1024, unit_idx+1)
        return '{} {}'.format(prefix, suffix)


def none_field(v):
    return (v is None) or (isinstance(v, float) and math.isnan(v)) or (isinstance(v, str) and v in ['None', '', 'NULL'])


def wait_for_network():
    while True:
        try:
            ret = requests.get('https://www.cloudflare.com/cdn-cgi/trace/')
            if ret.status_code == 200:
                print('Connected to network!')
                return
        except:
            pass
        print('Waiting for network...')
        time.sleep(4)


def get_ip():
    warnings.warn('Deprecated warning: use network status instead.')
    return requests.get('https://api4.ipify.org').text.strip()


def url2ip(url):
    try:
        ip = socket.gethostbyname(url)
        return ip
    except:
        return 'error'


def current_time():
    return datetime.now(tz=tz)


def today():
    return current_time().date()
