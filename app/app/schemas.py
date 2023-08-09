from pydantic import BaseModel
from enum import Enum
from typing import Union, Any, Optional, List, Dict
from datetime import datetime


class TaskType(str, Enum):
    short = "short"
    medium = "medium"
    long = "long"


class TaskIn(BaseModel):
    type: Union[None, TaskType]


# Ref: https://docs.celeryq.dev/en/latest/internals/reference/celery.backends.database.models.html
# when `result_extended=True`, return [TaskExtended](https://docs.celeryq.dev/en/latest/internals/reference/celery.backends.database.models.html#celery.backends.database.models.TaskExtended`)
# when `result_extended=False`, return [TaskExtended](https://docs.celeryq.dev/en/latest/internals/reference/celery.backends.database.models.html#celery.backends.database.models.Task`)
class Task(BaseModel):
    # id: int
    task_id: str
    status: Optional[str]  # `PENDING`, `STARTED`, `RETRY`, `FAILURE`, `SUCCESS`
    result: Optional[Any]
    date_done: Optional[datetime]
    # extended fields
    name: Optional[str]
    args: Optional[List]
    kwargs: Optional[Dict]
    worker: Optional[str]
    retries: Optional[int]
    queue: Optional[str]
