from celery import Celery, Task, chord, group, subtask, chain
from celery.result import AsyncResult, allow_join_result, GroupResult
from typing import List, Any
import os
import sys
import time
import math


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


@app.task()
def log(msg: Any) -> Any:
    time.sleep(1)
    return f"log() - message[{msg}]"


@app.task(acks_late=True)
def wait(secs: float) -> str:
    print(f"wait() - Start, secs[{secs}]s")
    time.sleep(secs)
    print(f"wait() - Done, secs[{secs}]s")
    return f"wait() - Done, secs[{secs}]s"


@app.task(bind=True, acks_late=True)
def progress(self, secs: float) -> List[int]:
    print(f"progress() - Start, secs[{secs}]s")
    secs = math.ceil(secs)
    total = 100
    n = 0
    result = []
    while n <= secs:
        self.update_state(
            state="PROGRESS",
            meta={
                "current": (n / secs) * total,
                "total": total,
            },
        )
        result.append(n)
        n = n + 1
        time.sleep(1)
    return result


@app.task(bind=True)
def add(self, x: float, y: float) -> float:
    print(f"add() - task[{self.request.id}], x[{x}], y[{y}]")
    time.sleep(10)
    total = x + y
    print(f"add() - task[{self.request.id}], total[{total}]")
    return total


@app.task(bind=True)
def mul(self, x: float, y: float):
    print(f"mul() - task[{self.request.id}], x[{x}], y[{y}]")
    time.sleep(10)
    total = x * y
    print(f"add() - task[{self.request.id}], total[{total}]")
    return total


@app.task(name="celery.notify", shared=False, ignore_result=True)
def notify(mgs: str):
    print(f"notify() - mgs[{mgs}]")


@app.task(ignore_result=False)
def map(data: str) -> int:
    print(f"map() - task[{app.current_task.request.id}] data[{data}]")
    time.sleep(3)
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


@app.task()
def dmap(results, t4, t5, t6):
    # Map a task over an result and return as a group

    # subtask is a task with parameters passed, but not yet started.
    t4 = subtask(t4)
    t5 = subtask(t5)
    t6 = subtask(t6)

    print(results[0])
    # iterating over result and cloning task
    header = [t4.clone((results[0],))]
    header.extend([t5.clone((arg,)) for arg in results[1]])
    task = chord(header=header, body=t6)
    result = task.apply_async()
    return result
