from celery import Celery
import os

app = Celery('bookstore',
             broker=os.getenv('CELERY_BROKER_URL', 'amqp://guest:guest@rabbitmq:5672//'),
             backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
             include=['app.tasks'])

app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    worker_concurrency=4,
    task_acks_late=True,
    task_reject_on_worker_lost=True
)

if __name__ == '__main__':
    app.start() 