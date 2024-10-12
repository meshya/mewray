from django.db import models
from traffic.fields import TrafficField


class subscribe(models.Model):
    id = models.BigAutoField(primary_key=True)
    api_pk = models.CharField(max_length=36)
    view_pk = models.CharField(max_length=36)
    node_number = models.IntegerField()
    connection_number = models.IntegerField()
    period = models.DurationField()
    traffic = TrafficField()
    start_date = models.DateTimeField()
    enable = models.BooleanField()

    def __str__(self):
        return f'{self.api_pk}->{self.view_pk}'

class plan(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=10)
    node_number = models.IntegerField()
    connection_number = models.IntegerField(default=1)
    period = models.DurationField()
    traffic = TrafficField()

    def __str__(self):
        return f'{self.name}: {self.id}'


class node(models.Model):
    backend = models.CharField(max_length=10, default='XUI')
    address = models.CharField(max_length=50)
    auth = models.CharField(max_length=100)
    host = models.CharField(max_length=30)
    max_traffic = TrafficField()
    period = models.DurationField()
    period_start = models.DateField()
    settings = models.CharField(max_length=100)
    enable = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.host}-{self.enable}'

def assign_on_node_delete(collector, field, sub_objs, using):
    models.SET_NULL(collector, field, sub_objs, using)
    collector.add_field_update(assign.enable, False, sub_objs)

class assign(models.Model):
    id = models.BigAutoField(primary_key=True)
    subscribe = models.ForeignKey(subscribe, on_delete=models.CASCADE)
    node = models.ForeignKey(node, on_delete=assign_on_node_delete)
    enable = models.BooleanField(default=True)
    uuid = models.CharField(max_length=36)

    def __str__(self):
        return f'{self.uuid}->{self.node.host}'