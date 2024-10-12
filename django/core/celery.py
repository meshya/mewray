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
        'schedule': crontab(minute=21),
    },
    'nodes': {
        'task': 'core.tasks.check_all_nodes',
        'schedule': crontab(hour='*/2')
    },
    'subscriptions_assigns': {
        'task': 'core.tasks.check_all_subscriptions_assigns',
        'schedule': crontab(hour='*/5')
    },
    'subscription_time_and_traffic':{
        'task': 'core.tasks.check_all_subscriptions_time_and_traffic',
        'schedule': crontab(hour='*/3')
    },
    'nodes_traffic': {
        'task': 'core.tasks.check_all_nodes_traffic',
        'schedule': crontab(hour='*/2')
    }
}