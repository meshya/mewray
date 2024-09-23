from rest_framework.views import APIView
from repo import models
from .serializers import SubscriptionSerializer, SubscriptionCreateSerializer, SubscriptionListSerializer
from django.http import HttpResponseNotFound, JsonResponse, HttpResponse, HttpRequest, Http404
import json
from asgiref.sync import async_to_sync, sync_to_async

def makeResponse(data=None, status=0, HttpStatus=202,**kwargs):
    export = {}
    if status is not None:
        export['status'] = status
    if data:
        export['data'] = data
    return JsonResponse(
        export,
        status = HttpStatus,
        **kwargs
    )

class SubscriptionsAPIView(APIView):
    @async_to_sync
    async def get(self, request, pk):
        q = models.subscribe.objects.filter(api_pk=pk)
        if not await q.aexists():
            return self.makeResponse(status=4, HttpStatus=404)
        serializer = SubscriptionSerializer(await q.afirst())
        return HttpResponse(
            makeResponse(
                serializer.data,
                0
            )
        )
    @async_to_sync
    async def delete(self, request, pk):
        q = models.subscribe.objects.filter(api_pk=pk)
        if not await q.aexists():
            return makeResponse(
                status=4,
                HttpStatus=404
            )
        await q.adelete()
        return makeResponse(
            status=0,
            HttpStatus=200
        )

from core.tasks import check_subscription_aligns

class SubscriptionsListAPIView(APIView):
    @async_to_sync
    async def post(self, request:HttpRequest):
        serializer = SubscriptionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return makeResponse(
                status=3,
                HttpStatus=400
            )
        try:
            obj = await serializer.acreate(serializer.data)
        except Http404:
            return makeResponse(
                status=4,
                HttpStatus=404
            )
        check_subscription_aligns.delay(obj.id)
        respSerializer = SubscriptionSerializer(obj)
        return makeResponse(
            data=respSerializer.data,
            HttpStatus=201,
            status=0
        )
    @async_to_sync
    async def get(self, request):
        try:
            objs = models.subscribe.objects.filter()
            all=[]
            async for i in objs.aiterator():
                all.append(i)
            serializer = SubscriptionListSerializer(all)
            data = serializer.data
        except:
            return makeResponse(
                status=2,
                HttpStatus=500
            )
        return makeResponse(
            data=data,
            status=0,
            HttpStatus=200
        )