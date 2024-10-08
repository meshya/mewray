from django.apps import AppConfig


class ApiConfig(AppConfig):
    def ready(self) -> None:
        from .docs import authentication
        return super().ready()
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
