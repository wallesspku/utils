from typing import Tuple, Optional
from datetime import datetime, date
from dataclasses import dataclass

from ..utils import tz
from ..global_obj.config_setup import DOMAINS, BALANCE_CONFIG


@dataclass()
class User:
    user_id: int
    enabled: bool
    blocked: bool
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
        self.enabled = (self.enabled != 0)
        self.blocked = (self.blocked != 0)
        if isinstance(self.register_day, int):
            self.register_day = datetime.fromtimestamp(self.register_day, tz=tz).date()
        if isinstance(self.last_active_day, int):
            self.last_active_day = datetime.fromtimestamp(self.last_active_day, tz=tz).date()
        self.tag = tuple(self.tag.split(':')) if self.tag else tuple()

    @property
    def valid(self):
        # is enabled and not blocked
        return self.enabled and not self.blocked

    def __repr__(self) -> str:
        ret = f'<User {self.user_id}: {self.email}'
        if not self.valid:
            ret += ' INVALID'
        return ret + '>'

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
