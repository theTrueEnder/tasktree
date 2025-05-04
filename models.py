from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional
import datetime
import uuid

class TaskState(Enum):
    PENDING = auto()
    BLOCKED = auto()
    EXTERNAL = auto()
    COMPLETED = auto()

@dataclass
class Task:
    title: str
    description: Optional[str] = ""
    due_date: Optional[datetime.datetime] = None
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    state: TaskState = TaskState.PENDING
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
