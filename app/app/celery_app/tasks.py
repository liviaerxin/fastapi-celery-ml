from celery import Celery, Task
from email.utils import make_msgid
from email.message import EmailMessage
import smtplib
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
def add(self, x, y):
    print(f"add() - task[{self.request.id}], x[{x}], y[{y}]")
    total = x + y
    print(f"add() - task[{self.request.id}], total[{total}]")
    return total