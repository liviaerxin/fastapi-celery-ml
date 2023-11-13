from celery import chord, group, chain, signature
from celery.result import GroupResult, AsyncResult

from app.celery_app import tasks

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
    data = ["hello world", "hi", "me"]
    result: AsyncResult = chord([tasks.map.s(x) for x in data])(tasks.reduce.s())
    
    print(store(result))

    print(f"chord() - result#[{result.id}]")
    print(f"chord() - result[{result.get()}]")


def run_group():
    job = group(
        [
            tasks.map.s("x"),
            tasks.map.s("x11"),
        ]
    )

    result: GroupResult = job.apply_async()
    print(result.children)
    print(store(result))

    print(f"group() - result#[{result.id}]")
    print(f"group() - result[{result.get()}]")


def run_chain():
    s1 = tasks.add.s(4, 5)
    s2 = tasks.add.s(6)
    s3 = tasks.mul.s(7)

    c = chain(s1, s2, s3)
    result: AsyncResult = c()

    print(store(result))

    print(f"chain() - result#[{result.id}]")

    print(f"chain() - result[{result.get()}]")

if __name__ == "__main__":
    # run_chain()
    # run_chord()
    run_group()
