from celery import Celery, Task, chord, group
from celery.result import AsyncResult, allow_join_result
from typing import List
import os
import sys
import time


class CeleryConfig:
    broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")


app = Celery()
app.config_from_object(CeleryConfig)
# Celery routing
# app.conf.task_routes = {
#     'app.celery_app.email_tasks.*': {
#         'queue': 'email_service',
#     },
# }
app.conf.broker_transport_options = {"visibility_timeout": 3600}


@app.task()
def echo(msg: str) -> str:
    time.sleep(1)
    return f"echo() - message[{msg}]"


@app.task(acks_late=True)
def wait(secs: float) -> str:
    print(f"wait() - Start, secs[{secs}]s")
    time.sleep(secs)
    print(f"wait() - Done, secs[{secs}]s")
    return f"wait() - Done, secs[{secs}]s"


@app.task(bind=True)
def add(self, x, y) -> int:
    print(f"add() - task[{self.request.id}], x[{x}], y[{y}]")
    total = x + y
    print(f"add() - task[{self.request.id}], total[{total}]")
    return total


@app.task()
def map(data: str) -> int:
    print(f"map() - task[{app.current_task.request.id}] data[{data}]")
    size = len(data)
    return size


@app.task()
def reduce(counts: List[int]) -> int:
    print(f"reduce() - task[{app.current_task.request.id}] counts[{counts}]")
    total = 0
    for c in counts:
        total += c
    return total


@app.task()
def mapreduce(data: List[str]):
    print(f"mapreduce() - task[{app.current_task.request.id}] data[{data}]")
    job = group([map.s(x) for x in data])
    task: AsyncResult = job.delay()
    with allow_join_result():
        result = task.get()
    # task.get(disable_sync_subtasks=False)
    print(f"mapreduce() - result[{result}]")
    return result
