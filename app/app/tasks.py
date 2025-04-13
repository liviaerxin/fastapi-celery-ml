from celery import Celery
from celery.result import AsyncResult
import time
import os

app = Celery("tasks")
app.config_from_object("app.celeryconfig")


@app.task(bind=True, name="create_short_task")
def create_short_task(self) -> bool:
    # self.update_state(state="PROGRESS")
    time.sleep(10)
    return True


@app.task(name="create_medium_task")
def create_medium_task() -> bool:
    time.sleep(20)
    return True


@app.task(name="create_long_task")
def create_long_task() -> bool:
    time.sleep(30)
    return True
