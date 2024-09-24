from repo import models
from rest_framework import serializers
from django.http import Http404
from .models import SubscriptionDto
from core.services import SubscriptionService
import uuid
import datetime
from asgiref.sync import async_to_sync

class SubscriptionSerializer(serializers.Serializer):
    UserId = serializers.CharField()
    ViewId = serializers.CharField()
    StartedAt = serializers.IntegerField()
    EnableUntil = serializers.IntegerField()
    MaxConnectionCount = serializers.IntegerField()
    MaxTraffic = serializers.CharField()
    UsedTraffic = serializers.CharField()

    def ato_representation(self, instance):
        return async_to_sync(self.ato_representation)(instance)

    async def ato_representation(self, instance):
        sub = instance
        return {
            "UserId": sub.api_pk,
            "ViewId": sub.view_pk,
            "StartedAt": sub.start_date.timestamp(),
            "EnableUntil": sub.start_date.timestamp() + sub.period.total_seconds(),
            "MaxConnectionCount": sub.connection_number,
            "MaxTraffic": f"{sub.traffic}M",
            "UsedTraffic": f"{await SubscriptionService(sub).get_used_traffic()}M"
        }
    

class SubscriptionListSerializer(serializers.ListSerializer):
    child = SubscriptionSerializer()

class SubscriptionCreateSerializer(serializers.Serializer):
    UserId = serializers.CharField()
    PlanId = serializers.IntegerField()

    async def auto_generate_uuid(self, uniq_test=None):
        gen = uuid.uuid4()
        if uniq_test and await uniq_test(gen):
            return self.auto_generate_uuid()
        return gen

    async def acreate(self, validated_data:dict)->models.subscribe:
        plan = models.plan.objects.filter(id=validated_data['PlanId'])
        if not await plan.aexists():
            raise Http404()
        plan = await plan.afirst()
        
        api_pk = validated_data.get('UserId', None)
        sub = None
        if api_pk:
            try:
                sub = await models.subscribe.objects.aget(api_pk=api_pk)
            except models.subscribe.DoesNotExist:
                sub = None
        else:
            api_pk = await self.auto_generate_uuid(lambda gen: models.subscribe.objects.filter(api_pk=gen).aexists())
        arguments={
            "node_number": plan.node_number,
            "connection_number": plan.connection_number,
            "period": plan.period,
            "traffic": plan.traffic,
            "start_date": datetime.datetime.now()
        }
        if sub:
            for name, value in arguments.items():
                setattr(sub ,name , value)
            await sub.asave()
        else:
            arguments['view_pk'] = await self.auto_generate_uuid(lambda gen: models.subscribe.objects.filter(view_pk=gen).aexists())
            arguments['api_pk'] = api_pk
            sub = await models.subscribe.objects.acreate(**arguments)

        return sub