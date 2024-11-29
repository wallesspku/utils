from dataclasses import dataclass
from datetime import date


@dataclass()
class Traffic:
    ut_id: int
    date: date
    node_id: int
    user_id: int
    upload: int
    download: int

    @classmethod
    def from_list(cls, lst) -> "Traffic":
        return Traffic(*lst)

    def __repr__(self):
        return f'<Traffic {self.traffic_id}: Node {self.node_id}, User {self.user_id}>'

