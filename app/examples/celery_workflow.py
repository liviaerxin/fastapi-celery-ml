from celery import chord, group
from celery.result import GroupResult, AsyncResult

from app.celery_app import tasks

if __name__ == "__main__":
    data = ["hello world", "hi"]

    # tasks.notify.delay("xxxxx")
    task: AsyncResult = chord([tasks.map.s(x) for x in data])(tasks.reduce.s())
    print(f"chord() - task[{task.id}]")
    # result = task.get()

    # print(f"chord() - task[{task.id}] result[{result}]")

    # job = group(
    #     [
    #         tasks.map.s("x"),
    #         tasks.map.s("x"),
    #     ]
    # )

    # task: GroupResult = job.apply_async()
    # print(f"group() - task[{task.id}]")