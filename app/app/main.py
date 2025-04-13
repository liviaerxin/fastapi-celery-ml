from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from enum import Enum
from pydantic import BaseModel
from typing import Any, Union, Optional
from sqlalchemy.orm import Session

from celery.result import AsyncResult

from .tasks import (
    create_short_task,
    create_medium_task,
    create_long_task,
    app as celery_app,
)

from pprint import pprint
from . import schemas


app = FastAPI()


html_content = """
<html>
    <head>
        <title>Some HTML in here</title>
    </head>
    <body>
        <div class="starter-template">
        <h1>FastAPI + Celery + Docker</h1>
        <hr><br>
        <div>
            <h3>Tasks</h3>
            <p>Pick a task length.</p>
            <div class="btn-group" role="group" aria-label="Basic example">
            <button type="button" class="btn btn-primary" onclick="handleClick('short')">Short</a>
            <button type="button" class="btn btn-primary" onclick="handleClick('medium')">Medium</a>
            <button type="button" class="btn btn-primary" onclick="handleClick('long')">Long</a>
            </div>
        </div>
        <br><br>
        <div>
            <h3>Task Status</h3>
            <br>
            <table class="table">
            <thead>
                <tr>
                <th>ID</th>
                <th>Status</th>
                <th>Result</th>
                <th>DateDone</th>
                <th>Name</th>
                <th>Args</th>
                <th>Kwargs</th>
                <th>Worker</th>
                <th>Retries</th>
                <th>Queue</th>
                </tr>
            </thead>
            <tbody id="tasks">
            </tbody>
            </table>
        </div>
        </div>
    </body>
    <script type="text/javascript">
    (function() {
        console.log('Sanity Check!');
    })();

    function handleClick(type) {
    fetch('/tasks', {
        method: 'POST',
        headers: {
        'Content-Type': 'application/json'
        },
        body: JSON.stringify({ type: type }),
    })
    .then(response => response.json())
    .then(task => {
        const task_id = task.task_id
        getStatus(task_id)
    })
    }

    function getStatus(taskID) {
    fetch(`/tasks/${taskID}`, {
        method: 'GET',
        headers: {
        'Content-Type': 'application/json'
        },
    })
    .then(response => response.json())
    .then(task => {
        console.log(task)
        if (!task) {
            setTimeout(function() {
                getStatus(taskID);
            }, 1000);
            return false
        }
        const html = `
        <tr>
            <td>${task.task_id}</td>
            <td>${task.status}</td>
            <td>${task.result}</td>
            <td>${task.date_done}</td>
            <td>${task.name}</td>
            <td>${task.status}</td>
            <td>${task.args}</td>
            <td>${task.kwargs}</td>
            <td>${task.worker}</td>
            <td>${task.retries}</td>
            <td>${task.queue}</td>
        </tr>`;
        const newRow = document.getElementById('tasks').insertRow(0);
        newRow.innerHTML = html;

        const taskStatus = task.status;
        if ( taskStatus === 'SUCCESS' || taskStatus === 'FAILURE') return true;

        setTimeout(function() {
            getStatus(taskID);
        }, 1000);
    })
    .catch(err => console.log(err));
    }
    </script>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def read_index():
    return HTMLResponse(content=html_content, status_code=200)


@app.post("/tasks", status_code=201)
def create_task(task: schemas.TaskIn):
    task_result: AsyncResult = None

    if task.type == schemas.TaskType.short:
        task_result = create_short_task.delay()
    if task.type == schemas.TaskType.medium:
        task_result = create_medium_task.delay()
    if task.type == schemas.TaskType.long:
        task_result = create_long_task.delay()

    task_id = task_result.id
    pprint(task_id)

    return {"task_id": task_id}


@app.get("/tasks/{task_id}", response_model=Optional[schemas.Task])
def read_task(task_id: str):
    
    result = AsyncResult(task_id, app=celery_app)
    pprint(celery_app.conf.database_table_names)

    task = schemas.Task(
        task_id=result.task_id,
        status=result.status,
        date_done=result.date_done,
        name=result.name,
        args=result.args,
        kwargs=result.kwargs,
        worker=result.worker,
        retries=result.retries,
        queue=result.queue,
    )
    pprint(task)

    return task
