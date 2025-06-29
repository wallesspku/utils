import time
from typing import List, Optional, Tuple
import logging

import pyodbc

from .objects import User, Node, Traffic, Relay, link_relays, Mix, link_mixes
from .utils import (
    USER_COLUMNS, NODE_COLUMNS, TRAFFIC_COLUMNS, MIX_COLUMNS,
    RELAY_COLUMNS, tn, SUBLOG_COLUMNS, REGISTRATION_COLUMNS,
    USER_TRAFFIC_COLUMNS, NODE_TRAFFIC_COLUMNS
)

logger = logging.getLogger('walless')


class DBCommunicator:
    insert_sublog_sql = f'INSERT INTO {tn.sublog} (ts, ip, remarks, proxy_group, user_id) VALUES (?, ?, ?, ?, ?)'
    update_user_sql = f"UPDATE {tn.user} SET balance = balance + (?), upload = upload + (?), download = download + (?), last_change = ?, last_activity = ? WHERE user_id = ?"
    update_user_balance_sql = f"UPDATE {tn.user} SET balance = ?, last_change = ? WHERE user_id = ?"
    update_node_sql = f"UPDATE {tn.node} SET upload = upload + (?), download = download + (?) WHERE uuid = ?"
    get_log_sql = f'SELECT TOP 20000 log_id, user_id, node_id, upload, download, ts FROM {tn.traffic_log} ORDER BY log_id ASC'
    delete_log_sql = f'DELETE FROM {tn.traffic_log} WHERE log_id <= ?'
    upload_log_sql = f'INSERT INTO {tn.traffic_log} (user_id, node_id, upload, download, ts) VALUES (?, ?, ?, ?, ?)'
    insert_probe_sql = f'INSERT INTO {tn.probe} (ip, port, probe_result, ts) VALUES (?, ?, ?, ?)'
    insert_or_update_traffic_sql = f"""
IF EXISTS (SELECT 1 FROM {tn.traffic} WHERE ut_date=? AND user_id=? AND node_id=?)
BEGIN
    UPDATE {tn.traffic} SET upload=upload+?, download=download+? WHERE ut_date=? AND user_id=? AND node_id=?
END
ELSE
BEGIN
   INSERT INTO {tn.traffic}(ut_date, upload, download, node_id, user_id) VALUES(?, ?, ?, ?, ?)
END
""" # need 3 + 5 + 5 = 13 args

    # used for backup script
    backup_user_sql = f'SELECT {",".join(USER_COLUMNS)} FROM {tn.user}'
    backup_node_sql = f'SELECT {",".join(NODE_COLUMNS)} FROM {tn.node}'
    backup_traffic_sql = f'SELECT {",".join(TRAFFIC_COLUMNS)} FROM {tn.traffic} WHERE ut_date = ?'
    backup_sublog_sql = f'SELECT {",".join(SUBLOG_COLUMNS)} FROM {tn.sublog} WHERE ts >= ? AND ts < ?'
    backup_registration_sql = f'SELECT {",".join(REGISTRATION_COLUMNS)} FROM {tn.reg} WHERE ts >= ? AND ts < ?'
    delete_probe_sql = f'DELETE FROM {tn.probe} WHERE ts < ?'
    delete_sublog_sql = f'DELETE FROM {tn.sublog} WHERE ts < ?'
    delete_traffic_sql = f'DELETE FROM {tn.traffic} WHERE ut_date < ?'
    delete_registration_sql = f'DELETE FROM {tn.reg} WHERE ts < ?'
    add_abuse_sql = f"INSERT INTO {tn.abuse_event} (user, node, reason) VALUES (?, ?, ?, ?)"

    def __init__(self, conn_cfgs):
        self.conn_cfgs = conn_cfgs

    def connection(self):
        if self.conn_cfgs['type'] == 'mysql':
            return pyodbc.connect(
                'DRIVER=MySQL ODBC 8.0 ANSI Driver;'
                f'SERVER={self.conn_cfgs["credentials"]["host"]};'
                f'DATABASE={self.conn_cfgs["credentials"]["database"]};'
                f'UID={self.conn_cfgs["credentials"]["user"]};'
                f'PWD={self.conn_cfgs["credentials"]["password"]};'
                f'PORT={self.conn_cfgs["credentials"]["port"]};'
                'charset=utf8mb4;'
            )
        elif self.conn_cfgs['type'] == 'mssql':
            return pyodbc.connect(
                'DRIVER={ODBC Driver 18 for SQL Server};'
                f'SERVER={self.conn_cfgs["credentials"]["host"]};'
                f'DATABASE={self.conn_cfgs["credentials"]["database"]};'
                f'UID={self.conn_cfgs["credentials"]["user"]};'
                f'PWD={self.conn_cfgs["credentials"]["password"]};'
            )

    @staticmethod
    def execute_cursor(
        cursor, sql, query=False, func_to_apply=None, args=None, bulk=False
    ):
        logger.debug(f'Executing SQL: {sql}')
        if args is None:
            cursor.execute(sql)
        elif bulk:
            if len(args) == 1:
                cursor.execute(sql, args[0])
            else:
                cursor.fast_executemany = True
                cursor.executemany(sql, args)
        else:
            cursor.execute(sql, args)

        if query:
            fetched = cursor.fetchall()
            if func_to_apply is None:
                return list(fetched)
            else:
                return list(map(func_to_apply, fetched))

    def execute(
        self, sql, query=True, func_to_apply=None, args=None, bulk=False
    ) -> Optional[list]:
        conn = self.connection()
        with conn.cursor() as cur:
            ret = self.execute_cursor(cur, sql, query, func_to_apply, args, bulk)
        if not query:
            conn.commit()
        conn.close()
        return ret

    # user table
    def all_users(self, enable_only=True, after=-1) -> List[User]:
        sql = f"SELECT {','.join(USER_COLUMNS)} FROM {tn.user} WHERE last_change > {after}"
        if enable_only:
            sql += ' AND enabled != 0'
        return self.execute(sql, query=True, func_to_apply=User.from_list)

    def get_one_user_by_email(self, email: str) -> Optional[User]:
        ret = self.execute(
            f"SELECT {','.join(USER_COLUMNS)} FROM {tn.user} WHERE email=?",
            query=True, func_to_apply=User.from_list, args=[email],
        )
        if len(ret) == 0:
            return None
        return ret[0]

    def reset_user(self, user_id, password, uuid):
        try:
            change = int(time.time())
            self.execute(
                f"UPDATE {tn.user} SET password=?, uuid=?, last_change=? WHERE user_id=?",
                args=[password, uuid, change, user_id], query=False,
            )
        except Exception as e:
            return False, f'SQL Error: {str(e)}'

    def new_registration(self, email_header: str, sender: str, receiver: str, status: str):
        self.execute(
            f'INSERT INTO {tn.reg} (ts, email_header, sender, receiver, status) '
            'VALUES                (?   ,          ?,      ?,        ?, ?)',
            args=[    int(time.time()), email_header, sender, receiver, status],
            query=False,
        )

    def enable_user(self, user_id: int, enable: bool):
        self.execute(
            f'UPDATE {tn.user} SET enabled = ?, last_change = ? WHERE user_id = ?',
            args=[int(enable), int(time.time()), user_id], query=False,
        )

    # node table

    def all_servers(
            self,
            get_relays: bool = True,
            include_delete: bool = True,
            get_mix: bool = True,
            exclude_tail: bool = True,
        ) -> List[Node]:
        sql = f"SELECT {' , '.join(NODE_COLUMNS)} FROM {tn.node} "
        conditions = []
        if not include_delete:
            conditions += ['deleted = 0']
        if exclude_tail:
            conditions += ['node_id < 10000']
        if conditions:
            sql += ' WHERE ' + ' AND '.join(conditions)
        nodes = self.execute(sql, query=True, func_to_apply=Node.from_list)
        if get_relays:
            relays = self.execute(f"SELECT {' , '.join(RELAY_COLUMNS)} FROM {tn.relay}", True, Relay.from_list)
            link_relays(nodes, relays)
        if get_mix:
            mixes = self.execute(f'SELECT {",".join(MIX_COLUMNS)} from {tn.mix}', query=True, func_to_apply=Mix.from_list)
            link_mixes(nodes, mixes)
        nodes.sort(key=lambda x: x.node_id)
        return nodes

    def get_node_by_ip(self, ipv4: str) -> Node:
        ret = self.execute(
            f"SELECT * FROM {tn.node} WHERE ipv4=? AND deleted = 0",
            query=True, func_to_apply=Node.from_list, args=[ipv4]
        )
        if len(ret) == 1:
            return ret[0]
        return None

    def get_node_by_uuid(self, uuid: str) -> Node:
        # this retrieves deleted node as well
        ret = self.execute(
            f"SELECT {','.join(NODE_COLUMNS)} FROM {tn.node} WHERE uuid=?",
            query=True, func_to_apply=Node.from_list, args=[uuid]
        )
        if len(ret) == 1:
            return ret[0]
        return None

    def check_node_port(self, node_uuid: int):
        return self.execute(
            f'SELECT port FROM {tn.node} WHERE node_uuid = ?', args=[node_uuid], query=True
        )[0][0]

    def change_node_port(self, node_uuid: str, port: int):
        self.execute(
            f'UPDATE {tn.node} SET port = ? WHERE uuid = ?',
            args=[port, node_uuid], query=False,
        )

    def hide_node(self, node_uuid: str, hide_flag: bool):
        self.execute(
            f'UPDATE {tn.node} SET hidden = ? WHERE uuid = ?',
            args=[bool(hide_flag), node_uuid], query=False,
        )

    # user traffic table

    def get_traffic_after(self, user_id, after) -> List[Traffic]:
        return self.execute(
            f'SELECT {",".join(USER_TRAFFIC_COLUMNS)} FROM {tn.user_traffic} WHERE ut_date > ? AND user_id = ?',
            args=(after, user_id), func_to_apply=Traffic.from_list_user, query=True,
        )

    # probe table

    def get_probe_after(self, after: int) -> List[Tuple]:
        return self.execute(
            f'SELECT ip, port, probe_result, ts from {tn.probe} WHERE ts > ?',
            args=[after], query=True,
        )

    # abuse event

    def report_abuse_event(self, node_id: str, user_id: int, reason: str):
        self.execute(
            sql=self.add_abuse_sql,
            args=[user_id, node_id, reason],
            query=False,
        )
