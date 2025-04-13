# celeryconfig.py
import os

broker_url = os.environ.get("BROKER_URL", "redis://redis:6379")
result_backend = os.environ.get("RESULT_BACKEND", "redis://redis:6379")
result_extended = (
    True  # return more fields than normal, seeing `TaskExtended` and `Task`
)
task_track_started = True

# Add other configuration settings as needed
database_table_names = {
    "task": "myapp_taskmeta",
    "group": "myapp_groupmeta",
}
