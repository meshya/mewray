from django.apps import AppConfig


class CoreConfig(AppConfig):
    def ready(self) -> None:
        from . import celery
        return super().ready()
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
