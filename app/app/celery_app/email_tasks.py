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
app.conf.task_routes = {
    "app.celery_app.email_tasks.*": {
        "queue": "email_service",
    },
}


@app.task(acks_late=True)
def send_email(email_to: str):
    smtp_server = "10.6.64.184"
    port = 465  # For SSL

    sender_email = "me@rms.intranet"
    receiver_email = email_to
    password = "123456"

    # NOTE: `Subject` and `From` fields must be included to avoid being treadted as spam emails!
    # Fancy message
    message = EmailMessage()
    message["Subject"] = "multipart test"
    message["From"] = sender_email
    message["To"] = receiver_email

    asparagus_cid = make_msgid()
    print(asparagus_cid)
    message.set_content(
        """\
    <html>
        <body>
        <p>Hi,<br>
            How are you?<br>
            <a href="http://www.realpython.com">Real Python</a> 
            has many great tutorials.
        </p>
        <p>
            <img src="https://www.w3schools.com/html/pic_trulli.jpg" alt="Italian Trulli">
        </p>
        <p>
            <img src="cid:{asparagus_cid}" alt="Logo" width="600" height="400"><br>
        </p>
        </body>
    </html>
    """.format(
            asparagus_cid=asparagus_cid[1:-1],
        ),
        subtype="html",
    )

    # with open("/app/tests-data/out1.jpg", "rb") as fp:
    #     message.add_related(
    #         fp.read(), maintype="image", subtype="jpg", cid=asparagus_cid
    #     )

    with smtplib.SMTP_SSL(smtp_server, port) as s:
        # s.set_debuglevel(1)
        # s.ehlo()
        s.login(sender_email, password)
        s.send_message(message)
        # s.sendmail(sender_email, receiver_email, message)
