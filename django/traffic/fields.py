from typing import Any
from django.db import models
from .models import traffic

__all__ = [
    "TrafficField"
]

class TrafficField(models.IntegerField):
    def to_python(self, value: int) -> traffic:
        return traffic(value)
    def get_prep_value(self, value: traffic) -> int:
        if isinstance(value,traffic):
            return value.bytes
        else:
            return value

