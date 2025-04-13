# Demo ML(mach) application

Python ">=3.10"

Run web server,

```sh
uvicorn app.main:app --reload
```

Run ml worker,

```sh
celery --app app.celery_task_app.ml_tasks:app worker --loglevel=info --queue=ml_service
```

Run email worker,

```sh
celery --app app.celery_task_app.ml_tasks:app worker --loglevel=info --queue=email_service
```
