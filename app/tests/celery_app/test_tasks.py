from app.celery_app import tasks
from celery.result import AsyncResult
from celery import chord


def test_echo():
    task: AsyncResult = tasks.echo.delay("hello world")
    result = task.get()
    print(f"test_echo() - result[{result}]")


def test_add():
    task: AsyncResult = tasks.add.delay(2, 4)
    result = task.get()
    print(f"test_add() - result[{result}]")
    assert result == 6


def test_map():
    task: AsyncResult = tasks.map.delay("hello world")
    result = task.get()
    print(f"test_map() - result[{result}]")
    assert result == 11


def test_reduce():
    task: AsyncResult = tasks.reduce.delay([3, 4, 5, 6])
    result = task.get()
    print(f"test_reduce() - result[{result}]")
    assert result == 18


def test_mapreduce():
    data = ["hello world", "hi", "welcome"]
    task: AsyncResult = tasks.mapreduce.delay(data)
    result = task.get()
    print(f"test_mapreduce_1() - result[{result}]")
    # assert result == 20
