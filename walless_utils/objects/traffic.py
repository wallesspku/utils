from dataclasses import dataclass
from datetime import date


@dataclass()
class Traffic:
    date: date
    node_uuid: str = None
    user_id: int = None
    upload: int = 0
    download: int = 0

    @classmethod
    def from_list(cls, lst) -> "Traffic":
        return Traffic(*lst)
    
    @classmethod
    def from_list_user(cls, lst) -> "Traffic":
        return Traffic(lst[0], None, lst[1], lst[2], lst[3])
    
    @classmethod
    def from_list_node(cls, lst) -> "Traffic":
        return Traffic(lst[0], lst[1], None, lst[2], lst[3])

    def __repr__(self):
        return f'<Traffic {self.traffic_id}: Node {self.node_id}, User {self.user_id}>'

