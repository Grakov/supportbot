import os
from celery import Celery
from django.conf import settings


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

broker_url = f'{settings.RABBITMQ_LIB}://guest:guest@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}//'
app = Celery('backend_celery', broker=broker_url)

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
