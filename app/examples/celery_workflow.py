from celery import group, chord, chain, signature, Task
from celery.canvas import Signature
from celery.result import AsyncResult, allow_join_result, GroupResult, ResultSet

import time
from app.celery_app import tasks
import uuid
import json


def print_task(task: Signature):
    print(f"{json.dumps(task, indent=2)}")


def store(node):
    id_chain = []
    while node.parent:
        id_chain.append(node.id)
        node = node.parent
    id_chain.append(node.id)
    return id_chain


def restore(id_chain):
    id_chain.reverse()
    last_result = None
    for tid in id_chain:
        result = AsyncResult(tid)
        result.parent = last_result
        last_result = result
    return last_result


def run_chord():
    result: AsyncResult = chord([tasks.add.s(2, 2), tasks.add.s(3, 3)])(
        tasks.test_celery.s()
    )
    print(f"{result.get()}")


def run_group():
    result: GroupResult = group(
        [tasks.add.s(2, 2), tasks.add.s(3, 3), tasks.add.s(4, 4)]
    ).apply_async()
    print(f"#{result.id} {result.get()}")

    result.save()
    saved_result = GroupResult.restore(result.id)

    print(f"#{saved_result.id} {saved_result.get()}")


def run_chain():
    s1 = tasks.add.s(4, 5)
    s2 = tasks.add.s(6)
    s3 = tasks.add.s(7)

    # result: AsyncResult = chain(tasks.add.s(4,5), tasks.add.s(6), tasks.add.s(7))()
    result: AsyncResult = chain(s1, s2, s3).apply_async()

    print(result.c)
    print(result.get())


def get_chain_graph():
    # result: AsyncResult = chord(group([tasks.add.s(2, 2), tasks.add.s(3, 3)]))(
    #     group([tasks.add.si(2, 2), tasks.add.si(3, 3)])
    # )
    # fmt: off
    task = chain(
            tasks.add.s(2, 2), 
            tasks.add.s(3)
        )
    print_task(task)

    # fmt: on
    result: AsyncResult = (
        task.freeze()
    )  # `freeze()` Dry run to give underlying running steps

    print(f"chain task: {task}")
    print(f"chain graph: {result.as_tuple()}")
    print(f"result: #[{result}]")


def get_group_graph():
    # fmt: off
    task = group(
        [
            tasks.add.s(2, 2), 
            tasks.add.s(3, 3)
        ])
    print_task(task)

    # fmt: on
    result: GroupResult = (
        task.freeze()
    )  # `freeze()` Dry run to give underlying running steps

    print(f"group task: {task}")
    print(f"group graph: {result.as_tuple()}")
    print(f"group: #[{result}]")


def get_chord_graph():
    task = chord(header=[tasks.add.s(2, 2), tasks.add.s(3, 3)], body=tasks.add.si(4, 2))
    print_task(task)
    # task = chord(header=[tasks.add.s(2, 2), tasks.add.s(3, 3)], body=group([tasks.add.si(4, 2), tasks.add.si(4, 3)]))
    result: AsyncResult = (
        task.freeze()
    )  # `freeze()` Dry run to give underlying running steps

    print(type(result.parent))
    print(f"chord task: {task}")
    print(f"chord graph: {result.as_tuple()}")
    print(f"chord: #[{result}]")


def run_chord_graph(dryrun=False, wait=True):
    # task = chord(header=[tasks.add.s(2, 2), tasks.add.s(3, 3)], body=tasks.add.si(4, 2))
    task = chord(
        header=[tasks.add.s(2, 2), tasks.add.s(3, 3)],
        body=group([tasks.add.si(4, 2), tasks.add.si(4, 3)]),
    )
    print_task(task)

    result: AsyncResult = (
        task.freeze() if dryrun else task.apply_async()
    )  # `freeze()` Dry run to give underlying running steps

    print(type(result.parent))
    print(f"chord task: {task}")
    print(f"chord graph: {result.as_tuple()}")
    print(f"chord: #[{result}]")
    if not dryrun and wait:
        print(f"chord: [{result.get()}]")


def run_signature(dryrun=False):
    task_id = str(uuid.uuid4())
    print(f"task_id#[{task_id}]")
    task: Signature = tasks.progress.s(10).set(task_id=task_id)
    print(f"signature: #{task.id}")

    result: AsyncResult = task.freeze() if dryrun else task.apply_async()

    print(f"signature: {task}")
    print(f"signature: #[{result}]")
    if not dryrun:
        print(f"signature: [{result.get()}]")


