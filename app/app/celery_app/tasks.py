from celery import Celery, Task, chord, group, subtask, chain
from celery.result import AsyncResult, GroupResult, allow_join_result
from celery.canvas import Signature
from typing import List, Any
import os
import sys
import time
import math
import uuid


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


@app.task(bind=True)
def convert_video(self, video_path: str) -> str:
    print(f"convert_video() - task[{self.request.id}], video_path[{video_path}]")
    time.sleep(10)
    root, ext = os.path.splitext(video_path)
    output_video_path = f"{root}.out{ext}"
    print(
        f"convert_video() - task[{self.request.id}], output_video_path[{output_video_path}]"
    )
    return output_video_path


@app.task(bind=True)
def analyze_video(self, video_path: str) -> List[int]:
    import random

    print(f"convert_video() - task[{self.request.id}], video_path[{video_path}]")
    time.sleep(10)
    frames = random.sample(range(0, 20), 5)
    print(f"convert_video() - task[{self.request.id}], frames[{frames}]")
    return frames


@app.task(bind=True)
def mark_video(self, video_path: str) -> str:
    print(f"mark_video() - task[{self.request.id}], video_path[{video_path}")
    time.sleep(10)
    root, ext = os.path.splitext(video_path)
    mark_video_path = f"{root}.mark{ext}"
    print(f"mark_video() - task[{self.request.id}], mark_video_path[{mark_video_path}]")
    return mark_video_path


@app.task(bind=True)
def clip_video(self, video_path: str, frame: int) -> str:
    print(
        f"clip_video() - task[{self.request.id}], video_path[{video_path} frame[{frame}]"
    )
    time.sleep(10)
    root, ext = os.path.splitext(video_path)
    clipped_video_path = f"{root}.{frame}{ext}"
    print(
        f"clip_video() - task[{self.request.id}], clipped_video_path[{clipped_video_path}]"
    )
    return clipped_video_path


@app.task(bind=True)
def clip_videos(self: Task, video_path: str, frames: List[int]):
    print(
        f"clip_video() - task[{self.request.id}], video_path[{video_path}] frames[{frames}]"
    )

    subtasks: List[Signature] = []
    for frame in frames:
        t: Signature = clip_video.s(video_path=video_path, frame=frame).set(
            task_id=str(uuid.uuid4())
        )
        subtasks.append(t)

    g: Signature = group(subtasks)

    # To make the `g` be trackable, save the group result
    # After that, we can get the result by `GroupResult.restore(g_id)`
    g_result: GroupResult = GroupResult(
        id=self.request.id, results=[AsyncResult(id=t.id) for t in subtasks]
    )
    g_result.save()

    # Replace clip_videos with `g` task.
    # Inside this step, the `g` will be `apply_async()`.
    # So there is no need to call `apply_async()`
    self.replace(g)
    # code will not execute after `replace()`
    return


@app.task(bind=True)
def dmap_video(self, result, t4, t5):
    output_video = result[0]
    frames = result[1]

    t4 = subtask(t4)
    t5 = subtask(t5)

    t4: Signature = t4.clone(args=(output_video,))
    t5: Signature = t5.clone(args=(output_video, frames))

    g = group(t4, t5)
    self.replace(g)


@app.task(bind=True)
def pipeline(self: Task, video_path: str):
    input_video = video_path
    t1: Signature = convert_video.s(video_path=input_video).set(
        task_id=str(uuid.uuid4())
    )
    t2: Signature = analyze_video.s(video_path=input_video).set(
        task_id=str(uuid.uuid4())
    )

    t4: Signature = mark_video.s().set(task_id=str(uuid.uuid4()))
    t5: Signature = clip_videos.s().set(task_id=str(uuid.uuid4()))

    workflow: Signature = chain(group(t1, t2), dmap_video.s(t4, t5))
    # res: AsyncResult = workflow.apply_async()

    return self.replace(workflow)


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
