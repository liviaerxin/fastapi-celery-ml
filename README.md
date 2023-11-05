# FastAPI + Celery + Machine Learning demo

An example microservices illustrates how to perform heavy background computation task such as running machine learning model.

![](./2023-06-16-16-20-19.png)

In this demo, we will say:

- **Celery** uses `Redis` as both of `broker` and `backend`.
- There are two **Celery** workers to do their separate tasks:
  - **ml-worker** will only handle detecting spam tasks
  - **email-worker** will only handle email related tasks
  - both these two workers will run in solo pool
- Use Redis

Tech stack:

- FastAPI
- Celery
  - Redis: as broker and backend

Workflow:

![workflow1](./out/workflow1.png)

_NOTE_:

- `broker` is where `Celery` transport message into a queue
- `backend` is where `Celery` store the result
- FastAPI will not involve with `Redis` and `PostgresSQL` directly, it's done through `Celery`
- Celery will manage backend `PostgresSQL` database via `SQLAlchemy`
- Celery will manage broker `Redis`
- Celery will detect schema [Task and TaskSet](https://docs.celeryq.dev/en/latest/internals/reference/celery.backends.database.models.html#celery.backends.database.models) in PostgreSQL and generate lazily when doing on the first job run.

## Get Started

```sh
docker-compose build

docker-compose up -d
```

## Redis CLI

```sh
redis-cli -h redis -p 6379
```

```sh

```