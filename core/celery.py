from __future__ import absolute_import, unicode_literals
from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mewray.settings')

app = Celery('mewray')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.beat_schedule = {
    'assigns': {
        'task': 'core.tasks.check_all_assigns',
        'schedule': crontab(minute='*/1'),
    },
    'nodes': {
        'task': 'core.tasks.check_all_nodes',
        'schedule': crontab(minute='*/1')
    },
    'subscriptions': {
        'task': 'core.tasks.check_all_subscriptions',
        'schedule': crontab(minute='*/1')
    }
}