def show_progress():
    t1: Signature = tasks.progress.s(10).set(task_id=str(uuid.uuid4()))
    t2: Signature = tasks.progress.s(5).set(task_id=str(uuid.uuid4()))

    # t3: Signature = tasks.add.si(4, 4).set(task_id=str(uuid.uuid4()))
    # t4: Signature = tasks.add.si(5, 5).set(task_id=str(uuid.uuid4()))
    t3: Signature = tasks.log.s().set(task_id=str(uuid.uuid4()))
    t4: Signature = tasks.log.s().set(task_id=str(uuid.uuid4()))

    task = chord(header=[t1, t2], body=group([t3, t4]))
    result: AsyncResult = task.apply_async()

    print(f"task: {task}")
    print(f"graph: {result.as_tuple()}")
    print(f"result: #[{result}]")

    res1 = AsyncResult(id=t1.id)
    res2 = AsyncResult(id=t2.id)
    res3 = AsyncResult(id=t3.id)
    res4 = AsyncResult(id=t4.id)

    ress = ResultSet(results=[res1, res2, res3, res4])

    while not result.ready():
        print(f"result #1, result[{res1.result}] status[{res1.status}]")
        print(f"result #2, result[{res2.result}] status[{res2.status}]")
        print(f"result #3, result[{res3.result}] status[{res3.status}]")
        print(f"result #4, result[{res4.result}] status[{res4.status}]")
        print(f"result set[#1, #2, #3, #4] {ress.completed_count()} {ress.ready()}")
        time.sleep(1)

    print(f"result #1, result[{res1.result}] status[{res1.status}]")
    print(f"result #2, result[{res2.result}] status[{res2.status}]")
    print(f"result #3, result[{res3.result}] status[{res3.status}]")
    print(f"result #4, result[{res4.result}] status[{res4.status}]")
    print(f"result set[#1, #2, #3, #4] {ress.completed_count()} {ress.ready()}")
    print(f"result: {result.get()}")


"""_summary_
dag_adjacency_list={
    t1: [t3], #
    t2: [t3],
    t3: [t4, t5]
    t4: [t6]
    t5: [t6]
}

# t1 + t2 > t3 > t4 + (t51, t52, t53, t54, t55, t56) > t6
"""


def run_workflow():
    input_video = "foo.mp4"
    print(f"run_workflow() - process video[{input_video}]")
    t1: Signature = tasks.convert_video.s(video_path=input_video).set(
        task_id=str(uuid.uuid4())
    )
    t2: Signature = tasks.analyze_video.s(video_path=input_video).set(
        task_id=str(uuid.uuid4())
    )

    g12: Signature = group(t1, t2)
    g12_res: GroupResult = g12.apply_async()

    # Blocking util t1, t2 all are completed
    while not g12_res.ready():
        res1 = AsyncResult(id=t1.id)
        res2 = AsyncResult(id=t2.id)
        print(f"result #t1, result[{res1.result}] status[{res1.status}]")
        print(f"result #t2, result[{res2.result}] status[{res2.status}]")
        print(
            f"result #g12, completed_count#[{g12_res.completed_count()}] ready[{g12_res.ready()}]"
        )

        time.sleep(1)

    print(f"result #g12, {g12_res.get()}")
    output_video, frames = g12_res.get()

    t4: Signature = tasks.mark_video.s(video_path=output_video).set(
        task_id=str(uuid.uuid4())
    )
    t5: Signature = tasks.clip_videos.s(video_path=output_video, frames=frames).set(
        task_id=str(uuid.uuid4())
    )

    g45: Signature = group(t4, t5)
    g45_res: GroupResult = g45.apply_async()

    # Blocking util t4, t5 all are completed
    while not g45_res.ready():
        res4 = AsyncResult(id=t4.id)
        res5 = AsyncResult(id=t5.id)
        print(f"result #t4, result[{res4.result}] status[{res4.status}]")
        print(f"result #t5, result[{res5.result}] status[{res5.status}]")
        print(
            f"result #g45, result[{g45_res.completed_count()}] ready[{g45_res.ready()}]"
        )

        time.sleep(1)

    print(f"result #g45, {g45_res.get()}")
    mark_video, clipped_videos = g45_res.get()


def run_workflow_1():
    input_video = "foo.mp4"
    print(f"run_workflow_1() - process video[{input_video}]")
    res: AsyncResult = tasks.pipeline.delay(video_path=input_video)

    print(f"run_workflow_1() - #[{res.id}] result: {res.get()}")


if __name__ == "__main__":
    # run_chord_graph(dryrun=True)
    # run_chord_graph(dryrun=False, wait=True)
    # run_signature(dryrun=False)
    # show_progress()
    # run_workflow()
    run_workflow_1()
