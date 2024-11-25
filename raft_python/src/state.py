from enum import Enum
from dataclasses import dataclass


class NodeState(Enum):
    FOLLOWER = 0
    CANDIDATE = 1
    LEADER = 2


@dataclass
class LogEntry:
    term: int
    command: str
    index: int