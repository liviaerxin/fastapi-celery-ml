from celery import Celery, Task
import importlib.util
import os
import sys
import time


class CeleryConfig:
    broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")


app = Celery()
app.config_from_object(CeleryConfig)
# Celery routing
app.conf.task_routes = {
    "app.celery_app.ml_tasks.*": {
        "queue": "ml_service",
    },
}
app.conf.broker_transport_options = {"visibility_timeout": 36000}  # 1h

MODEL_DIR = os.path.abspath(os.path.join(__file__, "..", "..", "..", "ml"))


class PredictTask(Task):
    """
    Abstraction of Celery's Task class to support loading ML model.
    """

    abstract = True

    def __init__(self):
        super().__init__()
        self.model = None
        print("PredictTask initialized")

    def __call__(self, *args, **kwargs):
        """
        Load model on first call (i.e. first task processed)
        Avoids the need to load model on each task request
        """
        if not self.model:
            print("Loading Model...")
            print(self.path)
            sys.path.insert(0, self.path[0])

            # NOTE: Use `parent_package.package`, so for getting `model.py`, it should be `mock_model.model`

            spec = importlib.util.find_spec(self.path[1])
            print(spec)
            # Or
            # spec = util.spec_from_file_location("mock_model.model", self.model_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            assert getattr(
                module, self.path[2]
            ), f"{self.path[2]} Class Not Found in {module}!"

            # Initialize an instance
            model_class = getattr(module, self.path[2])
            self.model = model_class()

            print("Model loaded")
        return self.run(*args, **kwargs)


@app.task(
    ignore_result=False,
    bind=True,
    base=PredictTask,
    path=(MODEL_DIR, "model", "SpamModel"),
)
def detect_spam(self, msg: str):
    """
    Essentially the run method of PredictTask
    """
    result = self.model.predict(msg)
    return result
