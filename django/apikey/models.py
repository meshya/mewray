from django.db import models

def makeAccessKey():
    from uuid import uuid4
    return uuid4().__str__()

class access(models.Model):
    key = models.CharField(max_length=36, default=makeAccessKey)
    name = models.CharField(max_length=10)
    access = models.BooleanField(default=True)
