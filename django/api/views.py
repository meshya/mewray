from rest_framework.views import APIView
from repo import models
from .serializers import SubscriptionSerializer, SubscriptionCreateSerializer, SubscriptionListSerializer, ResponseSerializer
from django.http import HttpResponseNotFound, JsonResponse, HttpResponse, HttpRequest, Http404
import json
from asgiref.sync import async_to_sync, sync_to_async
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, extend_schema_view
from drf_spectacular.types import OpenApiTypes
from .docs import authentication

async def makeResponse(serializer:ResponseSerializer, HttpStatus=202,**kwargs):
    export = await sync_to_async(getattr)(serializer, 'data')
    return JsonResponse(
        export,
        status = HttpStatus,
        **kwargs
    )

class SubscriptionsAPIView(APIView):
    @async_to_sync
    @extend_schema(
        responses={
                200:ResponseSerializer[SubscriptionSerializer]
            },
            # auth=[
                # 'XManagerKey'
            # ]
    )
    async def get(self, request, pk):
        q = models.subscribe.objects.filter(api_pk=pk)
        if not await q.aexists():
            return await makeResponse(status=4, HttpStatus=404)
        serializer = ResponseSerializer[SubscriptionSerializer](
            status=0,
            data=await q.afirst()
        )
        return HttpResponse(
            await makeResponse(
                serializer,
                0
            )
        )
    
    @async_to_sync
    @extend_schema(
        responses={
            204:ResponseSerializer
        }
    )
    async def delete(self, request, pk):
        q = models.subscribe.objects.filter(api_pk=pk)
        if not await q.aexists():
            return await makeResponse(
                ResponseSerializer(status=4),
                HttpStatus=404
            )
        await q.adelete()
        return await makeResponse(
            ResponseSerializer(),
            HttpStatus=204
        )

from core.tasks import check_subscription_aligns

class SubscriptionsListAPIView(APIView):
    @async_to_sync
    @extend_schema(
        request=SubscriptionCreateSerializer,
        responses={
            201:ResponseSerializer[SubscriptionSerializer]
        }
    )
    async def post(self, request:HttpRequest):
        serializer = SubscriptionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return await makeResponse(
                ResponseSerializer(
                    status=3
                ),
                HttpStatus=400
            )
        try:
            obj = await serializer.acreate(serializer.data)
        except Http404:
            return await makeResponse(
                ResponseSerializer(status=3),
                HttpStatus=404
            )
        check_subscription_aligns.delay(obj.id)
        respSerializer = ResponseSerializer[SubscriptionSerializer](
            status=0,
            data=obj
        )
        return await makeResponse(
            respSerializer,
            HttpStatus=201
        )
    @async_to_sync
    @extend_schema(
        responses={
            200:ResponseSerializer[SubscriptionListSerializer]
        }
    )
    async def get(self, request):
        try:
            objs = models.subscribe.objects.filter()
            all=[]
            async for i in objs.aiterator():
                all.append(i)
            serializer = ResponseSerializer[SubscriptionListSerializer](all)
        except:
            return await makeResponse(
                ResponseSerializer(
                    status=3
                ),
                HttpStatus=500
            )
        return await makeResponse(
            serializer,
            HttpStatus=200
        )