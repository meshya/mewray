from __future__ import absolute_import, unicode_literals
from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mewray.settings')

app = Celery('mewray')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.beat_schedule = {
    'nodes_sync': {
        'task': 'core.tasks.sync_nodes_task',
        'schedule': crontab(minute=21),
    },
    'subs_sync': {
        'task': 'core.tasks.sync_subs_task',
        'schedule': crontab(hour='*/5')
    },
    'subs_check':{
        'task': 'core.tasks.check_subs_task',
        'schedule': crontab(hour='*/3')
    },
}