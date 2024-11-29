from typing import *
from datetime import datetime, date
from dataclasses import dataclass

from ..utils import tz
from ..global_obj.config_setup import DOMAINS, BALANCE_CONFIG


@dataclass()
class User:
    user_id: int
    enable: bool
    username: str
    password: str
    email: str
    tag: Tuple[str]
    register_day: date
    last_active_day: date
    upload: int
    download: int
    balance: int
    uuid: str
    last_change: int
    remarks: Optional[str] = None

    def __post_init__(self):
        self.enable = (self.enable != 0)
        if isinstance(self.register_day, int):
            self.register_day = datetime.fromtimestamp(self.register_day, tz=tz).date()
        if isinstance(self.last_active_day, int):
            self.last_active_day = datetime.fromtimestamp(self.last_active_day, tz=tz).date()
        self.tag = tuple(self.tag.split(':')) if self.tag else tuple()

    def __repr__(self) -> str:
        ret = f'<User {self.user_id}: {self.email}'
        if not self.enable:
            ret += ' DISABLED'
        return ret + '>'

    def __eq__(self, other: "User"):
        return (
            self.user_id == other.user_id and
            self.password == other.password and
            self.uuid == other.uuid
        )

    @classmethod
    def from_list(cls, lst: list) -> "User":
        return User(*lst)

    @property
    def clash_sub_url(self):
        return f'https://{DOMAINS["subs"]}/clash/{self.email}/{self.password}'

    @property
    def profile_url(self):
        return f'https://{DOMAINS["profile"]}/profile/{self.email}/{self.password}'

    def provider(self, args: str = ''):
        return f'https://{DOMAINS["provider"]}/clash/{self.email}/{self.password}' + args

    @property
    def grade(self):
        return min(tag.lower() for tag in self.tag if len(tag) == 1)

    @property
    def total_data(self) -> int:
        return BALANCE_CONFIG['total'].get(self.grade, 0) * 2**30

    @property
    def daily_data(self) -> int:
        return BALANCE_CONFIG['daily'].get(self.grade, 0) * 2**30
